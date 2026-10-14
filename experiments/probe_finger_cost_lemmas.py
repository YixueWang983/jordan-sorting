"""Bounded checks of source-level cost lemmas; no timing or proof by curve."""
import argparse
from contextlib import contextmanager
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests'), str(ROOT/'experiments')]
from heterogeneous_finger_backend import ExternalLeaf, InternalNode, INTERIOR, ROOT as TREE_ROOT
from heterogeneous_finger_split import RootedPiece, TreeOperations
from sibling_list_backend import LEFT, RIGHT
from test_heterogeneous_finger_backend import Fixture
from probe_heterogeneous_split import probe as interleaved_probe


def normal_rank(node):
    return node.rank + int(node.red)


@lru_cache(None)
def forms(n):
    """All colored, ordered full RB shapes with n leaves, including red roots."""
    if n == 1:
        return ((False, 0, None, None),)
    result = []
    for k in range(1, n):
        for left in forms(k):
            for right in forms(n-k):
                if left[1] != right[1]:
                    continue
                result.append((False, left[1]+1, left, right))
                if not left[0] and not right[0]:
                    result.append((True, left[1], left, right))
    return tuple(result)


def build_down(form, fixture, offset=0):
    b = fixture.backend
    if form[2] is None:
        pair = fixture.pair(10*offset, 10*offset+1)
        node = b._leaf(b.pair_handle(pair.pair_id), INTERIOR)
        return RootedPiece(b.work, node, 1, node.key)
    left = build_down(form[2], fixture, offset)
    right = build_down(form[3], fixture, offset+left.size)
    node = InternalNode(b.work, b._node_id(), INTERIOR, form[0], form[1],
                        left.size+right.size, left.maximum, left.root, right.root)
    b._store(b._nodes, node.node_id, node)
    return RootedPiece(b.work, node, left.size+right.size, right.maximum)


def audit_down(piece):
    if piece is None:
        return []
    def visit(node):
        if isinstance(node, ExternalLeaf):
            assert not node.red and node.rank == 0 and node.span == 1
            return [node.key]
        left, right = visit(node.left), visit(node.right)
        assert not (node.red and (node.left.red or node.right.red))
        assert node.left.rank == node.right.rank
        assert node.rank == node.left.rank + int(not node.red)
        assert node.span == len(left)+len(right) and node.key == left[-1]
        assert left[-1] < right[0]
        return left+right
    values = visit(piece.root)
    assert len(values) == piece.size and values[-1] == piece.maximum
    return values


def forest_potential(backend):
    """Outside operations: Phi = black/BB + 2*black/RR; external leaves zero."""
    total = 0
    for header in backend._lists.values():
        outside = {}
        for side, finger in ((LEFT, header.left_finger), (RIGHT, header.right_finger)):
            node = finger
            while node is not header.root:
                parent = backend._up(node, side)
                outside[(parent.node_id, side)] = node
                node = parent
        stack = [header.root]
        while stack:
            node = stack.pop()
            if isinstance(node, ExternalLeaf):
                continue
            if node.role == TREE_ROOT:
                left, right = header.left_top, header.right_top
            elif node.role == LEFT:
                left, right = outside[(node.node_id, LEFT)], node.right
            elif node.role == RIGHT:
                left, right = node.left, outside[(node.node_id, RIGHT)]
            else:
                left, right = node.left, node.right
            if not node.red:
                total += 2 if left.red and right.red else int(not left.red and not right.red)
            stack.extend((left, right))
    return total


@contextmanager
def observe_lemmas(events):
    join = TreeOperations.join_down
    split = TreeOperations.split_down
    repair = TreeOperations.repair_short
    rib = TreeOperations.rib_child
    active_split = []; active_repair = []

    def joining(self, left, right, connector):
        if left is None or right is None:
            return join(self, left, right, connector)
        a, b = normal_rank(left.root), normal_rank(right.root)
        raw = [left.root.rank, right.root.rank]
        before = self.b.work.buckets['operations']['rooted_join_steps']
        result = join(self, left, right, connector)
        steps = self.b.work.buckets['operations']['rooted_join_steps']-before
        assert max(a,b) <= result.root.rank <= max(a,b)+1
        assert steps <= 2*abs(a-b)+3
        row = {'kind':'join', 'raw_ranks':raw, 'normalized_ranks':[a,b],
               'result_rank':result.root.rank, 'recursive_calls':steps}
        if active_split:
            direction = active_split[-1]['directions'][connector.node_id]
            acc, other = (b,a) if direction == RIGHT else (a,b)
            assert acc <= other+1
            row.update(side=direction, accumulator=acc, sibling=other)
            active_split[-1]['joins'].append(row)
        events.append(row)
        return result

    def splitting(self, piece, value):
        node = piece.root; directions = {}
        source_rank, source_red = node.rank, node.red
        while isinstance(node, InternalNode):
            direction = LEFT if value < node.key else RIGHT
            directions[node.node_id] = direction
            node = node.left if direction == LEFT else node.right
        record = {'directions':directions, 'joins':[]}
        active_split.append(record)
        try:
            left, right = split(self, piece, value)
        finally:
            active_split.pop()
        for output in (left,right):
            if output is None:
                continue
            assert normal_rank(output.root) <= source_rank+1
            if not source_red and normal_rank(output.root) == source_rank+1:
                assert not output.root.red and not output.root.left.red and not output.root.right.red
        steps = sum(row['recursive_calls'] for row in record['joins'])
        result_ranks = [normal_rank(p.root) if p is not None else 0 for p in (left,right)]
        assert steps <= 2*sum(result_ranks)+5*len(record['joins'])
        events.append({'kind':'split_down', 'source_rank':source_rank, 'source_red':source_red,
                       'frames':len(directions), 'joins':len(record['joins']),
                       'recursive_calls':steps, 'result_normalized_ranks':result_ranks})
        return left,right

    def repairing(self, header, short, side):
        record = {'start_rank':short.rank, 'rib_calls':0, 'rib_steps':0}
        before_potential = forest_potential(self.b)
        before = self.b.work.buckets['operations']['deletion_propagations']
        active_repair.append(record)
        try:
            result = repair(self, header, short, side)
        finally:
            active_repair.pop()
        record['propagations'] = self.b.work.buckets['operations']['deletion_propagations']-before
        record['potential_change'] = forest_potential(self.b)-before_potential
        assert record['propagations']+record['potential_change'] <= 8
        assert record['rib_calls'] <= 2
        assert record['rib_steps'] <= 4*(record['start_rank']+record['propagations']+2)
        events.append({'kind':'repair_short', **record})
        return result

    def walking(self, header, node, side):
        assert active_repair and self.b._up(node, side) is header.root
        before = self.b.work.buckets['operations']['rib_steps']
        result = rib(self, header, node, side)
        active_repair[-1]['rib_calls'] += 1
        active_repair[-1]['rib_steps'] += self.b.work.buckets['operations']['rib_steps']-before
        return result

    with patch.object(TreeOperations,'join_down',joining), patch.object(TreeOperations,'split_down',splitting), \
         patch.object(TreeOperations,'repair_short',repairing), patch.object(TreeOperations,'rib_child',walking):
        yield


def exhaustive_splits(max_leaves=10):
    rows = []; cases = 0
    with observe_lemmas(rows):
        for n in range(1,max_leaves+1):
            for form_index, form in enumerate(forms(n)):
                for k in range(n+1):
                    first = len(rows)
                    fixture=Fixture(); piece=build_down(form,fixture)
                    with fixture.backend.work.observe('operations','lemma_split'):
                        left,right=TreeOperations(fixture.backend).split_down(piece,10*k-5)
                    assert audit_down(left)==list(range(0,10*k,10))
                    assert audit_down(right)==list(range(10*k,10*n,10))
                    for row in rows[first:]:
                        row['case'] = {'leaves':n, 'shape_index':form_index, 'cut':k}
                    cases+=1
    return cases, rows


def mixed_updates():
    from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
    from io import StringIO
    events=[]; histories=[]; inserts=[]
    insert=Tree.insert_boundary
    def inserting(b,*args,**kwargs):
        phi=forest_potential(b)
        cascades=b.work.buckets['operations']['recolor_cascades']
        result=insert(b,*args,**kwargs)
        q=b.work.buckets['operations']['recolor_cascades']-cascades
        delta=forest_potential(b)-phi
        assert q+delta <= 8
        inserts.append({'cascades':q,'potential_change':delta})
        return result
    with observe_lemmas(events),patch.object(Tree,'insert_boundary',inserting):
        for n,k,seed in ((32,3,0),(32,7,1),(32,11,2),(128,5,0),(128,17,1),(128,41,2)):
            for side in (LEFT,RIGHT):
                first_event, first_insert = len(events), len(inserts)
                raw=StringIO()
                record=interleaved_probe(n,k,side,raw,seed)
                for row in events[first_event:]: row['case'] = record['case']
                for row in inserts[first_insert:]: row['case'] = record['case']
                # Observer reads affect generic field counts. Preserve only
                # explicit algorithm counters, with each operation's identity.
                steps = ('rooted_join_steps','rib_steps','deletion_propagations',
                         'recolor_cascades','join_calls','split_calls','rotations')
                operations = [json.loads(line) for line in raw.getvalue().splitlines()]
                histories.append({'case':record['case'], 'operations':record['records'],
                    'explicit_operation_steps':[
                        {'sequence':row['sequence'],'operation':row['operation'],
                         'steps':{key:row['work'][key] for key in steps}} for row in operations],
                    'model_and_structure_passed':record['model_and_structure_passed']})
    return histories,inserts,events


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    paths = sorted((ROOT/'src').glob('*.py')) + [ROOT/p for p in (
        'experiments/probe_finger_cost_lemmas.py','experiments/probe_heterogeneous_split.py',
        'tests/test_heterogeneous_finger_backend.py','tests/test_heterogeneous_finger_split.py')]
    source = lambda: {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before = source()
    (output/'plan.json').write_text(json.dumps({'max_exhaustive_leaves':10,
        'mixed_n_k_seed':[(32,3,0),(32,7,1),(32,11,2),(128,5,0),(128,17,1),(128,41,2)],
        'sides':[LEFT,RIGHT], 'source_sha256':before},indent=2)+'\n')
    cases,events=exhaustive_splits()
    histories,inserts,mixed=mixed_updates()
    # Explicit counterexample to a pre-normalization '+1' statement.
    f=Fixture(); form=(True,0,forms(1)[0],forms(1)[0])
    a,b=build_down(form,f),build_down(form,f,2)
    connector=InternalNode(f.backend.work,f.backend._node_id(),INTERIOR,True,0,0,10)
    with f.backend.work.observe('operations','red_red_join'):
        result=TreeOperations(f.backend).join_down(a,b,connector)
    assert result.root.rank==2 and audit_down(result)==[0,10,20,30]
    data={'scope':'bounded_cost_lemma_checks_not_a_general_proof', 'exhaustive_split_cases':cases,
          'max_exhaustive_leaves':10,'histories':histories,'inserts':inserts,
          'events':events+mixed,'raw_red_root_join':{'before':[0,0],'normalized':[1,1],'result':2},
          'source_sha256':before}
    assert source()==before
    with gzip.open(output/'records.json.gz','wt') as stream:
        json.dump(data,stream)
    print(json.dumps({'exhaustive_split_cases':cases,'mixed_histories':len(histories),
                      'join_rank_gaps':sorted({abs(r['normalized_ranks'][0]-r['normalized_ranks'][1]) for r in data['events'] if r['kind']=='join'}),
                      'root_rib_walks':sum(r['rib_calls'] for r in data['events'] if r['kind']=='repair_short')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
