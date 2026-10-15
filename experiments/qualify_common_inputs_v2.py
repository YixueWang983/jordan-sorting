"""Full frozen common qualification using explicit synchronous v2 routing."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification v2 requires optimization level 0')
import argparse
from collections import Counter
from pathlib import Path
import time
from unittest.mock import patch
from common_input_protocol import BACKENDS, digest, source_identity, measurement_protocol
from common_qualification_v2_protocol import SCHEMA, QUALIFICATION_SCHEMA, MODES, frozen_selection, plan
from committed_records import atomic_json, canonical, commit_record, read_records, run_bounded
from qualify_common_inputs import environment, read, seal
from matched_backend_fixture import backend_spec, identity, capture_output, error_details
from paper_jordan_validation import run_synchronous_qualification
from paper_jordan_sort import paper_jordan_sort_valid
from validate_qualification_refactor import fingerprint
import paper_jordan as core


def evaluate(values, name, mode, output, action):
    """Audit instrumentation only; external expectations never enter the core."""
    source = list(values); prefixes = []; initializations = []
    initialize = core._initialize_paper_jordan_state_values
    policy = 'checked' if mode == 'synchronous_v2' else 'minimal'
    def counted_init(*args, **kwargs):
        state = initialize(*args, **kwargs)
        if (canonical(state.backend_identity) != canonical(identity(name))
                or state.execution_policy.name != policy):
            raise ValueError('actual initialization backend/config/policy mismatch')
        initializations.append(dict(backend_identity=identity(name), policy=policy))
        return state
    def observe(state, views):
        k = state.processed_count
        observed = capture_output(state.partial_order.to_list())
        if (type(k) is not int or k != len(prefixes)+3
                or observed['output'] != sorted(values[:k])):
            raise ValueError('external prefix output or schedule mismatch')
        prefixes.append(dict(prefix=k, output_sha256=digest(observed['output']),
                             state_sha256=fingerprint(state, views)))
        atomic_json(output/'progress.json', dict(status='RUNNING', **action, last_completed_prefix=k))
    report = None; final = None
    with patch.object(core, '_initialize_paper_jordan_state_values', counted_init):
        if mode == 'synchronous_v2':
            state, report = run_synchronous_qualification(source, backend=backend_spec(name), prefix_callback=observe)
            if (type(report) is not dict or report.get('schema') != QUALIFICATION_SCHEMA
                    or any(type(report.get(k)) is not int or report[k] != v for k,v in
                           dict(prefix_comparisons=len(values)-2, fresh_final_replays=1, initialized_instances=3).items())
                    or report.get('same_backend_same_config') is not True or report.get('performance_eligible') is not False
                    or len(prefixes) != len(values)-2 or len(initializations) != 3
                    or type(state.processed_count) is not int or state.processed_count != len(values)):
                raise ValueError('incomplete synchronous coverage')
            result = state.partial_order.to_list()
            final = dict(processed_count=state.processed_count, metrics=dict(state.metrics), trace=state.trace)
        elif mode == 'fresh_minimal':
            result = paper_jordan_sort_valid(source, 'minimal', backend=backend_spec(name))
            if len(initializations) != 1:
                raise ValueError('fresh minimal must initialize once')
        else:
            raise ValueError('unknown qualification mode')
    captured = capture_output(result)
    if source != values:
        raise ValueError('input mutation')
    return dict(**captured, prefixes=prefixes, report=report, initializations=initializations, final=final)


def qualify_case(request, output):
    output.mkdir(parents=True, exist_ok=False)
    index = 0
    for name in request['backends']:
        for mode in MODES:
            action = dict(case=request['case'], backend=name, mode=mode)
            atomic_json(output/'progress.json', dict(status='RUNNING', **action))
            base = dict(**action, input_sha256=digest(request['values']), backend_identity=identity(name), status='PASS', error=None)
            row = dict(base)
            try:
                row.update(evaluate(request['values'], name, mode, output, action))
                if row.get('output') != sorted(request['values']):
                    raise ValueError('external final output mismatch')
            except Exception as exc:
                row.update(status='ERROR', error=error_details(exc))
            try:
                canonical(row)
            except (TypeError, ValueError, OverflowError, RecursionError) as exc:
                row = {**base, 'status':'ERROR', 'error':error_details(exc, 'SerializationError')}
            commit_record(output, index, row); index += 1
            if row['status'] != 'PASS':
                return 2
    atomic_json(output/'progress.json', dict(status='COMPLETE', committed_records=index))
    return 0


def run(output):
    cfg = plan(); selection = frozen_selection(); env = environment()
    if env['dirty']:
        raise RuntimeError('freeze source and rules before full qualification')
    output.mkdir(parents=True, exist_ok=False)
    for filename, value in (('plan',cfg), ('selected',selection), ('environment',env), ('measurement_protocol',measurement_protocol())):
        atomic_json(output/f'{filename}.json', value)
    (output/'requests').mkdir(); (output/'jobs').mkdir()
    rows = []; stop = None; deadline = time.monotonic()+cfg['campaign_seconds']
    for index, case in enumerate(selection['cases']):
        cid = case['spec']['case']; order = list(BACKENDS if index%2 == 0 else BACKENDS[::-1])
        request = dict(schema=SCHEMA, case=cid, values=case['values'], backends=order)
        path = output/'requests'/f'{cid}.json'; atomic_json(path, request)
        remaining = deadline-time.monotonic(); budget = max(0, min(cfg['case_seconds'], remaining))
        row = dict(case=cid, input_sha256=case['input_sha256'], backends=order, budget_seconds=budget,
                   worker_resource_wall_seconds=0, status='NOT_RUN', reason=stop)
        if stop is None and remaining > 0:
            job = output/'jobs'/cid
            atomic_json(output/'progress.json', dict(status='RUNNING', case=cid, index=index))
            tick = time.monotonic()
            code = run_bounded([sys.executable, str(Path(__file__).resolve()), '--worker', str(path), '--output', str(job)], job, budget)
            row['worker_resource_wall_seconds'] = time.monotonic()-tick
            if code == 0:
                # A successful process exit alone is not evidence of coverage.
                try:
                    from validate_common_qualification_v2 import validate_job
                    validate_job(job, request, case['input_sha256'], passing=True)
                except (ValueError, KeyError, TypeError, OSError) as exc:
                    code = 2
                    atomic_json(job/'failure.json', dict(status='INCOMPLETE_WORKER_RECORDS', accepted=False,
                        error=error_details(exc), committed_records=len(read_records(job)), performance_eligible=False))
            row['status'] = 'PASS' if code == 0 else ('TIMEOUT' if read(job/'failure.json')['status'] == 'RESOURCE_TIMEOUT' else 'ERROR')
            if code:
                stop = f"{cid}: {row['status']}"; row['reason'] = stop
        elif stop is None:
            stop = 'campaign resource budget exhausted'; row['reason'] = stop
        commit_record(output, index, row); rows.append(row)
        print(f"{index+1}/{len(selection['cases'])} {cid}: {row['status']}", flush=True)
    unchanged = source_identity() == env['source_sha256']
    passed = bool(rows) and all(r['status'] == 'PASS' for r in rows) and unchanged
    atomic_json(output/'summary.json', dict(schema=SCHEMA, selected=len(rows), status_counts=dict(Counter(r['status'] for r in rows)),
        all_selected_qualified=passed, selection_sha256=selection['selection_sha256'], source_unchanged=unchanged,
        performance_eligible=False, efficient_backend_accepted=False,
        worker_resource_wall_seconds=sum(r['worker_resource_wall_seconds'] for r in rows)))
    atomic_json(output/'progress.json', dict(status='COMPLETE' if passed else 'FAILED', committed_records=len(rows)))
    seal(output)
    return passed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True); parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        request = read(args.worker)
        if request.get('schema') != SCHEMA or sorted(request['backends']) != sorted(BACKENDS):
            raise ValueError('wrong worker schema/backend set')
        raise SystemExit(qualify_case(request, args.output))
    raise SystemExit(0 if run(args.output) else 2)
