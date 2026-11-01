"""Bounded host comparison diagnostic; new immutable output directory per run."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments')]

from common_input_protocol import source_identity
from committed_records import atomic_json, run_bounded
from input_suite_registry import load_suite
from matched_measurement import capture_environment, execute_case
from platform_environment import power_binding, require_power_binding
from qualify_common_inputs import read, seal
from qualify_common_inputs_v2 import qualify_case
from stability_protocol import SCHEMA, BACKENDS, rules, select_cases, session_order
from uninstrumented_protocol import power_observation
from validate_common_qualification_v2 import validate_job
from validate_matched_measurement import check_environment, check_job


def worker(request, output):
    if request['schema'] != SCHEMA or request['source_sha256'] != source_identity():
        raise ValueError('diagnostic worker source/schema')
    entry = next((e for e in select_cases(load_suite(), [request['entry']['case_id']])), None)
    if entry != request['entry']:
        raise ValueError('diagnostic input changed')
    if request['phase'] == 'qualification':
        from oracle import oracle
        if oracle(entry['values'])['valid'] is not True:
            raise ValueError('invalid registered Jordan input')
        power = {'before': power_observation()}
        require_power_binding(power['before'], request['power_binding'])
        code = qualify_case(request['job'], output,
                            on_start=lambda: atomic_json(output / 'power.json', power))
        power['after'] = power_observation()
        atomic_json(output / 'power.json', power)
        require_power_binding(power['after'], request['power_binding'])
    else:
        if request['job']['stage'] not in ('calibration', 'stability') or request['job']['rules'] != rules():
            raise ValueError('diagnostic measurement rules')
        code = execute_case(request['job'], output)
    if source_identity() != request['source_sha256']:
        raise ValueError('source changed during diagnostic worker')
    return code


def run(output, *, case_ids=(), sessions=3, budget=900, conditions=None):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('use a new diagnostic output directory')
    if type(sessions) is not int or sessions < 3 or sessions > 10 or not 0 < budget <= 3600:
        raise ValueError('diagnostic needs 3..10 sessions and a finite budget <=3600 seconds')
    suite = load_suite()
    entries = select_cases(suite, case_ids)
    env = capture_environment(configuration='uninstrumented')
    check_environment(env, uninstrumented=True)
    cfg = dict(schema=SCHEMA, purpose='host stability diagnostic only', performance_eligible=False,
               suite_sha256=suite['suite_sha256'], case_ids=[e['case_id'] for e in entries],
               requested_case_ids=list(case_ids), sessions=sessions, rules=rules(),
               budget_seconds=budget, input_seconds=180, started_utc=datetime.now(timezone.utc).isoformat())
    output.mkdir(parents=True)
    atomic_json(output / 'config.json', cfg)
    atomic_json(output / 'environment.json', env)
    atomic_json(output / 'conditions.json', conditions or {'source':'not supplied', 'dedicated_host':None})
    (output / 'requests').mkdir()
    (output / 'jobs').mkdir()
    start = time.monotonic()
    binding = power_binding(env['execution']['hardware'])
    batches = {}

    def dispatch(label, entry, phase, job):
        remaining = budget - (time.monotonic() - start)
        if remaining <= 0:
            raise TimeoutError('diagnostic campaign budget exhausted')
        req = dict(schema=SCHEMA, phase=phase, entry=entry,
                   source_sha256=env['execution']['source_sha256'], power_binding=binding, job=job)
        path = output / 'requests' / (label + '.json')
        atomic_json(path, req)
        folder = output / 'jobs' / label
        code = run_bounded([sys.executable, '-B', str(Path(__file__).resolve()), '--worker', str(path),
                            '--output', str(folder)], folder, min(180, remaining))
        if code:
            raise RuntimeError('diagnostic job failed: ' + label)
        if phase == 'qualification':
            result = validate_job(folder, job, entry['input_sha256'], passing=True)
        else:
            result = check_job(folder, job, passing=True, verify_summary=False)
        print(label + ': PASS', flush=True)
        return result

    def measurement(entry, index, stage, batch):
        return dict(stage=stage, index=index, rules=cfg['rules'],
                    case={k:entry[v] for k,v in (('case','case_id'),('values','values'),('input_sha256','input_sha256'))},
                    batch_size=batch, configuration='uninstrumented',
                    gc_thresholds=env['execution']['gc_thresholds'], power_binding=binding)

    try:
        for i, entry in enumerate(entries):
            dispatch('q-' + entry['case_id'], entry, 'qualification',
                     dict(case=entry['case_id'], values=entry['values'],
                          backends=list(BACKENDS if i % 2 == 0 else BACKENDS[::-1])))
        for i, entry in enumerate(entries):
            result = dispatch('c-' + entry['case_id'], entry, 'calibration', measurement(entry, i, 'calibration', None))
            batches[entry['case_id']] = result['result']['chosen_batch']
        atomic_json(output / 'batch_sizes.json', batches)
        for session in range(sessions):
            for i, entry in enumerate(session_order(entries, session)):
                dispatch(f's{session}-' + entry['case_id'], entry, 'stability',
                         measurement(entry, i, 'stability', batches[entry['case_id']]))
        after = capture_environment(configuration='uninstrumented')
        from input_suite_protocol import environment_equal
        environment_equal(env['execution'], after['execution'])
        if time.monotonic() - start > budget:
            raise TimeoutError('diagnostic campaign budget exhausted')
        atomic_json(output / 'environment_after.json', after)
        atomic_json(output / 'completion.json', dict(complete=True, performance_eligible=False,
                    elapsed_seconds=time.monotonic()-start, finished_utc=datetime.now(timezone.utc).isoformat()))
    except Exception as exc:
        atomic_json(output / 'failure.json', dict(complete=False, performance_eligible=False,
                    error_type=type(exc).__name__, error=str(exc), elapsed_seconds=time.monotonic()-start))
        seal(output)
        raise
    seal(output)
    from validate_host_stability import validate
    return validate(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--case-id', action='append', default=[])
    p.add_argument('--sessions', type=int, default=3)
    p.add_argument('--budget', type=int, default=900)
    p.add_argument('--conditions', type=Path)
    p.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.worker:
        raise SystemExit(worker(read(a.worker), a.output))
    report = run(a.output, case_ids=a.case_id, sessions=a.sessions, budget=a.budget,
                 conditions=read(a.conditions) if a.conditions else None)
    print(json.dumps(report, indent=2))
