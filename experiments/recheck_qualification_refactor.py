"""Rebuild bounded v2 development comparisons; no algorithm/performance gate."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification refinement requires optimization level 0')
import argparse
from collections import Counter
import hashlib
import json
import math
import re
from datetime import datetime,timedelta
from pathlib import Path
from common_input_protocol import source_identity, BACKENDS
from committed_records import canonical,read_records
from matched_backend_fixture import identity
from validate_qualification_refactor import plan


def require(condition,message):
    if not condition: raise ValueError(message)


def read(path): return json.loads(path.read_text())


def recheck(output):
    output=Path(output); cfg=read(output/'plan.json'); require(canonical(cfg)==canonical(plan()),'frozen plan')
    env=read(output/'environment.json')
    require(type(env) is dict and set(env)=={'head','dirty','source_sha256','captured_at','python','executable','platform','machine',
            'hardware','python_optimize','gc_enabled','gc_thresholds','purpose'},'environment fields')
    require(type(env['head']) is str and re.fullmatch('[0-9a-f]{40}',env['head']),'commit')
    require(all(type(env[k]) is str and env[k].strip() for k in ('python','executable','platform','machine','captured_at')),'environment text')
    stamp=datetime.fromisoformat(env['captured_at']);require(stamp.tzinfo is not None and stamp.utcoffset()==timedelta(0),'UTC timestamp')
    require(env['gc_enabled'] is True and type(env['gc_thresholds']) is list and len(env['gc_thresholds'])==3
            and all(type(x) is int and x>=0 for x in env['gc_thresholds']),'GC')
    hardware=env['hardware'];require(type(hardware) is dict and hardware and all(type(k) is str and type(v) is str and v.strip() for k,v in hardware.items()),'hardware')
    if env['platform'].startswith('macOS'):
        require(set(hardware)=={'machdep.cpu.brand_string','hw.physicalcpu','hw.logicalcpu','hw.memsize','power'},'hardware keys')
        require(all(hardware[k].isdigit() and int(hardware[k])>0 for k in ('hw.physicalcpu','hw.logicalcpu','hw.memsize')),'hardware values')
    require(env['purpose']=='qualification resource observations only','purpose')
    require(env['dirty'] is False and env['source_sha256']==source_identity(),'source binding')
    require(type(env['python_optimize']) is int and env['python_optimize']==0,'optimization')
    statuses=read_records(output); require(len(statuses)==len(cfg['cases']),'case statuses')
    total=Counter(); comparisons=0; profiles=[]; passed=True
    files={'plan.json','environment.json','summary.json'}
    for i,(case,status) in enumerate(zip(cfg['cases'],statuses)):
        cid=case['case']; require(set(status)=={'case','status','reason','budget_seconds'} and status['case']==cid,'case order/fields')
        require(type(status['budget_seconds']) in (int,float) and math.isfinite(status['budget_seconds']) and 0<=status['budget_seconds']<=cfg['case_seconds'],'budget')
        files|={f'records/{i:06d}.json.gz',f'requests/{cid}.json'}
        require(canonical(read(output/'requests'/f'{cid}.json'))==canonical(case),'request')
        if status['status']=='NOT_RUN':
            require(not passed or status['reason']=='campaign resource budget exhausted','unexpected not run')
            passed=False; continue
        require(passed,'continued after failed case')
        require(status['status'] in ('PASS','FAILED'),'case status')
        job=output/'jobs'/cid; rows=read_records(job)
        expected=[(name,mode) for name in BACKENDS for mode in
                  (('reference','synchronous_v2','fresh_minimal') if case['compare_reference'] else ('synchronous_v2','fresh_minimal'))]
        if status['status']=='FAILED':
            require((job/'failure.json').is_file(),'missing failure')
            require(read(job/'failure.json')['accepted'] is False,'failed case accepted')
            passed=False
        else: require(len(rows)==len(expected),'missing versions')
        require(len(rows)<=len(expected),'extra versions')
        old={}
        for j,row in enumerate(rows):
            name,mode=expected[j]
            require(row['case']==cid and row['backend']==name and row['mode']==mode,'row order')
            require(row['input_sha256']==case['input_sha256'] and canonical(row['backend_identity'])==canonical(identity(name)),'row binding')
            if row['status']=='ERROR':
                require(not passed and j==len(rows)-1 and type(row['error']) is dict,'unhandled error');continue
            require(row['status']=='PASS' and row['error'] is None,'row status')
            require(type(row['output']) is list and all(type(x) is int for x in row['output'])
                    and row['output']==sorted(case['values']) and row['output_diagnostic'] is None,'external output')
            require(type(row['resource_wall_seconds']) in (int,float) and math.isfinite(row['resource_wall_seconds']) and row['resource_wall_seconds']>=0,'resource observation')
            require(set(row['counts'])=={'tree_audit_calls','initializations'} and all(type(v) is int and v>=0 for v in row['counts'].values()),'work counts')
            require(type(row['history_work']) is dict and all(type(v) is int and v>=0 for v in row['history_work'].values()),'history counts')
            n=case['n']; t=n-2
            if mode=='fresh_minimal':
                require(row['prefixes']==[] and row['final'] is None and row['counts']['initializations']==1,'fresh minimal')
            else:
                require([p['prefix'] for p in row['prefixes']]==list(range(3,n+1)) and all(type(p['prefix']) is int for p in row['prefixes']),'prefix coverage')
                require(all(type(p['state_sha256']) is str and re.fullmatch('[0-9a-f]{64}',p['state_sha256']) for p in row['prefixes']),'state hashes')
                require(type(row['final']['metrics']['invariant_checks']) is int and row['final']['metrics']['invariant_checks']==t,'audit metric')
                if mode=='reference':
                    require(row['counts']['initializations']==t+1,'reference constructors')
                    require(row['history_work']['reference_filter_visits']==sum(3*k*(k-3) for k in range(3,n+1)),'reference history work')
                    old[name]=row
                else:
                    report=row['report']
                    require(all(type(report[k]) is int for k in ('prefix_comparisons','fresh_final_replays','initialized_instances')),'schedule count types')
                    require(report['same_backend_same_config'] is True,'same backend/config')
                    require(report['schema']==cfg['qualification_schema'] and report['prefix_comparisons']==t
                            and report['fresh_final_replays']==1 and report['initialized_instances']==3
                            and row['counts']['initializations']==3 and report['performance_eligible'] is False,'v2 schedule')
                    require(row['history_work']==report['history_work'] and row['history_work']['linked_points']==2*sum(range(3,n+1))+2*n,'linear neighbor construction')
                    require(row['history_work']['removed_points']==2*sum(range(n-2))+2*(n-3),'reverse removals')
                    if case['compare_reference']:
                        require(row['prefixes']==old[name]['prefixes'] and row['final']==old[name]['final'],'old/new state mismatch')
                        comparisons+=t
            if name=='heterogeneous_finger' and case['shape']=='flat':
                expected_audits=(t*(t+1)//2+4*t if mode=='reference' else 5*t+2 if mode=='synchronous_v2' else 0)
                require(row['counts']['tree_audit_calls']==expected_audits,'flat audit schedule')
            total[mode]+=1
            profiles.append(dict(case=cid,backend=name,mode=mode,counts=row['counts'],history_work=row['history_work'],resource_wall_seconds=row['resource_wall_seconds']))
        if passed: require(read(job/'progress.json')==dict(status='COMPLETE',records=len(rows)),'completion cursor')
        # Failed jobs may contain ignored partials/current progress, never passing rows.
        job_files={str(p.relative_to(output)) for p in job.rglob('*') if p.is_file()}
        if passed:
            require(job_files=={f'jobs/{cid}/progress.json'}|{f'jobs/{cid}/records/{j:06d}.json.gz' for j in range(len(rows))},'unexpected worker file')
        files|=job_files
    expected_summary=dict(completed=passed,source_unchanged=True,cases=len(statuses),
                          passed=sum(r['status']=='PASS' for r in statuses),performance_eligible=False,
                          full_140_qualified=False,efficient_backend_accepted=False)
    require(canonical(read(output/'summary.json'))==canonical(expected_summary),'summary')
    manifest=read(output/'manifest.json'); require(set(manifest)==files,'manifest inventory')
    dirs={str(p) for f in files for p in Path(f).parents if str(p)!='.'}|{'jobs','requests'}
    require({str(p.relative_to(output)) for p in output.rglob('*')}==files|dirs|{'manifest.json'},'extra path')
    require(not any(p.is_symlink() for p in output.rglob('*')),'symlink')
    require(all(hashlib.sha256((output/f).read_bytes()).hexdigest()==h for f,h in manifest.items()),'manifest hashes')
    return dict(archive_valid=True,completed=passed,cases=len(statuses),runs=dict(total),
                old_new_prefix_comparisons=comparisons,performance_eligible=False,full_140_qualified=False,
                efficient_backend_accepted=False,profiles=profiles)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    report=recheck(parser.parse_args().directory);print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['completed'] else 2)
