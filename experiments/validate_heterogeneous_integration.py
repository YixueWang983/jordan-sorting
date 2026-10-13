"""Bounded real-tree/shared-loop correctness evidence; never timing data.

Input qualification and sorted expected output stay outside the core. Each
backend is independently checked against these, including every completed
prefix. Same-backend replay is a consistency check, not an independent sorter.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from generators import generate_flat, generate_nested, generate_incremental_valid
from heterogeneous_finger_backend import HeterogeneousFingerBackend
from oracle import oracle
from paper_execution_policy import CHECKED_POLICY, MINIMAL_POLICY
from paper_jordan import _run_paper_jordan_state_values, validate_paper_jordan_state
from paper_jordan_sort import paper_jordan_sort_valid


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_geometry(state):
    """Independent O(n^2) closest-enclosing-parent model, audit path only."""
    records = state.sibling_backend.logical_snapshot()[1]
    intervals = {}
    dummies = {}
    for pid, end, first, second, family, dummy, owner, groups in records:
        if dummy:
            dummies[family] = pid
        else:
            a, b = state.point_value(first), state.point_value(second)
            intervals[pid] = (min(a, b), max(a, b), family)
    expected_children = {row[0]: set() for row in records}
    for pid, end, first, second, family, dummy, owner, groups in records:
        if dummy:
            if owner is not None:
                raise AssertionError("dummy has an owner")
            continue
        low, high, _ = intervals[pid]
        enclosing = [(a, other) for other, (a, b, f) in intervals.items()
                     if f == family and a < low and high < b]
        expected_owner = max(enclosing)[1] if enclosing else dummies[family]
        if owner != expected_owner:
            raise AssertionError(f"closest enclosing owner mismatch at pair {pid}")
        expected_children[owner].add(pid)
    for pid, end, first, second, family, dummy, owner, groups in records:
        flat = [child for group in groups for child in group]
        if len(groups) > 2 or any(not group for group in groups):
            raise AssertionError("invalid child-group shape")
        if len(set(flat)) != len(flat) or set(flat) != expected_children[pid]:
            raise AssertionError("child-group membership mismatch")
        if any(intervals[a][1] >= intervals[b][0] for a, b in zip(flat, flat[1:])):
            raise AssertionError("child intervals overlap or are out of order")


def validate_case(label, values):
    values = list(values)
    if not oracle(values)["valid"]:
        raise AssertionError(f"fixed/generated input is not qualified: {label}")
    results = {}
    for backend in ("ordinary_list", "heterogeneous_finger"):
        prefixes = []
        def inspect(state):
            if state.partial_order.to_list() != sorted(values[:state.processed_count]):
                raise AssertionError(f"prefix output mismatch: {label}/{backend}")
            b = state.sibling_backend
            if backend == "heterogeneous_finger":
                if type(b) is not HeterogeneousFingerBackend:
                    raise AssertionError("tree selection returned a different backend")
                if b._pending_transfer is not None or b._pending_split is not None:
                    raise AssertionError("completed prefix still pending")
            check_geometry(state)
            validate_paper_jordan_state(state)  # includes fresh same-backend replay
            prefixes.append(state.processed_count)
        if len(values) < 3:
            for mode in ("checked", "minimal"):
                if paper_jordan_sort_valid(values, mode, backend=backend) != sorted(values):
                    raise AssertionError("small output mismatch")
            results[backend] = {"prefixes": [], "splits": 0, "both_sides_nonempty": 0,
                                "branches": {}, "z1_boundary": 0, "z1_output": 0}
            continue
        state = _run_paper_jordan_state_values(values, execution_policy=CHECKED_POLICY,
                                             backend=backend, invariant_callback=inspect)
        if prefixes != list(range(3, len(values) + 1)):
            raise AssertionError('not every completed prefix was checked exactly once')
        # A separate minimal run is also externally checked and replay-audited.
        minimal = _run_paper_jordan_state_values(values, execution_policy=MINIMAL_POLICY, backend=backend)
        if minimal.partial_order.to_list() != sorted(values):
            raise AssertionError("minimal output mismatch")
        check_geometry(minimal)
        validate_paper_jordan_state(minimal)
        if minimal.sibling_backend.audit_snapshot() != state.sibling_backend.audit_snapshot():
            raise AssertionError("policy changed physical state")
        if minimal.stage_results != state.stage_results:
            raise AssertionError("policy changed mandatory stage results")
        branches = Counter()
        transfers = []
        for iteration, stages in state.stage_results.items():
            insertion = stages["step3a_insert_pair"]
            split = stages["step3b_split_sibling_list"]
            if split.performed:
                branch = '/'.join((insertion.orientation, insertion.insertion_mode,
                                   'finite_owner' if insertion.parent_pair_id > 0 else 'dummy_owner'))
                branches[branch] += 1
                transfers.append({"iteration": iteration, "source": insertion.transfer_source_list_id,
                                  "owner": insertion.parent_pair_id, "target": insertion.sibling_list_id,
                                  "left": split.left_list_id, "right": split.right_list_id,
                                  "acquired_side": split.acquired_side})
        results[backend] = {
            "backend_identity": state.backend_identity, "prefixes": prefixes,
            "splits": len(transfers), "both_sides_nonempty": sum(
                t['left'] is not None and t['right'] is not None for t in transfers),
            "branches": dict(branches), "transfers": transfers,
            "z1_boundary": state.metrics["z1_boundary_adjustments"],
            "z1_output": state.metrics["z1_output_anchor_adjustments"],
        }
        if backend == "heterogeneous_finger":
            # Diagnostic observations only, includes initialization. Full audit
            # is a separate bucket. Replay creates separate ledgers, excluded.
            results[backend]["checked_work_buckets"] = state.sibling_backend.work.snapshot()
            results[backend]["minimal_work_buckets"] = minimal.sibling_backend.work.snapshot()
    return {"case": label, "values": values, "input_sha256": digest(json.dumps(values).encode()),
            "qualified": True, "external_output_and_geometry_passed": True,
            "same_backend_replay_passed": True, "results": results}


def cases(max_n):
    for n in range(max_n + 1):
        for values in itertools.permutations(range(n)):
            if oracle(values)["valid"]:
                yield f"exhaustive/{n}", values
    for i, values in enumerate(([1, 2, 3, 4, 6, 7, 0, 5], [3, 2, 1, 4, 5])):
        for mirror in (False, True):
            yield f"fixed/{i}/mirror={mirror}", [-x for x in values] if mirror else values
    for n in (16, 32, 64):
        for family, values in (("flat", generate_flat(n)), ("nested", generate_nested(n)),
                               ("incremental", generate_incremental_valid(n, seed=13000+n))):
            for mirror in (False, True):
                yield f"structured/{family}/{n}/seed={13000+n}/mirror={mirror}", [-x for x in values] if mirror else values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--max-n', type=int, default=7, choices=range(3, 9))
    args = parser.parse_args()
    sources = sorted(ROOT.glob('src/*.py')) + [Path(__file__).resolve(), ROOT / 'tests/test_heterogeneous_sort_integration.py']
    source_hashes = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sources}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    records = []
    # Output remains unaccepted if an exception occurs; no failure filtering.
    with (args.output_dir / 'cases.jsonl.gz').open('wb') as out:
        with gzip.GzipFile(fileobj=out, mode='wb', mtime=0, filename='') as stream:
            for label, values in cases(args.max_n):
                result = validate_case(label, values)
                records.append(result)
                stream.write((json.dumps(result, sort_keys=True) + '\n').encode())
    aggregate = {}
    for backend in ('ordinary_list', 'heterogeneous_finger'):
        branches = Counter()
        for record in records:
            branches.update(record['results'][backend]['branches'])
        aggregate[backend] = {name: sum(r['results'][backend][name] for r in records)
                              for name in ('splits', 'both_sides_nonempty', 'z1_boundary', 'z1_output')}
        aggregate[backend]['completed_prefixes_checked'] = sum(len(r['results'][backend]['prefixes']) for r in records)
        aggregate[backend]['branches'] = dict(branches)
    if source_hashes != {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sources}:
        raise RuntimeError('validation sources changed during the run')
    summary = {
        'scope': 'bounded_end_to_end_correctness_not_timing', 'accepted': True,
        'backend_ready_for_timing': False, 'amortized_bound_proved': False,
        'max_exhaustive_n': args.max_n, 'case_runs': len(records),
        'distinct_input_hashes': len({r['input_sha256'] for r in records}),
        'exhaustive_qualified_by_n': dict(Counter(r['case'].split('/')[1] for r in records if r['case'].startswith('exhaustive/'))),
        'aggregate': aggregate, 'python': sys.version, 'platform': platform.platform(),
        'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'worktree_differs_from_base': bool(subprocess.check_output(
            ['git', 'status', '--porcelain', '--', 'src', 'tests', 'experiments'], cwd=ROOT, text=True).strip()),
        'source_sha256': source_hashes,
        'cases_gzip_sha256': digest((args.output_dir / 'cases.jsonl.gz').read_bytes()),
        'mirror_rule': 'negate each value; related inputs, not independent statistical samples',
        'policy_scope': 'checked: each prefix + fresh replay; minimal: final state + fresh replay; both external output and geometry',
    }
    (args.output_dir / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: summary[k] for k in ('scope', 'accepted', 'case_runs', 'aggregate')}, sort_keys=True))


if __name__ == '__main__':
    main()
