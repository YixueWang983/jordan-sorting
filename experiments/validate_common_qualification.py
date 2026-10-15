"""Rebuild selection/qualification from raw records; never certify performance."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification validation requires optimization level 0')
import argparse
from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
from common_input_protocol import (SCHEMA, SIZES, CATEGORIES, TARGETS, BACKENDS,
    qualification_plan, measurement_protocol, candidate_specs, generate, source_identity, digest)
from committed_records import read_records, canonical
from matched_backend_fixture import identity
from oracle import oracle
from stats import structure_profile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def validate(output):
    output = Path(output)
    require(canonical(read(output/'plan.json')) == canonical(qualification_plan()), 'selection/budget rules')
    require(canonical(read(output/'measurement_protocol.json')) == canonical(measurement_protocol()), 'measurement rules')
    env = read(output/'environment.json')
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
    # Deterministically regenerate ONLY candidates whose cells are not full.
    # No runner selection/summarization or backend is invoked by this checker.
    candidates = read_records(output/'selection')
    counts = Counter(); seen = {}; selected = []; cursor = 0
    for spec in candidate_specs():
        cell = (spec['n'], spec['requested_category'])
        if counts[cell] == TARGETS[cell[1]]:
            continue
        require(cursor < len(candidates), 'missing candidate record')
        row = candidates[cursor]; cursor += 1
        values = generate(spec); cert = oracle(values); profile = structure_profile(values, oracle_result=cert)
        require(sorted(values) == list(range(1, spec['n']+1)), 'noncanonical input')
        key = digest(values)
        status = ('INVALID' if cert['valid'] is not True else
                  'CATEGORY_MISMATCH' if profile['category'] != cell[1] else
                  'DUPLICATE' if key in seen else 'SELECTED')
        expected = dict(spec=spec, values=values, input_sha256=key, rank_sha256=key, status=status,
                        duplicate_of=seen.get(key), profile=profile,
                        oracle={k:v for k,v in cert.items() if k != 'sorted'})
        require(canonical(row) == canonical(expected), 'candidate content/order/classification')
        if status == 'SELECTED':
            seen[key] = spec['case']; counts[cell] += 1; selected.append(row)
    require(cursor == len(candidates), 'extra candidate records')
    selected.sort(key=lambda r:(-r['spec']['n'], CATEGORIES.index(r['spec']['requested_category']),
                                r['spec']['candidate_index'], r['spec']['mirror']))
    deficits = [dict(n=n, category=c, target=TARGETS[c], selected=counts[n,c])
                for n in SIZES for c in CATEGORIES if counts[n,c] != TARGETS[c]]
    require(canonical(read(output/'selected.json')) == canonical(dict(
        cases=selected, selection_sha256=digest(selected), deficits=deficits)), 'selected input set/hash')
    require(read(output/'selection/progress.json') == dict(status='COMPLETE', selected=len(selected)), 'selection cursor')
    rows = read_records(output); require(len(rows) == len(selected), 'missing qualification statuses')
    expected_files = {'plan.json','measurement_protocol.json','environment.json','selected.json','summary.json','progress.json',
                      'selection/progress.json'}
    expected_files |= {f'selection/records/{i:06d}.json.gz' for i in range(len(candidates))}
    stopped = False; runs = 0; prefixes = Counter(); splits = Counter(); nonempty = Counter()
    for i, (case, row) in enumerate(zip(selected, rows)):
        cid = case['spec']['case']; values = case['values']
        order = list(BACKENDS if i%2 == 0 else BACKENDS[::-1])
        request = dict(case=cid, values=values, backends=order)
        require(canonical(read(output/'requests'/f'{cid}.json')) == canonical(request), 'worker request')
        expected_files |= {f'requests/{cid}.json', f'records/{i:06d}.json.gz'}
        require(type(row) is dict and set(row) == {'case','input_sha256','backends','budget_seconds','worker_resource_wall_seconds','status','reason'}, 'qualification fields')
        require(row['case'] == cid and row['input_sha256'] == case['input_sha256'] and row['backends'] == order, 'qualification identity')
        require(number(row['budget_seconds']) and row['budget_seconds'] <= 180
                and number(row['worker_resource_wall_seconds']), 'resource values')
        if row['status'] == 'NOT_RUN':
            require(type(row['reason']) is str and bool(row['reason']) and row['worker_resource_wall_seconds'] == 0, 'not-run reason')
            stopped = True; continue
        require(not stopped, 'continued after failure')
        require(row['status'] in ('PASS','ERROR','TIMEOUT') and row['budget_seconds'] > 0, 'worker status')
        job = output/'jobs'/cid; evidence = read_records(job)
        expected_files |= {f'jobs/{cid}/progress.json'}
        expected_files |= {f'jobs/{cid}/records/{j:06d}.json.gz' for j in range(len(evidence))}
        schedule = [(name, mode) for name in order for mode in ('checked','minimal')]
        require(len(evidence) <= 4, 'extra worker rows')
        if row['status'] != 'PASS':
            stopped = True
            require(type(row['reason']) is str and bool(row['reason']), 'failure reason')
            require((job/'failure.json').is_file(), 'missing durable failure')
            fail = read(job/'failure.json')
            require(fail.get('accepted') is False, 'failed worker accepted')
            expected_files.add(f'jobs/{cid}/failure.json')
        else:
            require(row['reason'] is None and len(evidence) == 4, 'passing case missing checks')
            require(read(job/'progress.json') == dict(status='COMPLETE', committed_records=4), 'worker cursor')
        for j, record in enumerate(evidence):
            name, mode = schedule[j]
            require(record.get('case') == cid and record.get('backend') == name and record.get('mode') == mode, 'worker order')
            require(record.get('input_sha256') == case['input_sha256']
                    and canonical(record.get('backend_identity')) == canonical(identity(name)), 'worker binding')
            if record.get('status') == 'ERROR':
                require(row['status'] != 'PASS' and j == len(evidence)-1 and type(record.get('error')) is dict, 'unhandled error')
                continue
            require(record.get('status') == 'PASS' and record.get('error') is None, 'worker check status')
            common = {'case','backend','mode','input_sha256','backend_identity','status','error','output','output_diagnostic'}
            require(set(record) == common | ({'processed_count','invariants_valid','same_backend_replay','replay_prefixes','metrics','trace'} if mode == 'checked' else set()), 'worker fields')
            require(type(record['output']) is list and all(type(x) is int for x in record['output'])
                    and record['output'] == sorted(values) and record['output_diagnostic'] is None, 'external output')
            runs += 1
            if mode == 'checked':
                require(type(record['processed_count']) is int and record['processed_count'] == len(values), 'processed count')
                require(record['invariants_valid'] is True and record['same_backend_replay'] is True, 'checked audit/replay')
                require(type(record['replay_prefixes']) is int and record['replay_prefixes'] == len(values)-2, 'replay count')
                require(type(record['metrics']) is dict and all(type(v) is int and v >= 0 for v in record['metrics'].values()), 'metrics')
                require(type(record['trace']) is list and all(type(e) is dict for e in record['trace']), 'trace')
                prefixes[name] += record['replay_prefixes']
                events = [e for e in record['trace'] if e.get('step') == 'step3b_split_sibling_list' and e.get('performed') is True]
                splits[name] += len(events); nonempty[name] += sum(e['left_size'] > 0 and e['right_size'] > 0 for e in events)
    passed = bool(rows) and all(r['status'] == 'PASS' for r in rows)
    summary = dict(schema=SCHEMA, selected=len(rows), status_counts=dict(Counter(r['status'] for r in rows)),
                   all_selected_qualified=passed, coverage_target_met=not deficits, source_unchanged=True,
                   deficits=deficits, performance_eligible=False, efficient_backend_accepted=False,
                   worker_resource_wall_seconds=sum(r['worker_resource_wall_seconds'] for r in rows))
    require(canonical(read(output/'summary.json')) == canonical(summary), 'summary reconstruction')
    require(read(output/'progress.json') == dict(status='COMPLETE' if passed else 'FAILED', committed_records=len(rows)), 'campaign cursor')
    manifest = read(output/'manifest.json')
    # Successful campaigns have an exact directory/file inventory. Interrupted
    # worker partials in failed campaigns are retained but never passing rows.
    partials = {str(p.relative_to(output)) for p in output.rglob('*.partial')} if not passed else set()
    expected_files |= partials
    require(type(manifest) is dict and set(manifest) == expected_files, 'manifest file inventory')
    dirs = {str(p) for name in expected_files for p in Path(name).parents if str(p) != '.'} | {'jobs','requests'}
    require({str(p.relative_to(output)) for p in output.rglob('*')} == expected_files | dirs | {'manifest.json'}, 'unexpected entry')
    require(not any(p.is_symlink() for p in output.rglob('*')), 'archive symlink')
    for name, sha in manifest.items():
        path = output/name
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == sha, 'manifest hash/type')
    return dict(archive_valid=True, all_selected_qualified=passed, coverage_target_met=not deficits,
                inputs=len(selected), public_executions=runs, per_backend_checked_prefixes=dict(prefixes),
                per_backend_splits=dict(splits), per_backend_nonempty_splits=dict(nonempty),
                performance_eligible=False, efficient_backend_accepted=False, source_head=env['head'],
                selection_sha256=digest(selected), deficits=deficits)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('directory', type=Path)
    report = validate(parser.parse_args().directory)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['all_selected_qualified'] else 2)
