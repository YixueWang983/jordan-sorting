"""Read-only reconstruction of diagnostic records and cross-host comparison."""
import argparse
import json
import math
from pathlib import Path
import statistics

from common_input_protocol import digest
from input_suite_protocol import environment_equal
from input_suite_registry import load_suite
from platform_environment import power_binding, require_power_binding
from qualify_common_inputs import read
from stability_protocol import SCHEMA, BACKENDS, rules, select_cases, session_order
from validate_common_qualification_v2 import validate_job
from validate_input_suite_run import verify_manifest
from validate_matched_measurement import check_environment, check_job


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(path, *, historical=False):
    path = Path(path).resolve()
    verify_manifest(path)
    require(not (path / 'failure.json').exists(), 'failed diagnostic is not a complete comparison')
    cfg, env = read(path / 'config.json'), read(path / 'environment.json')
    suite = load_suite()
    require(cfg['schema'] == SCHEMA and cfg['purpose'] == 'host stability diagnostic only'
            and cfg['performance_eligible'] is False, 'diagnostic identity')
    require(cfg['suite_sha256'] == suite['suite_sha256'] and cfg['rules'] == rules(), 'diagnostic input/rules')
    require(type(cfg['sessions']) is int and 3 <= cfg['sessions'] <= 10, 'diagnostic session count')
    require(type(cfg['budget_seconds']) in (int, float) and math.isfinite(cfg['budget_seconds'])
            and 0 < cfg['budget_seconds'] <= 3600 and cfg['input_seconds'] == 180, 'diagnostic budgets')
    entries = select_cases(suite, cfg['requested_case_ids'])
    require(cfg['case_ids'] == [e['case_id'] for e in entries], 'diagnostic panel selection')
    check_environment(env, uninstrumented=True, historical=historical)
    after = read(path / 'environment_after.json')
    check_environment(after, uninstrumented=True, historical=historical)
    environment_equal(env['execution'], after['execution'])
    done = read(path / 'completion.json')
    require(done['complete'] is True and done['performance_eligible'] is False and
            type(done['elapsed_seconds']) in (int,float) and
            0 <= done['elapsed_seconds'] <= cfg['budget_seconds'], 'diagnostic completion/budget')
    from input_suite_protocol import stamp
    require(stamp(env['execution']['captured_at']) <= stamp(cfg['started_utc']) <=
            stamp(after['execution']['captured_at']) <= stamp(done['finished_utc']), 'diagnostic chronology')
    binding = power_binding(env['execution']['hardware'])
    labels, batches, stats = set(), {}, {e['case_id']: {b:[] for b in BACKENDS} for e in entries}

    def inspect(label, entry, phase, job):
        labels.add(label)
        request = read(path / 'requests' / (label + '.json'))
        wanted = dict(schema=SCHEMA, phase=phase, entry=entry,
                      source_sha256=env['execution']['source_sha256'], power_binding=binding, job=job)
        require(request == wanted, 'diagnostic worker request binding: ' + label)
        folder = path / 'jobs' / label
        require(not (folder / 'failure.json').exists(), 'failed diagnostic job')
        if phase == 'qualification':
            p = read(folder / 'power.json')
            require(set(p) == {'before', 'after'}, 'qualification power checkpoints')
            for observation in p.values():
                require_power_binding(observation, binding)
            return validate_job(folder, job, entry['input_sha256'], passing=True)
        return check_job(folder, job, passing=True, verify_summary=False)

    def measurement(entry, index, stage, batch):
        return dict(stage=stage, index=index, rules=rules(),
                    case=dict(case=entry['case_id'], values=entry['values'], input_sha256=entry['input_sha256']),
                    batch_size=batch, configuration='uninstrumented',
                    gc_thresholds=env['execution']['gc_thresholds'], power_binding=binding)

    for i, entry in enumerate(entries):
        inspect('q-' + entry['case_id'], entry, 'qualification',
                dict(case=entry['case_id'], values=entry['values'],
                     backends=list(BACKENDS if i % 2 == 0 else BACKENDS[::-1])))
        result = inspect('c-' + entry['case_id'], entry, 'calibration', measurement(entry, i, 'calibration', None))
        batches[entry['case_id']] = result['result']['chosen_batch']
    require(read(path / 'batch_sizes.json') == batches, 'diagnostic common B reconstruction')
    for session in range(cfg['sessions']):
        for i, entry in enumerate(session_order(entries, session)):
            result = inspect(f's{session}-' + entry['case_id'], entry, 'stability',
                             measurement(entry, i, 'stability', batches[entry['case_id']]))
            for backend in BACKENDS:
                stats[entry['case_id']][backend].append(result['result']['groups'][backend])
    require({p.name for p in (path / 'jobs').iterdir()} == labels and
            {p.name for p in (path / 'requests').iterdir()} == {x+'.json' for x in labels}, 'diagnostic job inventory')
    expected_root = {'config.json','environment.json','environment_after.json','conditions.json',
                     'completion.json','batch_sizes.json','manifest.json','requests','jobs'}
    require({p.name for p in path.iterdir()} == expected_root, 'diagnostic root inventory')
    rows = []
    for entry in entries:
        for backend in BACKENDS:
            groups = stats[entry['case_id']][backend]
            medians = [g['median_ns_per_call'] for g in groups]
            relative = [g['iqr_ns_per_call'] / g['median_ns_per_call'] for g in groups]
            rows.append(dict(case_id=entry['case_id'], source=entry['source'], n=entry['n'], backend=backend,
                             batch_size=batches[entry['case_id']], sessions=groups,
                             median_ns_per_call=statistics.median(medians),
                             median_relative_iqr=statistics.median(relative),
                             relative_session_spread=(max(medians)-min(medians))/statistics.median(medians)))
    aggregate = {b:dict(median_relative_iqr=statistics.median(r['median_relative_iqr'] for r in rows if r['backend']==b),
                       median_relative_session_spread=statistics.median(r['relative_session_spread'] for r in rows if r['backend']==b))
                 for b in BACKENDS}
    return dict(schema=SCHEMA, complete=True, performance_eligible=False, archive=str(path),
                archive_manifest_sha256=digest(read(path/'manifest.json')), environment=env,
                suite_sha256=cfg['suite_sha256'], case_ids=cfg['case_ids'], rules=cfg['rules'],
                sessions=cfg['sessions'], conditions=read(path/'conditions.json'),
                paired_sample_batches=len(entries)*cfg['sessions']*20,
                total_sample_batches=len(entries)*cfg['sessions']*20*2,
                rows=rows, aggregate=aggregate)


def compare(left, right):
    for key in ('schema','suite_sha256','case_ids','rules','sessions'):
        require(left[key] == right[key], 'incomparable diagnostic: '+key)
    a,b = left['environment']['execution'],right['environment']['execution']
    require(a['source_sha256'] == b['source_sha256'], 'incomparable diagnostic source')
    require(a['python'].split()[0] == b['python'].split()[0] and a['gc_thresholds'] == b['gc_thresholds'],
            'incomparable Python/GC configuration')
    def ratio(x,y):
        return x/y if y else None
    right_rows = {(r['case_id'],r['backend']):r for r in right['rows']}
    rows=[]
    for r in left['rows']:
        s=right_rows[r['case_id'],r['backend']]
        rows.append(dict(case_id=r['case_id'],backend=r['backend'],
                         left_relative_iqr=r['median_relative_iqr'],right_relative_iqr=s['median_relative_iqr'],
                         left_session_spread=r['relative_session_spread'],right_session_spread=s['relative_session_spread'],
                         left_over_right_time=ratio(r['median_ns_per_call'],s['median_ns_per_call'])))
    aggregates={}
    for backend in BACKENDS:
        selected=[r for r in rows if r['backend']==backend]
        aggregates[backend]=dict(cases=len(selected),
            left_lower_within_case_variation=sum(r['left_relative_iqr']<r['right_relative_iqr'] for r in selected),
            left_lower_between_session_variation=sum(r['left_session_spread']<r['right_session_spread'] for r in selected),
            left=left['aggregate'][backend],right=right['aggregate'][backend])
    return dict(schema='host_stability_comparison_v1',performance_eligible=False,
                left_archive=left['archive'],right_archive=right['archive'],
                left_manifest=left['archive_manifest_sha256'],right_manifest=right['archive_manifest_sha256'],
                scope='descriptive host comparison; no pooled samples, no OS causality or significance claim',
                aggregate=aggregates,rows=rows)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive',type=Path)
    p.add_argument('--compare',type=Path)
    p.add_argument('--historical',action='store_true')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    result=validate(a.archive,historical=a.historical)
    if a.compare:
        result=compare(result,validate(a.compare,historical=a.historical))
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        # Reports are external to immutable measurement archives.
        if a.output.resolve().is_relative_to(a.archive.resolve()) or (a.compare and a.output.resolve().is_relative_to(a.compare.resolve())):
            raise ValueError('analysis output must be outside the measurement archives')
        with a.output.open('x',encoding='utf-8') as stream:
            stream.write(text)
    else:
        print(text)
