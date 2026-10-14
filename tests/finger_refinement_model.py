"""Slow ghost models for refinement checks, never imported by the sorter.

Forest expectations use only input values and indices. The tree decoder reads
physical fields without calling backend traversal, audit or repair helpers.
"""
import sys
from collections import Counter
from unittest.mock import patch

if sys.flags.optimize != 0:
    raise RuntimeError('Refinement checks require optimization level 0')

import paper_jordan as core
from heterogeneous_finger_backend import ExternalLeaf, ROOT, INTERIOR
from sibling_list_backend import LEFT, RIGHT, UPPER, LOWER


def forest(values, count):
    intervals = {i: tuple(sorted(values[i-2:i])) for i in range(2, count+1)}
    owners = {}
    children = {i: [] for i in (-1, -2, *intervals)}
    for i, (low, high) in intervals.items():
        containers = [j for j, (a, b) in intervals.items()
                      if i % 2 == j % 2 and a < low and high < b]
        owner = max(containers, key=lambda j: intervals[j][0]) if containers else (-1 if i % 2 == 0 else -2)
        owners[i] = owner
        children[owner].append(i)
    groups = {}
    for owner, items in children.items():
        items.sort(key=lambda j: intervals[j][0])
        latest = max([owner, *items])
        if not items:
            groups[owner] = ()
        elif latest == owner:
            groups[owner] = (tuple(items),)
        else:
            cut = values[latest-1]
            left = tuple(j for j in items if intervals[j][1] <= cut)
            right = tuple(j for j in items if cut <= intervals[j][0])
            assert len(left) + len(right) == len(items), 'latest endpoint crosses a child'
            groups[owner] = tuple(g for g in (left, right) if g)
    return intervals, owners, groups


def check_records(values, count, records):
    intervals, owners, groups = forest(values, count)
    expected = {}
    for pid in groups:
        dummy = pid < 0
        family = (UPPER if pid == -1 else LOWER) if dummy else (UPPER if pid % 2 == 0 else LOWER)
        expected[pid] = (pid, None if dummy else pid, None if dummy else pid-1,
                         None if dummy else pid, family, dummy, owners.get(pid), groups[pid])
    actual = {row[0]: row for row in records}
    assert len(records) == len(actual), 'duplicate pair records'
    assert actual == expected, ('exact geometric forest/group mismatch', values[:count], actual, expected)


def decode_tree(piece, *, downward=False):
    """Return logical shape with identities; validate all tree metadata.

    An ordinary recursive traversal of this independently decoded tree is
    deliberately expensive. No production _up/_inner/_audit_tree is used.
    """
    root = piece.root
    outward = {}
    if not downward:
        for side, finger in ((LEFT, piece.left_finger), (RIGHT, piece.right_finger)):
            node, seen = finger, set()
            while node is not root:
                assert node is not None and id(node) not in seen, 'broken reverse chain'
                seen.add(id(node))
                assert node.role == side
                parent = node.left if side == LEFT else node.right
                assert parent is not None
                outward[id(parent), side] = node
                node = parent
    visited = set()
    leaves = []
    def visit(node, left_path, right_path, is_root=False):
        assert node is not None and id(node) not in visited, 'cycle/shared logical node'
        visited.add(id(node))
        role = INTERIOR if downward else ROOT if is_root else LEFT if left_path else RIGHT if right_path else INTERIOR
        assert node.role == role, ('role', node.node_id, node.role, role)
        if isinstance(node, ExternalLeaf):
            assert not node.red and node.rank == 0 and node.span == 1
            assert node.handle.leaf is node and node.key == node.handle.low
            if downward or role in (ROOT, INTERIOR):
                assert node.left is node.right is None
            elif role == LEFT:
                assert node.right is None
            else:
                assert node.left is None
            leaves.append(node)
            return (node.node_id, node.key, False, 0), 1, node.key, node.key
        if downward or role == INTERIOR:
            left, right = node.left, node.right
        elif role == ROOT:
            assert node.left is node.right is None
            left, right = outward[id(node), LEFT], outward[id(node), RIGHT]
            assert piece.left_top is left and piece.right_top is right
        elif role == LEFT:
            left, right = outward[id(node), LEFT], node.right
        else:
            left, right = node.left, outward[id(node), RIGHT]
        a, na, low, mid = visit(left, left_path, False)
        b, nb, high_start, high = visit(right, False, right_path)
        assert mid == node.key and mid < high_start, 'separator/order'
        assert left.rank == right.rank and node.rank == left.rank + int(not node.red), 'rank'
        assert not (node.red and (left.red or right.red)), 'red/red'
        mass = na + nb if downward or role == INTERIOR else nb if role == LEFT else na if role == RIGHT else 0
        assert node.span == mass, 'role-sensitive span'
        return (node.node_id, node.key, node.red, node.rank, a, b), na+nb, low, high
    shape, size, low, high = visit(root, True, True, True)
    assert size == piece.size
    if downward:
        assert piece.maximum == high
    else:
        assert not root.red
        assert leaves[0] is piece.left_finger and leaves[-1] is piece.right_finger
        if size == 1:
            assert piece.left_top is piece.right_top is None
    return shape, tuple(leaves), visited


def check_physical(backend, expected_groups):
    nodes, pairs, members = set(), set(), {}
    for lid, header in backend._lists.items():
        assert header.list_id == lid
        assert header.live and header in header.owner.child_slots
        shape, leaves, visited = decode_tree(header)
        members[header] = tuple(leaf.handle.pair.pair_id for leaf in leaves)
        assert backend._pairs[header.owner.pair.pair_id] is header.owner
        assert not nodes.intersection(visited)
        nodes.update(visited)
        for index, leaf in enumerate(leaves):
            h = leaf.handle
            assert h.pair.pair_id not in pairs
            pairs.add(h.pair.pair_id)
            assert h.left_boundary is (header if index == 0 else None)
            assert h.right_boundary is (header if index == len(leaves)-1 else None)
            assert backend._pairs[h.pair.pair_id] is h
    assert nodes == {id(n) for n in backend._nodes.values()}, 'unreachable/extra nodes'
    assert all(n.node_id == key for key, n in backend._nodes.items()), 'wrong node registry key'
    assert pairs == {pid for pid in backend._pairs if pid > 0}, 'missing/extra leaves'
    seen_headers = []
    for pid, handle in backend._pairs.items():
        assert handle.pair.pair_id == pid
        assert tuple(members[h] for h in handle.child_slots) == expected_groups[pid]
        seen_headers.extend(handle.child_slots)
    assert len(seen_headers) == len(members) and set(seen_headers) == set(members)


def next_plan(values, count):
    """Derive next call preconditions geometrically, without backend queries."""
    i = count + 1
    intervals, owners, groups = forest(values, count)
    x, y = values[i-2:i]
    color_pairs = {j: ab for j, ab in intervals.items() if j % 2 == i % 2}
    containers = [j for j, (a, b) in color_pairs.items() if a < x < b]
    owner = max(containers, key=lambda j: intervals[j][0]) if containers else (-1 if i % 2 == 0 else -2)
    endpoints = sorted((values[k-1], j) for j in color_pairs for k in (j-1, j))
    left = max((e for e in endpoints if e[0] < x), default=(None, owner), key=lambda e: e[0])[1]
    right = min((e for e in endpoints if e[0] > x), default=(None, owner), key=lambda e: e[0])[1]
    def group_of(j, side):
        if j == owner:
            return None
        assert owners[j] == owner, 'neighbor is not an immediate sibling'
        group = next(g for g in groups[owner] if j in g)
        assert j == group[-1 if side == LEFT else 0], 'neighbor is not the required endpoint'
        return group
    lg, rg = group_of(left, LEFT), group_of(right, RIGHT)
    assert lg is None or rg is None or lg != rg, 'two boundaries share a group'
    increasing = x < y
    target, source = (lg, rg) if increasing else (rg, lg)
    if target is None:
        assert len(groups[owner]) < 2, 'singleton has no free owner slot'
    low, high = sorted((x, y))
    if owner > 0:
        assert intervals[owner][0] < low < high < intervals[owner][1]
    acquired = tuple(j for g in groups[owner] for j in g
                     if low < intervals[j][0] and intervals[j][1] < high)
    assert not acquired or source is not None
    assert all(j in (source or ()) for j in acquired), 'acquisition crosses group boundary'
    if source is not None:
        by_cut = tuple(j for j in source if (intervals[j][0] <= y if increasing else intervals[j][0] > y))
        assert acquired == by_cut, 'key split differs from geometric acquisition'
        assert all(not (intervals[j][0] <= y <= intervals[j][1]) for j in source)
    candidates = [k for k in range(1, i) if (values[k-1] < y if increasing else values[k-1] > y)]
    closest = lambda ks: (max if increasing else min)(ks, key=lambda k: values[k-1])
    anchor = closest(candidates)
    paired = [k for k in candidates if not (i % 2 == 1 and k == 1)]
    base = closest(paired)
    return dict(owner=owner, left=left, right=right, target=target, source=source,
                acquired=acquired, increasing=increasing, anchor=anchor, base=base)


def check_run(values, backend, policy):
    """Observe the *same* production loop; never supply computed expectations."""
    values = list(values)
    plans, counts, identities = {}, Counter(), {}
    original_a, original_b, original_c = core._step3a, core._step3b, core._step3c
    def snapshot(state, count):
        check_records(values, count, state.sibling_backend.logical_snapshot()[1])
        if hasattr(state.sibling_backend, '_nodes'):
            b = state.sibling_backend
            intervals, _, groups = forest(values, count)
            check_physical(b, groups)
            for pid in range(2, count+1):
                h = b._pairs[pid]
                assert (h.low, h.high) == intervals[pid]
                assert state.pairs[pid] is h.pair
                identity = (h, h.leaf, h.pair)
                if pid in identities:
                    assert all(a is c for a, c in zip(identity, identities[pid]))
                identities[pid] = identity
    def before_a(state, i, *args, **kwargs):
        plan = next_plan(values, i-1)
        plans[i] = plan
        stages = state.stage_results[i]
        assert stages['step1_select_boundary_pair'].pair_id == plan['left']
        assert stages['step2_select_boundary_pair'].pair_id == plan['right']
        # Match an already-audited logical group to a concrete live ID.
        b = state.sibling_backend
        def list_id(group):
            if group is None:
                return None
            return b.boundary_list(group[0], LEFT)
        plan['source_id'], plan['target_id'] = list_id(plan['source']), list_id(plan['target'])
        if hasattr(b, '_nodes') and plan['source'] is not None:
            plan['source_object'] = b._lists[plan['source_id']]
        result = original_a(state, i, *args, **kwargs)
        assert result.parent_pair_id == plan['owner']
        assert result.transfer_source_list_id == plan['source_id']
        if plan['target'] is not None:
            assert result.sibling_list_id == plan['target_id']
        if plan['source'] is not None:
            assert b.list_owner(plan['source_id']) == plan['owner']
            assert b.list_size(plan['source_id']) == len(plan['source'])
            assert b.boundary_list(plan['source'][0], LEFT) == plan['source_id']
            assert b.boundary_list(plan['source'][-1], RIGHT) == plan['source_id']
            if 'source_object' in plan:
                assert b._lists[plan['source_id']] is plan['source_object']
        counts['iterations'] += 1
        counts['increasing' if plan['increasing'] else 'decreasing'] += 1
        counts['singleton' if plan['target'] is None else 'endpoint_insert'] += 1
        counts['finite_owner' if plan['owner'] > 0 else 'dummy_owner'] += 1
        counts['z1_boundary'] += sum(stages[s].adjusted_for_z1 for s in ('step1_select_boundary_pair','step2_select_boundary_pair'))
        return result
    def after_b(state, i, *args, **kwargs):
        result = original_b(state, i, *args, **kwargs)
        plan = plans[i]
        assert result.performed == (plan['source'] is not None)
        snapshot(state, i)  # forest restored before Step 3(c), output still old
        if result.performed:
            counts['splits'] += 1
            counts['both_nonempty'] += 0 < len(plan['acquired']) < len(plan['source'])
            if 'source_object' in plan:
                assert not plan['source_object'].live
                assert plan['source_id'] not in state.sibling_backend._lists
        return result
    def after_c(state, i, *args, **kwargs):
        result = original_c(state, i, *args, **kwargs)
        plan = plans[i]
        assert result.output_anchor_point_id == plan['anchor']
        assert result.base_anchor_point_id == plan['base']
        assert result.adjusted_for_z1 == (plan['base'] != plan['anchor'])
        counts['z1_output'] += result.adjusted_for_z1
        return result
    def prefix(state):
        snapshot(state, state.processed_count)
        assert state.partial_order.to_list() == sorted(values[:state.processed_count])
        counts['prefixes'] += 1
    with patch.object(core, '_step3a', before_a), patch.object(core, '_step3b', after_b), patch.object(core, '_step3c', after_c):
        state = core._run_paper_jordan_state_values(values, backend=backend, execution_policy=policy, invariant_callback=prefix)
    assert counts['prefixes'] == len(values)-2 and counts['iterations'] == len(values)-3
    return state, dict(counts)
