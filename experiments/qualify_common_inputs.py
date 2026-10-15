"""Fixed-budget common qualification. No timing, warmups or performance claims."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification evidence requires optimization level 0')
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

from common_input_protocol import (ROOT, SCHEMA, SIZES, CATEGORIES, TARGETS, BACKENDS,
    candidate_specs, generate, qualification_plan, measurement_protocol, source_identity, digest)
from committed_records import atomic_json, commit_record, read_records, run_bounded, canonical
from matched_backend_fixture import backend_spec, identity, capture_output, error_details
from oracle import oracle
from stats import structure_profile
from paper_jordan_sort import paper_jordan_diagnostics_valid, paper_jordan_sort_valid


def read(path):
    return json.loads(Path(path).read_text())


def environment():
    def command(args):
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    hardware = {}
    if sys.platform == 'darwin':
        for key in ('machdep.cpu.brand_string', 'hw.physicalcpu', 'hw.logicalcpu', 'hw.memsize'):
            hardware[key] = command(['sysctl', '-n', key])
        hardware['power'] = command(['pmset', '-g', 'batt'])
    else:
        hardware['processor'] = platform.processor() or 'unavailable'
    return dict(head=command(['git', 'rev-parse', 'HEAD']),
                dirty=bool(command(['git', 'status', '--porcelain'])),
                source_sha256=source_identity(), captured_at=datetime.now(timezone.utc).isoformat(),
                python=sys.version, executable=sys.executable, platform=platform.platform(),
                machine=platform.machine(), hardware=hardware, python_optimize=sys.flags.optimize,
                gc_enabled=gc.isenabled(), gc_thresholds=list(gc.get_threshold()),
                purpose='qualification resource observations only')


def select(output, deadline):
    directory = output/'selection'; directory.mkdir()
    selected, known, counts = [], {}, Counter()
    record_index = 0
    for spec in candidate_specs():
        cell = (spec['n'], spec['requested_category'])
        if counts[cell] == TARGETS[cell[1]]:
            continue  # Remaining candidates are explicitly unused, never replacements.
        if time.monotonic() >= deadline:
            raise TimeoutError('selection resource budget exhausted')
        atomic_json(directory/'progress.json', dict(status='RUNNING', candidate=spec))
        values = generate(spec)
        if sorted(values) != list(range(1, spec['n']+1)):
            raise ValueError('generator returned a noncanonical rank permutation')
        cert = oracle(values)
        profile = structure_profile(values, oracle_result=cert)
        key = digest(values)
        status = ('INVALID' if cert['valid'] is not True else
                  'CATEGORY_MISMATCH' if profile['category'] != cell[1] else
                  'DUPLICATE' if key in known else 'SELECTED')
        row = dict(spec=spec, values=values, input_sha256=key, rank_sha256=key,
                   status=status, duplicate_of=known.get(key), profile=profile,
                   oracle={k:v for k,v in cert.items() if k != 'sorted'})
        commit_record(directory, record_index, row); record_index += 1
        if status == 'SELECTED':
            known[key] = spec['case']; counts[cell] += 1; selected.append(row)
    selected.sort(key=lambda r:(-r['spec']['n'], CATEGORIES.index(r['spec']['requested_category']),
                                r['spec']['candidate_index'], r['spec']['mirror']))
    atomic_json(directory/'progress.json', dict(status='COMPLETE', selected=len(selected)))
    result = dict(cases=selected, selection_sha256=digest(selected),
                  deficits=[dict(n=n, category=c, target=TARGETS[c], selected=counts[n,c])
                            for n in SIZES for c in CATEGORIES if counts[n,c] != TARGETS[c]])
    atomic_json(output/'selected.json', result)
    return result


def qualify_case(request, output):
    """One isolated input; success rows are durable before the next public call."""
    output.mkdir(parents=True, exist_ok=False)
    values = request['values']; expected = sorted(values); index = 0
    for name in request['backends']:
        for mode in ('checked', 'minimal'):
            action = dict(backend=name, mode=mode, case=request['case'])
            atomic_json(output/'progress.json', dict(status='RUNNING', action=action))
            row = dict(**action, input_sha256=digest(values), backend_identity=identity(name),
                       status='PASS', error=None)
            try:
                source_values = list(values)
                if mode == 'checked':
                    result = paper_jordan_diagnostics_valid(source_values, backend=backend_spec(name))
                    if type(result) is not dict:
                        raise TypeError('diagnostics must return a dictionary')
                    row.update(capture_output(result.get('output')))
                    count = result.get('processed_count')
                    row.update(processed_count=count if type(count) is int else None,
                               invariants_valid=result.get('invariants_valid') is True,
                               same_backend_replay=False)
                    if (type(count) is not int or count != len(values) or not row['invariants_valid']
                            or canonical(result.get('backend_identity')) != canonical(identity(name))):
                        raise ValueError('checked count/audit/backend identity mismatch')
                    row.update(same_backend_replay=True, replay_prefixes=len(values)-2,
                               metrics=result['metrics'], trace=result['trace'])
                else:
                    row.update(capture_output(paper_jordan_sort_valid(
                        source_values, 'minimal', backend=backend_spec(name))))
                if row['output'] != expected:
                    raise ValueError('external output mismatch')
                if source_values != values:
                    raise ValueError('input mutation')
            except Exception as exc:
                row.update(status='ERROR', error=error_details(exc))
            try:
                canonical(row)
            except (TypeError, ValueError, OverflowError, RecursionError) as exc:
                row = dict(**action, input_sha256=digest(values), backend_identity=identity(name),
                           status='ERROR', error=error_details(exc, 'SerializationError'))
            commit_record(output, index, row); index += 1
            if row['status'] != 'PASS':
                return 2
    atomic_json(output/'progress.json', dict(status='COMPLETE', committed_records=index))
    return 0


def seal(output):
    atomic_json(output/'manifest.json', {str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.rglob('*')) if p.is_file() and p != output/'manifest.json'})


def run(output):
    env = environment()
    if env['dirty']:
        raise RuntimeError('commit source and rules before actual qualification')
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output/'plan.json', qualification_plan())
    atomic_json(output/'measurement_protocol.json', measurement_protocol())
    atomic_json(output/'environment.json', env)
    start = time.monotonic(); deadline = start + 1800
    try:
        selection = select(output, min(deadline, start+180))
    except Exception as exc:
        atomic_json(output/'failure.json', dict(accepted=False, phase='selection', error=error_details(exc)))
        seal(output); return False
    rows = []; stop = None
    (output/'requests').mkdir(); (output/'jobs').mkdir()
    for index, case in enumerate(selection['cases']):
        cid = case['spec']['case']
        order = list(BACKENDS if index%2 == 0 else BACKENDS[::-1])
        request = dict(case=cid, values=case['values'], backends=order)
        path = output/'requests'/f'{cid}.json'; atomic_json(path, request)
        remaining = deadline-time.monotonic()
        budget = min(180, max(0, remaining))
        base = dict(case=cid, input_sha256=case['input_sha256'], backends=order,
                    budget_seconds=budget, worker_resource_wall_seconds=0, status='NOT_RUN', reason=stop)
        if stop is None and remaining > 0:
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', str(path), '--output', str(output/'jobs'/cid)]
            atomic_json(output/'progress.json', dict(status='RUNNING', case=cid, index=index, command=command))
            tick = time.monotonic()
            code = run_bounded(command, output/'jobs'/cid, budget)
            base['worker_resource_wall_seconds'] = time.monotonic()-tick
            base['status'] = 'PASS' if code == 0 else (
                'TIMEOUT' if read(output/'jobs'/cid/'failure.json')['status'] == 'RESOURCE_TIMEOUT' else 'ERROR')
            if code == 0:
                evidence = read_records(output/'jobs'/cid)
                if len(evidence) != 4 or any(r.get('status') != 'PASS' for r in evidence):
                    base['status'] = 'ERROR'; base['reason'] = 'worker success lacks four passing checks'
            if base['status'] != 'PASS':
                stop = f"{cid}: {base['status']}"; base['reason'] = stop
        elif stop is None:
            stop = 'campaign resource budget exhausted'; base['reason'] = stop
        commit_record(output, index, base); rows.append(base)
        print(f"{index+1}/{len(selection['cases'])} {cid}: {base['status']}", flush=True)
    unchanged = source_identity() == env['source_sha256']
    passed = bool(rows) and all(r['status'] == 'PASS' for r in rows) and unchanged
    summary = dict(schema=SCHEMA, selected=len(rows), status_counts=dict(Counter(r['status'] for r in rows)),
                   all_selected_qualified=passed, coverage_target_met=not selection['deficits'],
                   source_unchanged=unchanged, deficits=selection['deficits'], performance_eligible=False,
                   efficient_backend_accepted=False, worker_resource_wall_seconds=sum(r['worker_resource_wall_seconds'] for r in rows))
    atomic_json(output/'summary.json', summary)
    atomic_json(output/'progress.json', dict(status='COMPLETE' if passed else 'FAILED', committed_records=len(rows)))
    seal(output)
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return qualify_case(read(args.worker), args.output)
    return 0 if run(args.output) else 2


if __name__ == '__main__':
    raise SystemExit(main())
