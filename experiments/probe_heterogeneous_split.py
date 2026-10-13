"""Reproducible operation-work evidence, not Jordan sorting or timing.

The test fixture only generates geometry and calls the real backend. The
independent list oracle and complete tree audit are outside operation buckets.
Initial construction is a baseline; every subsequent operation is recorded.
"""
import argparse
from contextlib import contextmanager
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from test_heterogeneous_finger_split import build, stage_parent
from sibling_list_backend import LEFT, RIGHT
from heterogeneous_finger_backend import HeterogeneousFingerBackend, WorkLedger


def probe(n, count, side, stream, seed=39):
    case = f'{n}-{count}-{side}-seed{seed}'
    f, lid, model = build(n, seed)
    b = f.backend
    baseline = b.work.snapshot()['operations']
    totals = dict.fromkeys(WorkLedger.FIELDS, 0)
    phase_totals = {p: totals.copy() for p in b.work.phases}
    split_totals = totals.copy()
    seq = 0
    original_observe = b.work.observe

    @contextmanager
    def record(bucket, operation):
        nonlocal seq
        outer = b.work.active is None
        with original_observe(bucket, operation):
            yield
        if outer and bucket == 'operations':
            item = b.work.last_operation
            if item['status'] != 'ok':
                raise RuntimeError('failed operation in accepted work sequence')
            stream.write(json.dumps({'case': case, 'sequence': seq, **item}, sort_keys=True)+'\n')
            seq += 1
            for key, value in item['work'].items():
                if sum(p[key] for p in item['phases'].values()) != value:
                    raise RuntimeError('phase partition mismatch')
                totals[key] += value
                if operation == 'split_pairs_at_value':
                    split_totals[key] += value
                for phase in phase_totals:
                    phase_totals[phase][key] += item['phases'][phase][key]

    b.work.observe = record

    def check(out, expected):
        b.validate_invariants()
        if out is None:
            if expected: raise RuntimeError('lost nonempty output')
        elif (b.list_size(out) != len(expected) or
              (b.list_owner(out), tuple(p.pair_id for p in expected)) not in b.materialize_audit()):
            raise RuntimeError('split/insert disagrees with independent sequence')

    def split(out, expected, k, acquired_side):
        cut = (b.pair_handle(expected[k-1].pair_id).high + b.pair_handle(expected[k].pair_id).low)/2
        parent = stage_parent(f, out, cut, acquired_side)
        stable = [(b.pair_handle(p.pair_id), b.pair_handle(p.pair_id).leaf) for p in expected]
        result = b.split_pairs_at_value(out, cut, acquired_side, parent.pair_id)
        outputs = [(result.left_list_id, expected[:k]), (result.right_list_id, expected[k:])]
        for h, leaf in stable:
            if h.leaf is not leaf: raise RuntimeError('leaf identity changed')
        for new_id, items in outputs: check(new_id, items)
        return outputs

    def insert(out, expected, end):
        header = b._lists[out]
        anchor = expected[0 if end == LEFT else -1]
        h = b.pair_handle(anchor.pair_id)
        limit = h.low-12 if end == LEFT else h.high+12
        if not header.owner.pair.is_dummy:
            limit = max(limit, header.owner.low) if end == LEFT else min(limit, header.owner.high)
        for other in header.owner.child_slots:
            if other is header: continue
            if end == LEFT and other.right_finger.handle.high < h.low:
                limit = max(limit, other.right_finger.handle.high)
            if end == RIGHT and h.high < other.left_finger.handle.low:
                limit = min(limit, other.left_finger.handle.low)
        if end == LEFT:
            gap = (h.low-limit)/3
            pair = f.pair(h.low-2*gap, h.low-gap)
        else:
            gap = (limit-h.high)/3
            pair = f.pair(h.high+gap, h.high+2*gap)
        if b.insert_boundary(pair.pair_id, anchor.pair_id, end) != out:
            raise RuntimeError('insertion changed live list id')
        expected.insert(0,pair) if end == LEFT else expected.append(pair)
        check(out, expected)

    outputs = split(lid, model, count, side)
    for out, expected in outputs:
        insert(out, expected, LEFT)
        insert(out, expected, RIGHT)
        for fresh, items in split(out, expected, len(expected)//2, side):
            insert(fresh, items, RIGHT)
    final = b.work.snapshot()
    if any(final['operations'][k]-baseline[k] != totals[k] for k in totals):
        raise RuntimeError('raw sum differs from ledger delta')
    return {'case': case, 'initial_items': n, 'first_cut_count': count,
            'acquired_side': side, 'seed': seed, 'records': seq, 'model_and_structure_passed': True,
            'initial_construction_baseline': baseline,
            'recorded_operation_totals': totals, 'split_totals': split_totals,
            'phase_totals': phase_totals, 'final_buckets': final}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw=args.output_dir/'operation_work.jsonl'
    with raw.open('w') as stream:
        cases=[probe(n,k,side,stream) for n in (32,128)
               for k in (1,n//2,n-1) for side in (LEFT,RIGHT)]
        cases += [probe(n,k,LEFT,stream,seed) for n,seed,k in ((5,0,3),(5,1,4),(7,2,6))]
    raw_bytes=raw.read_bytes()
    with (args.output_dir/'operation_work.jsonl.gz').open('wb') as target:
        with gzip.GzipFile(fileobj=target, mode='wb', mtime=0, filename='') as zipped:
            zipped.write(raw_bytes)
    raw.unlink()  # Only this script's newly generated redundant uncompressed copy.
    sources=['src/heterogeneous_finger_backend.py','src/heterogeneous_finger_split.py',
             'tests/test_heterogeneous_finger_backend.py','tests/test_heterogeneous_finger_split.py',
             'experiments/probe_heterogeneous_split.py']
    summary={'scope':'partial_split_adopt_interleaved_operations',
             'sorting_ready':HeterogeneousFingerBackend.sorting_ready,
             'sorting_validated_by_this_probe':False,
             'backend_ready_for_timing':False, 'contract_acceptance_passed':False,
             'metrics_schema':HeterogeneousFingerBackend.metrics_schema,
             'initial_construction_excluded_from_raw':True, 'cases':cases,
             'raw_sha256':hashlib.sha256(raw_bytes).hexdigest(),
             'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
    (args.output_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'scope':summary['scope'],'cases_passed':len(cases),
                      'records':sum(c['records'] for c in cases),
                      'sorting_ready':summary['sorting_ready'],
                      'sorting_validated_by_this_probe':False}))


if __name__=='__main__': main()
