"""Frozen structural correctness/resource campaign, never a timing benchmark."""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments')]
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
from oracle import oracle
from paper_execution_policy import CHECKED_POLICY, MINIMAL_POLICY
from paper_jordan import _run_paper_jordan_state_values, validate_paper_jordan_state
from sibling_backend_contract import SiblingBackendSpec
from validate_heterogeneous_integration import check_geometry


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def checksum(value):
    return sha_bytes(repr(value).encode())


def sequence(n, shape, mirror=False):
    """No search/rejection: one prescribed sequence per length/shape/mirror."""
    even_n = n - n % 2
    if shape in ('balanced', 'skew'):
        m = (even_n - 6) // 2
        k = m // 2 if shape == 'balanced' else 1
        values = [x for i in range(m) for x in (4*i, 4*i+1)]
        values += [values[-1]+1, 4*k-1, 4*k-2, values[-1]+2]
        values = [min(values)-2, max(values)+2] + values
    elif shape == 'repeated':
        length = even_n - 4
        template = (0, 1, 4, 5, 6, 3, 2, 7)
        values = [8*i+x for i in range(length//8) for x in template]
        values += list(range(len(values), length))
        for _ in range(2):
            values = [min(values)-2, max(values)+2] + values
    else:
        raise ValueError('unknown shape')
    if n % 2:
        values.append(values[-1] + 0.5)  # Inside the outer pair, past the payload.
    ranks = {x: i+1 for i, x in enumerate(sorted(values))}
    values = [ranks[x] for x in values]
    if mirror:
        values = [n+1-x for x in values]
    if len(values) != n or len(set(values)) != n:
        raise AssertionError('invalid construction size')
    return values


def config():
    # Three shapes per size; odd lengths use the reflected construction.
    # This is structural coverage, not independent sampling or a timing pool.
    return {'schema': 'finger_work_modes_v1', 'case_seconds': 180, 'batch_seconds': 900,
            'plan': [{'case': f'{shape}-{n}', 'n': n, 'shape': shape, 'mirror': bool(n % 2)}
                     for n in (128, 129, 256, 257, 512, 513)
                     for shape in ('balanced', 'skew', 'repeated')],
            'selection': 'fixed formulas; no retries, filtering or performance-based choice',
            'stop': 'any timeout, resource or correctness failure stops later cases',
            'scope': 'external prefix checks, geometry, final same-backend replay; NOT sorting timing',
            'variants': ['ordinary_list', 'tree_work_on', 'tree_work_off'],
            'policies': ['checked', 'minimal']}


def coverage(state):
    counts = Counter(); ratios = []; outputs = set(); finite = Counter()
    for e in state.trace:
        if e['step'] == 'step3a_insert_pair':
            if e['insertion_mode'] == 'boundary_insertion' and e['sibling_list_id'] in outputs:
                counts['insert_into_previous_split_output'] += 1
        if e['step'] != 'step3b_split_sibling_list' or not e['performed']:
            continue
        counts['splits'] += 1
        if e['input_list_id'] in outputs:
            counts['resplit_previous_output'] += 1
        insertion = state.stage_results[e['iteration']]['step3a_insert_pair']
        if insertion.parent_pair_id > 0:
            counts['finite_owner_splits'] += 1
            finite[insertion.parent_pair_id] += 1
        if e['left_size'] and e['right_size']:
            counts['both_nonempty'] += 1
            ratios.append([e['left_size'], e['right_size']])
        outputs.update(lid for lid in (e['left_list_id'], e['right_list_id']) if lid is not None)
    counts['finite_owners_with_multiple_transfers'] = sum(v > 1 for v in finite.values())
    return {'counts': dict(counts), 'nonempty_split_sizes': ratios}


def evaluate(spec):
    values = sequence(spec['n'], spec['shape'], spec['mirror'])
    if not oracle(values)['valid']:
        raise AssertionError('fixed construction is not a legal Jordan input')
    result = {'spec': spec, 'values': values, 'input_sha256': checksum(values), 'runs': {}}
    comparisons = {}
    for name, backend in (
        ('ordinary_list', 'ordinary_list'),
        ('tree_work_on', SiblingBackendSpec(Tree, (('detailed_work', True),))),
        ('tree_work_off', SiblingBackendSpec(Tree, (('detailed_work', False),))),
    ):
        for policy in (CHECKED_POLICY, MINIMAL_POLICY):
            prefixes = []
            def check(state):
                count = state.processed_count
                output = state.partial_order.to_list()
                if output != sorted(values[:count]):
                    raise AssertionError('external prefix output mismatch')
                check_geometry(state)
                state.sibling_backend.validate_invariants()
                if name.startswith('tree') and (state.sibling_backend._pending_transfer is not None or state.sibling_backend._pending_split is not None):
                    raise AssertionError('pending state after completed prefix')
                prefixes.append({'n': count, 'output': checksum(output),
                                 'logical': checksum(state.sibling_backend.logical_snapshot()),
                                 'physical': checksum(state.sibling_backend.audit_snapshot()),
                                 'stages': checksum(state.stage_results)})
            state = _run_paper_jordan_state_values(
                values, execution_policy=policy, backend=backend,
                invariant_callback=check if policy is CHECKED_POLICY else None)
            if policy is CHECKED_POLICY and [p['n'] for p in prefixes] != list(range(3, len(values)+1)):
                raise AssertionError('missing or duplicate prefix check')
            if state.partial_order.to_list() != sorted(values):
                raise AssertionError('external final output mismatch')
            check_geometry(state)
            validate_paper_jordan_state(state)  # final fresh same-config replay
            view = (state.partial_order.to_list(), state.sibling_backend.logical_snapshot(),
                    state.sibling_backend.audit_snapshot(), state.stage_results,
                    state.backend_work, state.metrics, state.trace, prefixes)
            if name == 'tree_work_on':
                comparisons[policy.name] = view
            elif name == 'tree_work_off' and view != comparisons[policy.name]:
                raise AssertionError('detailed-work switch changed algorithm behavior')
            row = {'backend_identity': state.backend_identity, 'prefixes': prefixes,
                   'output': state.partial_order.to_list(), 'state_digest': checksum(view[:-1]),
                   'final_output_geometry_replay_passed': True}
            if policy is CHECKED_POLICY:
                row['coverage'] = coverage(state)
                if not row['coverage']['counts'].get('both_nonempty'):
                    raise AssertionError('planned nonempty split coverage missing')
                if spec['shape'] == 'repeated' and (
                    row['coverage']['counts'].get('finite_owners_with_multiple_transfers', 0) == 0
                    or row['coverage']['counts'].get('insert_into_previous_split_output', 0) == 0
                ):
                    raise AssertionError('planned repeated transfer/update coverage missing')
            row['detailed_work_collected'] = name == 'tree_work_on'
            if name == 'tree_work_on':
                row['work_buckets'] = state.sibling_backend.work.snapshot()
            if name == 'tree_work_off' and (state.sibling_backend.work.buckets is not None or state.sibling_backend.work.last_operation is not None):
                raise AssertionError('disabled work still collected')
            result['runs'][name+'/'+policy.name] = row
    result['status'] = 'PASS'
    return result


def sources():
    paths = sorted((ROOT/'src').glob('*.py')) + [Path(__file__).resolve(), ROOT/'experiments/validate_heterogeneous_integration.py']
    return {str(p.relative_to(ROOT)): sha_bytes(p.read_bytes()) for p in paths}


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    cfg = config()
    (output/'config.json').write_text(json.dumps(cfg, indent=2)+'\n')
    provenance = {'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                  'source_sha256': sources(), 'python': sys.version, 'platform': platform.platform()}
    (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    rows = []; stopped = None; start = time.monotonic()
    for spec in cfg['plan']:
        remaining = cfg['batch_seconds'] - (time.monotonic()-start)
        stem = output/spec['case']
        request = stem.with_suffix('.request.json'); report = stem.with_suffix('.json.gz')
        request.write_text(json.dumps(spec)+'\n')
        if stopped or remaining <= 0:
            row = {'spec': spec, 'status': 'NOT_RUN', 'reason': stopped or 'batch budget exhausted'}
        else:
            tick = time.monotonic()
            try:
                process = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', str(request), str(report)],
                                         timeout=min(remaining, cfg['case_seconds']), capture_output=True, text=True)
                if process.returncode:
                    row = {'spec': spec, 'status': 'ERROR', 'stderr': process.stderr[-4000:]}
                else:
                    with gzip.open(report, 'rt') as stream:
                        row = json.load(stream)
            except subprocess.TimeoutExpired:
                row = {'spec': spec, 'status': 'TIMEOUT'}
            row['worker_resource_wall_seconds'] = time.monotonic()-tick
            if row['status'] != 'PASS':
                stopped = spec['case']+': '+row['status']
        # Parent writes the complete outcome, including failure/resource status.
        with report.open('wb') as dest:
            with gzip.GzipFile(fileobj=dest, mode='wb', mtime=0, filename='') as stream:
                stream.write((json.dumps(row, sort_keys=True)+'\n').encode())
        rows.append({'case': spec['case'], 'status': row['status'],
                     'coverage': row.get('runs',{}).get('tree_work_on/checked',{}).get('coverage')})
        print(spec['case'], row['status'], flush=True)
    unchanged = sources() == provenance['source_sha256']
    accepted = all(row['status'] == 'PASS' for row in rows) and unchanged
    summary = {'accepted': accepted, 'source_unchanged': unchanged, 'outcomes': rows,
               'status_counts': dict(Counter(row['status'] for row in rows)),
               'backend_ready_for_timing': False, 'full_amortized_bound_proved': False,
               'resource_scope': 'whole worker includes generation, certification, six executions, audits and replay; not sorting performance'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({p.name: sha_bytes(p.read_bytes()) for p in sorted(output.iterdir()) if p.is_file()},indent=2)+'\n')
    return 0 if accepted else 2


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        spec = json.loads(Path(sys.argv[2]).read_text())
        try:
            result = evaluate(spec)
        except Exception as error:
            result = {'spec': spec, 'status': 'ERROR', 'error': repr(error), 'traceback': traceback.format_exc()}
        with gzip.open(sys.argv[3], 'wt') as stream:
            json.dump(result, stream)
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--output', type=Path, required=True)
        raise SystemExit(run(parser.parse_args().output.resolve()))
