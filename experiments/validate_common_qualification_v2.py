"""Independent reconstruction of v2 records, frozen inputs and acceptance.

No sorting, synchronous controller or runner evaluation is executed here.
Recorded state hashes are integrity identifiers, not independent state proofs.
"""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification v2 validation requires optimization level 0')
import argparse
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
from common_input_protocol import ROOT, BACKENDS, SIZES, CATEGORIES, TARGETS, digest, source_identity, measurement_protocol
from common_qualification_v2_protocol import SCHEMA, QUALIFICATION_SCHEMA, MODES, frozen_selection, plan
from committed_records import canonical, read_records
from matched_backend_fixture import identity
from validate_common_qualification import require, number
from oracle import oracle
from stats import structure_profile


def read(path):
    return json.loads(path.read_text())


def validate_revision(env):
    # Match the named commit to all bound source files, even when the current
    # checkout is a later results-only commit. Repacking cannot invent a head.
    result = subprocess.run(['git','ls-tree','-r',env['head'],'--','src','experiments','tests'],
                            cwd=ROOT, capture_output=True, text=True)
    require(result.returncode == 0, 'unknown producing revision')
    blobs = {}
    for line in result.stdout.splitlines():
        metadata, path = line.split('\t',1)
        mode, kind, sha = metadata.split()
        if len(Path(path).parts) == 2 and path.endswith('.py'):
            require(kind == 'blob' and mode in ('100644','100755'), 'source object type')
            blobs[path] = sha
    expected = {}
    for path in env['source_sha256']:
        data = (ROOT/path).read_bytes()
        expected[path] = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    require(blobs == expected, 'producing commit/source identity mismatch')


def validate_environment(env):
    fields = {'head','dirty','source_sha256','captured_at','python','executable','platform','machine',
              'hardware','python_optimize','gc_enabled','gc_thresholds','purpose'}
    require(type(env) is dict and set(env) == fields, 'environment fields')
    require(type(env['head']) is str and re.fullmatch('[0-9a-f]{40}', env['head']), 'source revision')
    require(env['dirty'] is False and env['source_sha256'] == source_identity(), 'source changed; use producing revision')
    require(type(env['python_optimize']) is int and env['python_optimize'] == 0, 'optimization flag')
    require(env['gc_enabled'] is True, 'GC disabled')
    require(type(env['gc_thresholds']) is list and len(env['gc_thresholds']) == 3
            and all(type(x) is int and x >= 0 for x in env['gc_thresholds']), 'GC thresholds')
    require(all(type(env[k]) is str and env[k].strip() for k in ('python','executable','platform','machine','captured_at')), 'environment text')
    stamp = datetime.fromisoformat(env['captured_at'])
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), 'UTC timestamp')
    require(type(env['hardware']) is dict and env['hardware']
            and all(type(k) is str and type(v) is str and v.strip() for k,v in env['hardware'].items()), 'hardware')
    if env['platform'].startswith('macOS'):
        require(set(env['hardware']) == {'machdep.cpu.brand_string','hw.physicalcpu','hw.logicalcpu','hw.memsize','power'}, 'hardware fields')
        require(all(env['hardware'][k].isdigit() and int(env['hardware'][k]) > 0
                    for k in ('hw.physicalcpu','hw.logicalcpu','hw.memsize')), 'hardware numeric values')
    require(env['purpose'] == 'qualification resource observations only', 'evidence purpose')
    validate_revision(env)


def validate_job(job, request, input_sha256, *, passing):
    """Validate a complete or committed-prefix worker archive; reject fake exits."""
    rows = read_records(job); values = request['values']; n = len(values); t = n-2
    schedule = [(name, mode) for name in request['backends'] for mode in MODES]
    require(len(rows) <= 4 and (not passing or len(rows) == 4), 'missing/extra mode checks')
    if passing:
        require(read(job/'progress.json') == dict(status='COMPLETE', committed_records=4), 'worker completion cursor')
    for j, row in enumerate(rows):
        name, mode = schedule[j]
        require(row.get('case') == request['case'] and row.get('backend') == name and row.get('mode') == mode, 'mode order')
        require(row.get('input_sha256') == input_sha256 and canonical(row.get('backend_identity')) == canonical(identity(name)), 'backend/input binding')
        if row.get('status') == 'ERROR':
            require(not passing and j == len(rows)-1 and type(row.get('error')) is dict
                    and type(row['error'].get('type')) is str and type(row['error'].get('message')) is str, 'error record')
            continue
        require(row.get('status') == 'PASS' and row.get('error') is None, 'mode status')
        require(set(row) == {'case','backend','mode','input_sha256','backend_identity','status','error',
            'output','output_diagnostic','prefixes','report','initializations','final'}, 'mode fields')
        require(type(row['output']) is list and all(type(x) is int for x in row['output'])
                and row['output'] == sorted(values) and row['output_diagnostic'] is None, 'external output')
        expected_initializations = [dict(backend_identity=identity(name), policy='checked' if mode == 'synchronous_v2' else 'minimal')]*(3 if mode == 'synchronous_v2' else 1)
        require(canonical(row['initializations']) == canonical(expected_initializations), 'actual initialization/config/policy')
        if mode == 'fresh_minimal':
            require(row['prefixes'] == [] and row['report'] is None and row['final'] is None, 'minimal scope')
            continue
        require(type(row['prefixes']) is list and len(row['prefixes']) == t, 'prefix count')
        for k, prefix in enumerate(row['prefixes'], 3):
            require(type(prefix) is dict and set(prefix) == {'prefix','output_sha256','state_sha256'}, 'prefix fields')
            require(type(prefix['prefix']) is int and prefix['prefix'] == k
                    and prefix['output_sha256'] == digest(sorted(values[:k])), 'prefix output/schedule')
            require(type(prefix['state_sha256']) is str and re.fullmatch('[0-9a-f]{64}',prefix['state_sha256']), 'state digest')
        report = row['report']
        removed = 2*sum(range(n-2))+2*(n-3)
        expected_report = dict(schema=QUALIFICATION_SCHEMA, prefix_comparisons=t, fresh_final_replays=1,
            initialized_instances=3, same_backend_same_config=True, performance_eligible=False,
            history_work=dict(linked_points=2*sum(range(3,n+1))+2*n, removed_points=removed,
                              boundary_predictions=2*removed, output_adjacency_predictions=removed))
        # Canonical equality also distinguishes booleans, floats and integers.
        require(canonical(report) == canonical(expected_report), 'v2 coverage/history counts')
        final = row['final']
        require(type(final) is dict and set(final) == {'processed_count','metrics','trace'}, 'final fields')
        require(type(final['processed_count']) is int and final['processed_count'] == n, 'processed count')
        metrics, trace = final['metrics'], final['trace']
        require(type(metrics) is dict and all(type(v) is int and v >= 0 for v in metrics.values()), 'metric types')
        require(metrics.get('invariant_checks') == t and metrics.get('output_insertions') == n-3, 'validation/output counts')
        require(type(trace) is list and len(trace) == 2+7*(n-3) and all(type(e) is dict for e in trace)
                and metrics.get('trace_event_count') == len(trace), 'trace coverage')
        events = [e for e in trace if e.get('step') == 'step3b_split_sibling_list']
        require([e.get('iteration') for e in events] == list(range(4,n+1))
                and all(type(e.get('iteration')) is int and type(e.get('performed')) is bool for e in events), 'split trace schedule')
        for event in events:
            require(all(type(event.get(k)) is int and event[k] >= 0 for k in ('input_size','left_size','right_size')), 'split sizes')
            require(event['left_size']+event['right_size'] == event['input_size'], 'split size conservation')
        require(metrics.get('sibling_list_splits') == sum(e['performed'] for e in events), 'split count')
    return rows


def validate(output):
    output = Path(output); cfg = plan()
    require(canonical(read(output/'plan.json')) == canonical(cfg), 'qualification rules')
    require(canonical(read(output/'measurement_protocol.json')) == canonical(measurement_protocol()), 'measurement rules')
    env = read(output/'environment.json'); validate_environment(env)
    selection = frozen_selection()
    require(canonical(read(output/'selected.json')) == canonical(selection), 'frozen input set')
    require(selection['selection_sha256'] == cfg['selection_sha256'] == digest(selection['cases']) and not selection['deficits'], 'selection hash/deficits')
    counts = Counter(); hashes = set()
    for case in selection['cases']:
        values = case['values']; spec = case['spec']; n = spec['n']
        require(all(type(v) is int for v in values) and sorted(values) == list(range(1,n+1)), 'canonical rank input')
        key = digest(values); require(key == case['input_sha256'] == case['rank_sha256'] and key not in hashes, 'input hash/uniqueness'); hashes.add(key)
        cert = oracle(values); profile = structure_profile(values, oracle_result=cert)
        require(cert['valid'] is True and profile['category'] == spec['requested_category'], 'input qualification/classification')
        require(canonical(case['profile']) == canonical(profile)
                and canonical(case['oracle']) == canonical({k:v for k,v in cert.items() if k != 'sorted'}), 'input evidence')
        counts[n,spec['requested_category']] += 1
    require(counts == Counter({(n,c):TARGETS[c] for n in SIZES for c in CATEGORIES}), 'coverage quotas')
    statuses = read_records(output); require(len(statuses) == len(selection['cases']), 'missing case statuses')
    files = {'plan.json','measurement_protocol.json','environment.json','selected.json','summary.json','progress.json'}
    stopped = False; runs = Counter(); prefixes = Counter(); splits = Counter(); nonempty = Counter(); constructors = Counter(); replays = Counter()
    for i, (case, row) in enumerate(zip(selection['cases'],statuses)):
        cid = case['spec']['case']; order = list(BACKENDS if i%2 == 0 else BACKENDS[::-1])
        request = dict(schema=SCHEMA, case=cid, values=case['values'], backends=order)
        require(canonical(read(output/'requests'/f'{cid}.json')) == canonical(request), 'request binding')
        files |= {f'requests/{cid}.json',f'records/{i:06d}.json.gz'}
        require(set(row) == {'case','input_sha256','backends','budget_seconds','worker_resource_wall_seconds','status','reason'}, 'case fields')
        require(row['case'] == cid and row['input_sha256'] == case['input_sha256'] and row['backends'] == order, 'case binding')
        require(number(row['budget_seconds']) and row['budget_seconds'] <= cfg['case_seconds']
                and number(row['worker_resource_wall_seconds']), 'case resource values')
        if row['status'] == 'NOT_RUN':
            require(type(row['reason']) is str and row['reason'] and row['worker_resource_wall_seconds'] == 0, 'not-run reason')
            require(stopped or row['reason'] == 'campaign resource budget exhausted', 'unexpected not run')
            stopped = True; continue
        require(not stopped and row['status'] in ('PASS','ERROR','TIMEOUT') and row['budget_seconds'] > 0, 'case status/order')
        passing = row['status'] == 'PASS'; job = output/'jobs'/cid
        records = validate_job(job, request, case['input_sha256'], passing=passing)
        files |= {f'jobs/{cid}/records/{j:06d}.json.gz' for j in range(len(records))}
        if (job/'progress.json').exists(): files.add(f'jobs/{cid}/progress.json')
        if passing:
            require(row['reason'] is None, 'pass reason')
        else:
            stopped = True
            require(type(row['reason']) is str and row['reason'], 'failure reason')
            failure = read(job/'failure.json'); files.add(f'jobs/{cid}/failure.json')
            require(failure.get('accepted') is False and failure.get('performance_eligible') is False, 'failure accepted')
            require(type(failure.get('committed_records')) is int and failure['committed_records'] == len(records), 'failure durable count')
            expected = ('RESOURCE_TIMEOUT',) if row['status'] == 'TIMEOUT' else ('WORKER_ERROR','INCOMPLETE_WORKER_RECORDS')
            require(failure.get('status') in expected, 'failure status')
            if row['status'] == 'TIMEOUT':
                require(number(failure.get('budget_seconds')) and failure['budget_seconds'] == row['budget_seconds'], 'timeout budget')
            if 'current' in failure:
                require(failure['current'] == (read(job/'progress.json') if (job/'progress.json').exists() else None), 'failure cursor')
            # Only uncommitted atomic files in this failed job are tolerated.
            files |= {str(p.relative_to(output)) for p in job.rglob('*.partial') if p.name.startswith('.')}
        for record in records:
            if record['status'] != 'PASS': continue
            name = record['backend']; runs[record['mode']] += 1
            constructors[name] += len(record['initializations'])
            if record['mode'] == 'synchronous_v2':
                prefixes[name] += record['report']['prefix_comparisons']; replays[name] += record['report']['fresh_final_replays']
                events = [e for e in record['final']['trace'] if e.get('step') == 'step3b_split_sibling_list' and e['performed']]
                splits[name] += len(events); nonempty[name] += sum(e['left_size'] > 0 and e['right_size'] > 0 for e in events)
    passed = bool(statuses) and all(r['status'] == 'PASS' for r in statuses)
    summary = dict(schema=SCHEMA, selected=len(statuses), status_counts=dict(Counter(r['status'] for r in statuses)),
        all_selected_qualified=passed, selection_sha256=selection['selection_sha256'], source_unchanged=True,
        performance_eligible=False, efficient_backend_accepted=False,
        worker_resource_wall_seconds=sum(r['worker_resource_wall_seconds'] for r in statuses))
    require(canonical(read(output/'summary.json')) == canonical(summary), 'summary reconstruction')
    require(read(output/'progress.json') == dict(status='COMPLETE' if passed else 'FAILED', committed_records=len(statuses)), 'campaign cursor')
    manifest = read(output/'manifest.json'); require(type(manifest) is dict and set(manifest) == files, 'manifest inventory')
    dirs = {str(p) for f in files for p in Path(f).parents if str(p) != '.'}|{'jobs','requests'}
    require({str(p.relative_to(output)) for p in output.rglob('*')} == files|dirs|{'manifest.json'}, 'extra entry')
    require(not any(p.is_symlink() for p in output.rglob('*')), 'symlink')
    for f, h in manifest.items():
        require((output/f).is_file() and hashlib.sha256((output/f).read_bytes()).hexdigest() == h, 'manifest hash/type')
    return dict(archive_valid=True, all_selected_qualified=passed, inputs=len(statuses), status_counts=summary['status_counts'],
        completed_modes=dict(runs), per_backend_synchronous_prefixes=dict(prefixes), per_backend_final_fresh_replays=dict(replays),
        per_backend_initializations=dict(constructors), per_backend_splits=dict(splits), per_backend_nonempty_splits=dict(nonempty),
        source_head=env['head'], selection_sha256=selection['selection_sha256'], performance_eligible=False, efficient_backend_accepted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('directory', type=Path)
    report = validate(parser.parse_args().directory); print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['all_selected_qualified'] else 2)
