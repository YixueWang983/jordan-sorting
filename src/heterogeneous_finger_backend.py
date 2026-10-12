"""First, deliberately partial, heterogeneous red-black sibling backend.

External leaves hold stable pair handles. Left/right ribs reverse the outward
child pointer; off-rib nodes point down. Insertion starts at an end finger and
only ascends while repairing a red/red violation. There is no ordinary-tree
copy, root search, member array, or per-item owner cache.

This implements make/endpoint insertion, NOT split or Jordan sorting. See
Tarjan--Van Wyk (1988), Appendix, pp. 171--175, Fig. 20 and corrected Fig. 22
(the drawing printed as Fig. 23 on p. 176). Code is independently written.
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps

from paper_execution_policy import CHECKED_POLICY, require_fixed_paper_execution_policy
from sibling_list_backend import LEFT, RIGHT, PairRecord


ROOT = "root"
INTERIOR = "interior"


class WorkLedger:
    """Count semantic record accesses, not Python bytecodes or elapsed time.

Each node field read/write is one node visit (revisits included). All stored
record-field assignments count as metadata writes, including initialization.
Comparisons count explicit geometry/key comparisons. Allocation counts cover
nodes, handles, headers and replacement child-slot tuples, not interpreter
temporaries. Registry operations are counted separately (Python dicts).
Auditing is a separate bucket and never pays for normal-path maintenance.
"""

    FIELDS = (
        "node_visits", "node_reads", "node_writes", "handle_reads", "header_reads",
        "metadata_writes", "pointer_writes", "comparisons", "rotations",
        "left_rotations", "right_rotations", "recolorings", "recolor_cascades",
        "root_blackenings", "allocations", "leaf_allocations",
        "internal_allocations", "handle_allocations", "header_allocations",
        "slot_tuple_allocations", "registry_reads", "registry_writes", "point_reads",
    )

    def __init__(self):
        self.buckets = {name: dict.fromkeys(self.FIELDS, 0)
                        for name in ("operations", "queries", "audit")}
        self.active = None
        self.last_operation = None

    def add(self, name, amount=1):
        if self.active is not None:
            self.active[name] += amount

    def read(self, kind):
        if kind in ("leaf", "internal"):
            self.add("node_visits")
            self.add("node_reads")
        else:
            self.add(kind + "_reads")

    def write(self, kind, pointer):
        self.add("metadata_writes")
        if pointer:
            self.add("pointer_writes")
        if kind in ("leaf", "internal"):
            self.add("node_visits")
            self.add("node_writes")

    def allocate(self, kind):
        self.add("allocations")
        self.add(kind + "_allocations")

    @contextmanager
    def observe(self, bucket, operation):
        # Nested queries are part of the calling update, not free work.
        if self.active is not None:
            yield
            return
        self.active = self.buckets[bucket]
        before = self.active.copy()
        status = "failed"
        try:
            yield
            status = "ok"
        finally:
            if bucket == "operations":
                self.last_operation = {
                    "operation": operation, "status": status,
                    "work": {k: self.active[k] - before[k] for k in self.FIELDS},
                }
            self.active = None

    def snapshot(self):
        return {name: values.copy() for name, values in self.buckets.items()}


def observed(bucket):
    def decorate(function):
        @wraps(function)
        def call(self, *args, **kwargs):
            with self.work.observe(bucket, function.__name__):
                return function(self, *args, **kwargs)
        return call
    return decorate


class _Tracked:
    """Instrument stored fields also inside local rotations/validation helpers."""

    __slots__ = ("_ledger",)
    _fields = frozenset()
    _pointers = frozenset()

    def __getattribute__(self, name):
        cls = type(self)
        if name in cls._fields:
            object.__getattribute__(self, "_ledger").read(cls._kind)
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        cls = type(self)
        if name in cls._fields:
            object.__getattribute__(self, "_ledger").write(cls._kind, name in cls._pointers)
        object.__setattr__(self, name, value)


class PairHandle(_Tracked):
    """Stable identity and child slots; only endpoints refer back to a header.

``pair`` is the exact registered PairRecord used by the shared core. Its old
eager parent/list/children fields remain unused. Geometry is captured once from
the fixed point source, with curve-order endpoints preserved in that record.
"""

    __slots__ = ("pair", "identity", "low", "high", "leaf", "left_boundary",
                 "right_boundary", "child_slots")
    _fields = frozenset(__slots__)
    _pointers = frozenset(("pair", "leaf", "left_boundary", "right_boundary", "child_slots"))
    _kind = "handle"

    def __init__(self, ledger, pair, low, high):
        self._ledger = ledger
        ledger.allocate("handle")
        self.pair = pair
        self.identity = (pair.pair_id, pair.end_index, pair.first_point_id,
                         pair.second_point_id, pair.family, pair.is_dummy)
        self.low, self.high = low, high
        self.leaf = None
        self.left_boundary = self.right_boundary = None
        self.child_slots = ()


class _Node(_Tracked):
    __slots__ = ("node_id", "left", "right", "role", "red", "rank", "span", "key")
    _fields = frozenset(__slots__)
    _pointers = frozenset(("left", "right"))

    def __init__(self, ledger, node_id, role, red, rank, span, key, left=None, right=None):
        self._ledger = ledger
        ledger.allocate(type(self)._kind)
        self.node_id = node_id
        self.left, self.right = left, right
        self.role, self.red = role, red
        # rank = logical black height, excluding black external leaves.
        # span = immediate DOWNWARD branch mass; rib ancestors are excluded.
        # It is not the subtree size or the optional reachable-position index
        # of Fig. 22. No position/secondary-heap search is offered here.
        self.rank, self.span, self.key = rank, span, key


class ExternalLeaf(_Node):
    __slots__ = ("handle",)
    _kind = "leaf"
    _fields = _Node._fields | {"handle"}
    _pointers = _Node._pointers | {"handle"}

    def __init__(self, ledger, node_id, handle, role):
        super().__init__(ledger, node_id, role, False, 0, 1, handle.low)
        self.handle = handle


class InternalNode(_Node):
    __slots__ = ()
    _kind = "internal"


class ListHeader(_Tracked):
    __slots__ = ("list_id", "owner", "live", "size", "root", "left_finger",
                 "right_finger", "left_top", "right_top")
    _fields = frozenset(__slots__)
    _pointers = frozenset(("owner", "root", "left_finger", "right_finger",
                           "left_top", "right_top"))
    _kind = "header"

    def __init__(self, ledger, list_id, owner, leaf):
        self._ledger = ledger
        ledger.allocate("header")
        self.list_id, self.owner, self.live, self.size = list_id, owner, True, 1
        self.root = self.left_finger = self.right_finger = leaf
        # The root reverses BOTH pointers. These two constant-size header
        # references provide its logical children during a root rotation.
        self.left_top = self.right_top = None


class HeterogeneousFingerBackend:
    backend_name = "heterogeneous_finger_partial"
    audit_schema = "heterogeneous-make-insert-v1"
    metrics_schema = "heterogeneous-record-access-v1"
    sorting_ready = False
    supported_operations = frozenset(("register_pair", "make_list", "insert_boundary"))

    def __init__(self, point_value, *, execution_policy=CHECKED_POLICY):
        if not callable(point_value):
            raise TypeError("point_value must be callable")
        self.execution_policy = require_fixed_paper_execution_policy(execution_policy)
        self._point_value = point_value
        self.work = WorkLedger()
        self._pairs = {}
        self._lists = {}
        self._nodes = {}
        self._dummies = {}
        self._next_list_id = self._next_node_id = 1

    def _lookup(self, registry, key):
        self.work.add("registry_reads")
        if type(key) is not int:
            raise TypeError("registry IDs must be integers")
        return registry[key]

    def _store(self, registry, key, value):
        self.work.add("registry_writes")
        registry[key] = value

    def _less(self, first, second):
        self.work.add("comparisons")
        return first < second

    def _equal(self, first, second):
        self.work.add("comparisons")
        return first == second

    def _handle(self, pair_id):
        return self._lookup(self._pairs, pair_id)

    def _header(self, list_id):
        header = self._lookup(self._lists, list_id)
        if not header.live or header.list_id != list_id:
            raise ValueError("retired or inconsistent list header")
        return header

    def _node_id(self):
        result = self._next_node_id
        self._next_node_id += 1
        self.work.add("metadata_writes")
        return result

    def _leaf(self, handle, role):
        leaf = ExternalLeaf(self.work, self._node_id(), handle, role)
        self._store(self._nodes, leaf.node_id, leaf)
        return leaf

    def _internal(self, key, role, parent, inner, side):
        node = InternalNode(self.work, self._node_id(), role, True, 0,
                            0 if role == ROOT else 1, key)
        if role != ROOT:
            self._set_up(node, parent, side)
            self._set_inner(node, inner, side)
        self._store(self._nodes, node.node_id, node)
        return node

    @observed("operations")
    def register_pair(self, pair):
        if not isinstance(pair, PairRecord):
            raise TypeError("pair must be a PairRecord")
        # Recheck the value object, which can have been mutated since creation.
        pair.__post_init__()
        self.work.add("registry_reads")
        if pair.pair_id in self._pairs:
            raise ValueError("duplicate pair id")
        low = high = None
        if pair.is_dummy:
            self.work.add("registry_reads")
            if pair.family in self._dummies:
                raise ValueError("duplicate family dummy")
        else:
            first = self.point_value(pair.first_point_id)
            second = self.point_value(pair.second_point_id)
            if self._less(first, second):
                low, high = first, second
            elif self._less(second, first):
                low, high = second, first
            else:
                raise ValueError("pair endpoints must be strictly ordered")
        handle = PairHandle(self.work, pair, low, high)
        self._store(self._pairs, pair.pair_id, handle)
        if pair.is_dummy:
            self._store(self._dummies, pair.family, handle)
        return pair.pair_id

    @observed("queries")
    def get_pair(self, pair_id):
        return self._handle(pair_id).pair

    @observed("queries")
    def pair_handle(self, pair_id):
        """Stable implementation handle; no arbitrary-owner lookup."""
        return self._handle(pair_id)

    @observed("queries")
    def point_value(self, point_id):
        self.work.add("point_reads")
        return self._point_value(point_id)

    def registered_pair_ids(self):
        """Explicit registry enumeration, only for initialization/full auditing."""
        return tuple(self._pairs)

    @observed("queries")
    def validate_live_pair(self, pair_id):
        handle = self._handle(pair_id)
        leaf = handle.leaf
        if handle.pair.is_dummy or leaf is None or leaf.handle is not handle:
            raise ValueError("expected a live finite pair")
        if self._lookup(self._nodes, leaf.node_id) is not leaf:
            raise RuntimeError("pair leaf is not registered")
        return handle.pair

    @observed("queries")
    def validate_dummy_ownership(self, pair_id):
        handle = self._handle(pair_id)
        self.work.add("registry_reads")
        if (not handle.pair.is_dummy or self._dummies.get(handle.pair.family) is not handle
                or handle.leaf is not None or handle.left_boundary is not None
                or handle.right_boundary is not None):
            raise ValueError("invalid family dummy")

    @staticmethod
    def _side(side):
        if side not in (LEFT, RIGHT):
            raise ValueError("side must be left or right")

    @observed("queries")
    def boundary_list(self, pair_id, side):
        self._side(side)
        handle = self._handle(pair_id)
        header = handle.left_boundary if side == LEFT else handle.right_boundary
        if header is None:
            raise ValueError("pair is not the requested live boundary")
        if self._header(header.list_id) is not header:
            raise ValueError("stale boundary header reference")
        leaf = header.left_finger if side == LEFT else header.right_finger
        if leaf is not handle.leaf or leaf.handle is not handle:
            raise ValueError("stale boundary finger reference")
        self._owner_slots(header.owner, required=header)
        return header.list_id

    @observed("queries")
    def list_owner(self, list_id):
        return self._header(list_id).owner.pair.pair_id

    @observed("queries")
    def list_size(self, list_id):
        return self._header(list_id).size

    def _owner_slots(self, owner, required=None):
        slots = owner.child_slots
        if len(slots) > 2 or (len(slots) == 2 and slots[0] is slots[1]):
            raise RuntimeError("invalid owner child slots")
        if required is not None and required not in slots:
            raise RuntimeError("header is absent from owner slots")
        for header in slots:  # Bounded by two, never by list length.
            if header.owner is not owner or self._header(header.list_id) is not header:
                raise RuntimeError("owner slot has an inconsistent header")
        return slots

    @observed("queries")
    def child_list_ids(self, parent_pair_id):
        return tuple(h.list_id for h in self._owner_slots(self._handle(parent_pair_id)))

    @observed("queries")
    def extreme_child(self, parent_pair_id, side):
        self._side(side)
        slots = self._owner_slots(self._handle(parent_pair_id))
        if not slots:
            return None
        header = slots[0 if side == LEFT else -1]
        leaf = header.left_finger if side == LEFT else header.right_finger
        pair = leaf.handle.pair
        if self.boundary_list(pair.pair_id, side) != header.list_id:
            raise RuntimeError("extreme child has inconsistent boundary ownership")
        return pair

    def _new_pair(self, pair_id):
        handle = self._handle(pair_id)
        if (handle.pair.is_dummy or handle.leaf is not None or handle.child_slots
                or handle.left_boundary is not None or handle.right_boundary is not None):
            raise ValueError("new item must be an unowned, childless finite pair")
        return handle

    def _owner(self, handle, owner):
        if handle.pair.family != owner.pair.family:
            raise ValueError("pair and owner must have the same family")
        if owner.pair.is_dummy:
            self.validate_dummy_ownership(owner.pair.pair_id)
        else:
            self.validate_live_pair(owner.pair.pair_id)
            if not (self._less(owner.low, handle.low) and self._less(handle.high, owner.high)):
                raise ValueError("new pair is not strictly enclosed by its owner")
        # Fresh childless items cannot create an ancestry cycle. Existing owner
        # connectivity is inductive for make/insert; the full auditor verifies it.

    def _disjoint(self, first_high, second_low):
        if not self._less(first_high, second_low):
            raise ValueError("sibling intervals must be disjoint and strictly ordered")

    @observed("operations")
    def make_list(self, pair_id, owner_parent_pair_id):
        handle = self._new_pair(pair_id)
        owner = self._handle(owner_parent_pair_id)
        self._owner(handle, owner)
        slots = self._owner_slots(owner)
        if len(slots) == 2:
            raise ValueError("owner already has two child lists")
        before = False
        if slots:
            other = slots[0]
            before = self._less(handle.low, other.left_finger.handle.low)
            if before:
                self._disjoint(handle.high, other.left_finger.handle.low)
            else:
                self._disjoint(other.right_finger.handle.high, handle.low)
        leaf = self._leaf(handle, ROOT)
        header = ListHeader(self.work, self._next_list_id, owner, leaf)
        self._next_list_id += 1
        self.work.add("metadata_writes")
        self._store(self._lists, header.list_id, header)
        handle.leaf = leaf
        handle.left_boundary = handle.right_boundary = header
        self.work.allocate("slot_tuple")
        owner.child_slots = (header, *slots) if before else (*slots, header)
        return header.list_id

    @staticmethod
    def _up(node, side):
        return node.left if side == LEFT else node.right

    @staticmethod
    def _set_up(node, parent, side):
        if side == LEFT:
            node.left = parent
        else:
            node.right = parent

    @staticmethod
    def _set_inner(node, child, side):
        if side == LEFT:
            node.right = child
        else:
            node.left = child

    @staticmethod
    def _inner(node, header, side):
        if node.role == ROOT:
            return header.right_top if side == LEFT else header.left_top
        return node.right if side == LEFT else node.left

    def _color(self, node, red):
        if node.red != red:
            node.red = red
            self.work.add("recolorings")

    def _blacken_root(self, header):
        root = header.root
        if root.red:
            self._color(root, False)
            root.rank += 1
            self.work.add("root_blackenings")

    def _rotate_outward(self, header, grand, parent, child, side):
        """Fig. 20(c), mirrored for right insertion, with reversed rib edges.

        ``child`` is the logical outward child of ``parent`` (not stored as
        a downward edge). A root rotation changes two rib roles, not all nodes
        on the opposite rib. Its inward-branch masses remain valid unchanged.
        """
        self.work.add("rotations")
        self.work.add("right_rotations" if side == LEFT else "left_rotations")
        was_root = grand.role == ROOT
        above = None if was_root else self._up(grand, side)
        middle = self._inner(parent, header, side)
        far = self._inner(grand, header, side)
        self._color(parent, False)
        self._color(grand, True)
        grand.rank = middle.rank
        parent.rank = grand.rank + 1
        if was_root:
            opposite = RIGHT if side == LEFT else LEFT
            parent.role, parent.left, parent.right, parent.span = ROOT, None, None, 0
            grand.role = opposite
            self._set_up(grand, parent, opposite)
            self._set_inner(grand, middle, opposite)
            grand.span = middle.span
            header.root = parent
            if side == LEFT:
                header.left_top, header.right_top = child, grand
            else:
                header.left_top, header.right_top = grand, child
            # far's reversed parent edge already points to grand.
        else:
            grand.role = INTERIOR
            if side == LEFT:
                grand.left, grand.right = middle, far
            else:
                grand.left, grand.right = far, middle
            grand.span = middle.span + far.span
            self._set_up(parent, above, side)
            self._set_inner(parent, grand, side)
            parent.span = grand.span
            if above.role == ROOT:
                if side == LEFT:
                    header.left_top = parent
                else:
                    header.right_top = parent

    def _repair_insert(self, header, node, side):
        while node.role != ROOT:
            parent = self._up(node, side)
            if not parent.red:
                return
            grand = self._up(parent, side)
            if grand is None:
                raise RuntimeError("red root before insertion repair")
            uncle = self._inner(grand, header, side)
            if uncle.red:
                self.work.add("recolor_cascades")
                self._color(parent, False)
                self._color(uncle, False)
                self._color(grand, True)
                parent.rank += 1
                uncle.rank += 1
                # Grand's rank stays unchanged: black->red, children +1.
                node = grand
            else:
                self._rotate_outward(header, grand, parent, node, side)
                return
        self._blacken_root(header)

    @observed("operations")
    def insert_boundary(self, pair_id, anchor_pair_id, side):
        self._side(side)
        handle = self._new_pair(pair_id)
        header = self._header(self.boundary_list(anchor_pair_id, side))
        anchor = self._handle(anchor_pair_id)
        self._owner(handle, header.owner)
        if side == LEFT:
            self._disjoint(handle.high, anchor.low)
        else:
            self._disjoint(anchor.high, handle.low)
        slots = self._owner_slots(header.owner, required=header)
        if len(slots) == 2:
            if side == LEFT and slots[1] is header:
                self._disjoint(slots[0].right_finger.handle.high, handle.low)
            if side == RIGHT and slots[0] is header:
                self._disjoint(handle.high, slots[1].left_finger.handle.low)

        old_leaf = anchor.leaf
        new_leaf = self._leaf(handle, side)
        singleton = header.size == 1
        above = None if singleton else self._up(old_leaf, side)
        key = handle.low if side == LEFT else anchor.low
        node = self._internal(key, ROOT if singleton else side, above, old_leaf, side)
        if singleton:
            opposite = RIGHT if side == LEFT else LEFT
            old_leaf.role = opposite
            self._set_up(old_leaf, node, opposite)
            header.root = node
            if side == LEFT:
                header.left_top, header.right_top = new_leaf, old_leaf
            else:
                header.left_top, header.right_top = old_leaf, new_leaf
        else:
            old_leaf.role, old_leaf.left, old_leaf.right = INTERIOR, None, None
            if above.role == ROOT:
                if side == LEFT:
                    header.left_top = node
                else:
                    header.right_top = node
        self._set_up(new_leaf, node, side)
        handle.leaf = new_leaf
        if side == LEFT:
            header.left_finger = new_leaf
            anchor.left_boundary = None
            handle.left_boundary = header
        else:
            header.right_finger = new_leaf
            anchor.right_boundary = None
            handle.right_boundary = header
        header.size += 1
        self._repair_insert(header, node, side)
        return header.list_id

    def split_value(self, *args, **kwargs):
        raise NotImplementedError("heterogeneous split and local repair are not implemented")

    def adopt_split(self, *args, **kwargs):
        raise NotImplementedError("split ownership/header transfer is not implemented")

    def split_pairs_at_value(self, *args, **kwargs):
        raise NotImplementedError("partial make/insert backend cannot run Jordan split")

    def _audit_tree(self, header, seen_nodes):
        """Reconstruct logical outward children ONLY in the audit bucket."""
        outer = {LEFT: {}, RIGHT: {}}
        root = header.root
        for side, finger in ((LEFT, header.left_finger), (RIGHT, header.right_finger)):
            current = finger
            path_seen = set()
            while current is not root:
                if current in path_seen or current.role != side:
                    raise RuntimeError("rib cycle or wrong rib role")
                path_seen.add(current)
                parent = self._up(current, side)
                if not isinstance(parent, InternalNode):
                    raise RuntimeError("rib does not reach the root")
                outer[side][parent] = current
                current = parent
        if root.role != ROOT or root.left is not None or root.right is not None or root.red:
            raise RuntimeError("invalid root orientation or color")
        if isinstance(root, ExternalLeaf):
            if (header.size != 1 or header.left_finger is not root or header.right_finger is not root
                    or header.left_top is not None or header.right_top is not None):
                raise RuntimeError("invalid singleton header")
        elif (outer[LEFT].get(root) is not header.left_top
              or outer[RIGHT].get(root) is not header.right_top):
            raise RuntimeError("root child cache disagrees with ribs")

        leaves = []
        info = {}
        children = {}
        left_rib = set(outer[LEFT].values())
        right_rib = set(outer[RIGHT].values())
        stack = [(root, False)]
        while stack:
            node, done = stack.pop()
            if done:
                left, right = children[node]
                lc, lr, lmin, lmax = info[left]
                rc, rr, rmin, rmax = info[right]
                if lr != rr or node.rank != lr + (not node.red):
                    raise RuntimeError("black-height/rank mismatch")
                if node.red and (left.red or right.red):
                    raise RuntimeError("red node has a red child")
                if not (self._equal(node.key, lmax) and self._less(node.key, rmin)):
                    raise RuntimeError("invalid separator key")
                mass = 0 if node.role == ROOT else (rc if node.role == LEFT else
                        lc if node.role == RIGHT else lc + rc)
                if node.span != mass:
                    raise RuntimeError("invalid local branch mass")
                info[node] = (lc + rc, node.rank, lmin, rmax)
                continue
            if not isinstance(node, _Node) or node in seen_nodes:
                raise RuntimeError("duplicate node or structural cycle")
            seen_nodes.add(node)
            if self._lookup(self._nodes, node.node_id) is not node:
                raise RuntimeError("unregistered tree node")
            expected_role = (ROOT if node is root else
                             LEFT if node in left_rib else
                             RIGHT if node in right_rib else INTERIOR)
            if node.role != expected_role:
                raise RuntimeError("node role disagrees with its rib position")
            if isinstance(node, ExternalLeaf):
                handle = node.handle
                if (handle.leaf is not node or handle.pair.is_dummy or node.red
                        or node.rank != 0 or node.span != 1 or not self._equal(node.key, handle.low)):
                    raise RuntimeError("invalid external leaf or stable handle")
                if node.role == INTERIOR and (node.left is not None or node.right is not None):
                    raise RuntimeError("interior external leaf has a pointer")
                if node.role == LEFT and node.right is not None:
                    raise RuntimeError("left external finger has an inward pointer")
                if node.role == RIGHT and node.left is not None:
                    raise RuntimeError("right external finger has an inward pointer")
                leaves.append(handle)
                info[node] = (1, 0, handle.low, handle.low)
            else:
                left = outer[LEFT].get(node) if node.role in (LEFT, ROOT) else node.left
                right = outer[RIGHT].get(node) if node.role in (RIGHT, ROOT) else node.right
                if left is None or right is None:
                    raise RuntimeError("internal node is not full")
                children[node] = (left, right)
                stack.extend(((node, True), (right, False), (left, False)))
        if info[root][0] != header.size:
            raise RuntimeError("header size mismatch")
        if leaves[0].leaf is not header.left_finger or leaves[-1].leaf is not header.right_finger:
            raise RuntimeError("header fingers are not logical extremes")
        for index, handle in enumerate(leaves):
            if handle.left_boundary is not (header if index == 0 else None):
                raise RuntimeError("stale left boundary reference")
            if handle.right_boundary is not (header if index == len(leaves)-1 else None):
                raise RuntimeError("stale right boundary reference")
            if index:
                self._disjoint(leaves[index-1].high, handle.low)
        return leaves

    def _audit(self, require_all_owned):
        seen_nodes = set()
        membership = {}
        groups = {}
        for list_id, header in self._lists.items():
            if header.list_id != list_id or not header.live:
                raise RuntimeError("invalid live header registry")
            owner = header.owner
            if self._handle(owner.pair.pair_id) is not owner:
                raise RuntimeError("unregistered list owner")
            self._owner_slots(owner, required=header)
            leaves = self._audit_tree(header, seen_nodes)
            groups[list_id] = tuple(h.pair.pair_id for h in leaves)
            for handle in leaves:
                pair_id = handle.pair.pair_id
                if pair_id in membership or self._handle(pair_id) is not handle:
                    raise RuntimeError("duplicate membership or unstable handle")
                self._owner(handle, owner)
                membership[pair_id] = owner.pair.pair_id
        if seen_nodes != set(self._nodes.values()):
            raise RuntimeError("orphan allocated node")
        for pair_id, handle in self._pairs.items():
            pair = handle.pair
            if handle.identity != (pair_id, pair.end_index, pair.first_point_id,
                                   pair.second_point_id, pair.family, pair.is_dummy) or pair.pair_id != pair_id:
                raise RuntimeError("registered pair identity changed")
            if pair.parent_pair_id is not None or pair.sibling_list_id is not None or pair.child_sibling_list_ids:
                raise RuntimeError("ordinary eager ownership fields must remain unused")
            if pair.is_dummy:
                self.validate_dummy_ownership(pair_id)
            elif handle.leaf is None:
                if require_all_owned or handle.child_slots or handle.left_boundary or handle.right_boundary:
                    raise RuntimeError("unowned pair or dangling handle metadata")
            elif pair_id not in membership:
                raise RuntimeError("live handle has no tree membership")
            if not pair.is_dummy:
                first = self.point_value(pair.first_point_id)
                second = self.point_value(pair.second_point_id)
                low, high = (first, second) if self._less(first, second) else (second, first)
                if not (self._equal(low, handle.low) and self._equal(high, handle.high)):
                    raise RuntimeError("fixed point source changed")
            slots = self._owner_slots(handle)
            if len(slots) == 2:
                self._disjoint(slots[0].right_finger.handle.high, slots[1].left_finger.handle.low)
        # Memoized owner-chain walk: audit the entire forest, not each ancestor
        # on every insertion. Pending registered/unowned items are excluded.
        finished = {h.pair.pair_id for h in self._dummies.values()}
        for pair_id in membership:
            path = set()
            current = pair_id
            while current not in finished:
                if current in path or current not in membership:
                    raise RuntimeError("owner cycle or disconnected family tree")
                path.add(current)
                current = membership[current]
            finished.update(path)
        return groups, membership

    @observed("audit")
    def validate_invariants(self, require_all_owned=True):
        self._audit(require_all_owned)
        return True

    @observed("audit")
    def materialize_audit(self, require_all_owned=True):
        """Full logical child grouping; never used by make/insert or queries."""
        groups, _ = self._audit(require_all_owned)
        return tuple((self._lists[key].owner.pair.pair_id, groups[key]) for key in sorted(groups))

    @observed("audit")
    def logical_snapshot(self):
        groups, membership = self._audit(True)
        return ("jordan-logical-v1", tuple(
            (*handle.identity, membership.get(pair_id),
             tuple(groups[h.list_id] for h in handle.child_slots))
            for pair_id, handle in sorted(self._pairs.items())))

    @observed("audit")
    def audit_snapshot(self):
        """Partial-backend deterministic structure; not a sorting acceptance."""
        def nid(node):
            return None if node is None else node.node_id
        return (
            self.audit_schema, self._next_node_id, self._next_list_id,
            tuple((key, h.identity, h.low, h.high, nid(h.leaf),
                   None if h.left_boundary is None else h.left_boundary.list_id,
                   None if h.right_boundary is None else h.right_boundary.list_id,
                   tuple(s.list_id for s in h.child_slots)) for key, h in sorted(self._pairs.items())),
            tuple((key, h.owner.pair.pair_id, h.live, h.size, nid(h.root),
                   nid(h.left_finger), nid(h.right_finger), nid(h.left_top), nid(h.right_top))
                  for key, h in sorted(self._lists.items())),
            tuple((key, type(n).__name__, n.role, n.red, n.rank, n.span, n.key,
                   nid(n.left), nid(n.right), n.handle.pair.pair_id if isinstance(n, ExternalLeaf) else None)
                  for key, n in sorted(self._nodes.items())),
            tuple((family, h.pair.pair_id) for family, h in sorted(self._dummies.items())),
        )
