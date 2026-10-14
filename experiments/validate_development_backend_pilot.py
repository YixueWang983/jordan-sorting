"""Independent raw-row reconstruction for the development pilot, not acceptance."""
import argparse
from datetime import datetime,timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Pilot validation requires optimization level 0')
from committed_records import canonical,read_records
from development_backend_pilot import SCHEMA,PROTOCOL,BACKENDS,inputs,identity,source_identity
from oracle import oracle


def require(condition,message):
    if not condition:raise ValueError(message)


def validate(directory):
    directory=Path(directory)
    config=json.loads((directory/'config.json').read_text())
    environment=json.loads((directory/'environment.json').read_text())
    expected={'schema':SCHEMA,'protocol':PROTOCOL,'inputs':inputs(),'backends':{n:identity(n) for n in BACKENDS}}
    require(canonical(config)==canonical(expected),'fixed pilot config/inputs/backend identity changed')
    envfields={'head','dirty','source_sha256','python','platform','captured_at','python_optimize',
               'measurement_kind','gc_enabled','clock'}
    require(type(environment) is dict and set(environment)==envfields,'environment fields')
    require(type(environment['head']) is str and re.fullmatch('[0-9a-f]{40}',environment['head']) is not None,'head')
    require(type(environment['dirty']) is bool,'dirty')
    require(all(type(environment[k]) is str and environment[k].strip() for k in ('python','platform','captured_at')),'environment text')
    stamp=datetime.fromisoformat(environment['captured_at'])
    require(stamp.tzinfo is not None and stamp.utcoffset()==timedelta(0),'timestamp must be UTC')
    require(type(environment['python_optimize']) is int and environment['python_optimize']==0,'optimized interpreter')
    require(environment['source_sha256']==source_identity(),'source differs; use producing source version')
    require(environment['measurement_kind']=='perf_counter_ns' and environment['gc_enabled'] is True,'clock/GC mode')
    clock=environment['clock']
    require(type(clock) is dict and set(clock)=={'implementation','resolution_seconds','monotonic','adjustable','successive_read_deltas_ns'},'clock fields')
    require(type(clock['implementation']) is str and bool(clock['implementation']),'clock implementation')
    require(type(clock['resolution_seconds']) in (int,float) and math.isfinite(clock['resolution_seconds']) and clock['resolution_seconds']>0,'clock resolution')
    require(clock['monotonic'] is True and type(clock['adjustable']) is bool,'clock properties')
    deltas=clock['successive_read_deltas_ns']
    require(type(deltas) is list and len(deltas)==1000 and all(type(t) is int and t>=0 for t in deltas) and any(deltas),'clock calibration')
    lookup={c['case']:c for c in config['inputs']}
    for case in lookup.values():
        require(len(set(case['values']))==len(case['values']) and oracle(case['values'])['valid'],'invalid pilot input')
    # Reconstruct schedule without runner.actions or runner.summarize.
    schedule=[]
    for cid in lookup:
        for backend in BACKENDS:schedule.append((cid,'preflight',backend,None,None))
    for index,cid in enumerate(lookup):
        for rep in range(2):
            for backend in (BACKENDS if (index+rep)%2==0 else BACKENDS[::-1]):
                schedule.append((cid,'warmup',backend,1,rep))
        for bidx,batch in enumerate((1,4,16)):
            for rep in range(3):
                for backend in (BACKENDS if (index+bidx+rep)%2==0 else BACKENDS[::-1]):
                    schedule.append((cid,'sample',backend,batch,rep))
    rows=read_records(directory)
    require(len(rows)<=len(schedule),'extra committed row')
    times={};failed=False;sample_calls=0
    for index,row in enumerate(rows):
        require(type(row) is dict,'row must be dictionary')
        require(canonical(tuple(row.get(k) for k in ('case','kind','backend','batch_size','round')))==canonical(schedule[index]),'row order/identity')
        cid,kind,name,batch,rep=schedule[index];case=lookup[cid]
        require(row.get('input_sha256')==case['sha256'] and canonical(row.get('backend_identity'))==canonical(identity(name)),'row input/backend binding')
        if row.get('status')=='ERROR':
            require(index==len(rows)-1,'continued after failed row')
            require(type(row.get('error')) is dict and type(row['error'].get('type')) is str and bool(row['error']['type']) and type(row['error'].get('message')) is str,'error detail')
            failed=True
            continue
        require(row.get('status')=='PASS' and row.get('error') is None,'invalid row status')
        common={'case','kind','backend','batch_size','round','input_sha256','backend_identity','status','error'}
        if kind=='preflight':
            require(set(row)==common|{'processed_count','same_backend_replay','output','output_diagnostic'},'preflight fields')
            require(type(row['processed_count']) is int and row['processed_count']==len(case['values']) and row['same_backend_replay'] is True,'preflight incomplete')
            captured=[{k:row[k] for k in ('output','output_diagnostic')}]
        else:
            require(set(row)==common|{'elapsed_ns','completed_calls','outputs'},'timed row fields')
            require(type(row['elapsed_ns']) is int and row['elapsed_ns']>0,'invalid measured duration')
            require(type(row['completed_calls']) is int and row['completed_calls']==batch,'missing batch calls')
            require(type(row['outputs']) is list and len(row['outputs'])==batch,'missing batch outputs')
            captured=row['outputs']
            if kind=='sample':
                times.setdefault((cid,name,batch),[]).append(row['elapsed_ns']);sample_calls+=batch
        for value in captured:
            require(type(value) is dict and set(value)=={'output','output_diagnostic'},'captured output fields')
            require(type(value['output']) is list and all(type(x) is int for x in value['output']) and value['output']==sorted(case['values']) and value['output_diagnostic'] is None,'external output mismatch')
    failure=(directory/'failure.json').exists()
    if failure or failed:
        require(failure,'failed row lacks failure record')
        evidence=json.loads((directory/'failure.json').read_text())
        require(evidence.get('accepted') is False,'failure marked accepted')
        return {'archive_complete':False,'completed_successfully':False,'committed_records_recovered':len(rows),
                'performance_eligible':False,'current':evidence.get('current'),'status':evidence.get('status')}
    require(len(rows)==len(schedule),'successful archive missing rows')
    groups=[]
    for cid in lookup:
        for name in BACKENDS:
            for batch in (1,4,16):
                values=times[cid,name,batch]
                require(len(values)==3,'missing/duplicated sample')
                groups.append({'case':cid,'backend':name,'batch_size':batch,'samples':len(values),
                               'min_batch_ns':min(values),'median_batch_ns':statistics.median(values),'max_batch_ns':max(values)})
    summary=json.loads((directory/'summary.json').read_text())
    expected_summary={'schema':SCHEMA,'completed_successfully':True,'source_unchanged':True,
        'performance_eligible':False,'rows':len(rows),'planned_rows':len(schedule),
        'sample_batches':144,'sample_calls':sample_calls,'groups':groups}
    require(canonical(summary)==canonical(expected_summary),'summary cannot be rebuilt')
    progress=json.loads((directory/'progress.json').read_text())
    require(progress=={'status':'COMPLETE','committed_records':len(rows)},'incomplete cursor')
    manifest=json.loads((directory/'manifest.json').read_text())
    expected_files={'config.json','environment.json','summary.json','progress.json'}|{f'records/{i:06d}.json.gz' for i in range(len(rows))}
    require(type(manifest) is dict and set(manifest)==expected_files,'manifest file set')
    entries={str(p.relative_to(directory)) for p in directory.rglob('*')}
    require(entries==expected_files|{'manifest.json','records'},'unexpected archive entry')
    require(all((directory/p).is_file() and not (directory/p).is_symlink() and hashlib.sha256((directory/p).read_bytes()).hexdigest()==h for p,h in manifest.items()),'archive file hash/type')
    require(not (directory/'records').is_symlink() and not (directory/'manifest.json').is_symlink(),'archive symlink')
    return {'archive_complete':True,'completed_successfully':True,'performance_eligible':False,
            'summary_rebuilt':True,'inputs':len(lookup),'rows':len(rows),'sample_batches':144,
            'sample_calls':sample_calls,'measurement_kind':'perf_counter_ns'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    print(json.dumps(validate(parser.parse_args().directory),indent=2))
