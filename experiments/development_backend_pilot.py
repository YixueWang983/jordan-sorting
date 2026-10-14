"""Budgeted real-clock development pilot, never formal performance acceptance."""
import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

if sys.flags.optimize != 0:
    raise RuntimeError('Pilot evidence requires optimization level 0')
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
from committed_records import atomic_json,commit_record,run_bounded,canonical
from matched_backend_fixture import backend_spec,identity,capture_output,error_details,output_diagnostic
from oracle import oracle
from paper_jordan_sort import paper_jordan_sort_valid,paper_jordan_diagnostics_valid
from validate_finger_middle_splits import values_for

SCHEMA='development_backend_pilot_v1'
BACKENDS=('ordinary_list','heterogeneous_finger')
PROTOCOL={'stage':'development_pilot','measurement_kind':'perf_counter_ns','performance_eligible':False,
          'execution_mode':'minimal','audit_execution_mode':'checked','tree_detailed_work':False,
          'warmups_per_backend':2,'batch_sizes':[1,4,16],'repetitions':3,'budget_seconds':180,
          'preflight':'all inputs and both backends before any warmup; final audit and same-backend replay',
          'boundary':'fresh public sort per call; initialization, algorithm, output recovery, batch loop and output-list append inside clock; expected comparisons and persistence outside',
          'gc':'enabled in measured calls; gc.collect before each batch outside clock',
          'order':'alternate first backend by case index plus batch-size index plus repetition',
          'failure':'stop at first detected error; batch outputs checked after timer; no retry, input deletion or replacement'}
SOURCE_FILES=tuple(sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').glob('*.py')))+(
    'experiments/committed_records.py','experiments/development_backend_pilot.py',
    'experiments/validate_development_backend_pilot.py','experiments/matched_backend_fixture.py',
    'experiments/validate_finger_middle_splits.py')


def source_identity():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCE_FILES}


def inputs():
    result=[]
    for n,k in ((32,3),(33,3),(128,7),(129,19)):
        for mirror in (False,True):
            values=values_for(n,k,mirror)
            result.append({'case':f'case-{len(result):02d}','n':n,'k':k,'mirror':mirror,
                           'values':values,'sha256':hashlib.sha256(canonical(values)).hexdigest()})
    return result


def actions(cases):
    for case in cases:
        for backend in BACKENDS:
            yield {'case':case['case'],'kind':'preflight','backend':backend,'batch_size':None,'round':None}
    for index,case in enumerate(cases):
        for rep in range(2):
            for backend in (BACKENDS if (index+rep)%2==0 else BACKENDS[::-1]):
                yield {'case':case['case'],'kind':'warmup','backend':backend,'batch_size':1,'round':rep}
        for bidx,batch_size in enumerate((1,4,16)):
            for rep in range(3):
                for backend in (BACKENDS if (index+bidx+rep)%2==0 else BACKENDS[::-1]):
                    yield {'case':case['case'],'kind':'sample','backend':backend,'batch_size':batch_size,'round':rep}


def preflight(values,name,expected):
    if len(set(values))!=len(values) or not oracle(values)['valid']:
        raise ValueError('illegal preselected Jordan input')
    result=paper_jordan_diagnostics_valid(values,backend=backend_spec(name))
    if type(result) is not dict:
        return {'status':'ERROR',**capture_output(result),
                'error':{'type':'PreflightError','message':'result is not a dictionary'}}
    captured=capture_output(result.get('output'))
    count=result.get('processed_count')
    passed=(type(count) is int and count==len(values) and captured['output']==expected
            and result.get('invariants_valid') is True
            and canonical(result.get('backend_identity'))==canonical(identity(name)))
    return {'status':'PASS' if passed else 'ERROR', 'processed_count':count if type(count) is int else None,
            'same_backend_replay':passed,**captured,
            'error':None if passed else {'type':'PreflightError','message':'count, output, audit or backend identity mismatch'}}



def trial_batch(values,name,expected,batch_size,clock=time.perf_counter_ns):
    spec=backend_spec(name)  # fixed immutable choice, not a mutable tree instance
    outputs=[];error=None
    gc.collect()  # identical policy for both, explicitly outside timer
    start=clock()
    try:
        for _ in range(batch_size):
            outputs.append(paper_jordan_sort_valid(values,'minimal',backend=spec))
    except Exception as exc:
        error=exc
    finally:
        finish=clock()
    # No oracle, expected comparison, diagnostic capture or fsync inside timer.
    captured=[capture_output(value) for value in outputs]
    if error is None and any(row['output']!=expected for row in captured):
        error=ValueError('external output mismatch')
    if error is None and (type(start) is not int or type(finish) is not int or finish<=start):
        error=ValueError('non-positive or invalid clock interval')
    return {'status':'ERROR' if error else 'PASS','elapsed_ns':finish-start,
            'completed_calls':len(outputs),'outputs':captured,
            'error':error_details(error) if error else None}


def summarize(rows):
    groups=[]
    for case in inputs():
        for backend in BACKENDS:
            for batch_size in (1,4,16):
                samples=[r for r in rows if r['kind']=='sample' and r['case']==case['case']
                         and r['backend']==backend and r['batch_size']==batch_size and r['status']=='PASS']
                if samples:
                    times=[r['elapsed_ns'] for r in samples]
                    groups.append({'case':case['case'],'backend':backend,'batch_size':batch_size,
                                   'samples':len(times),'min_batch_ns':min(times),
                                   'median_batch_ns':statistics.median(times),'max_batch_ns':max(times)})
    return groups


def run(output):
    source=source_identity();cases=inputs();schedule=list(actions(cases))
    config={'schema':SCHEMA,'protocol':PROTOCOL,'inputs':cases,'backends':{n:identity(n) for n in BACKENDS}}
    info=time.get_clock_info('perf_counter')
    ticks=[time.perf_counter_ns() for _ in range(1001)]
    deltas=[b-a for a,b in zip(ticks,ticks[1:])]
    environment={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
        'source_sha256':source,'python':sys.version,'platform':platform.platform(),
        'captured_at':datetime.now(timezone.utc).isoformat(),'python_optimize':sys.flags.optimize,
        'measurement_kind':'perf_counter_ns','gc_enabled':gc.isenabled(),
        'clock':{'implementation':info.implementation,'resolution_seconds':info.resolution,
                 'monotonic':info.monotonic,'adjustable':info.adjustable,
                 'successive_read_deltas_ns':deltas}}
    if not gc.isenabled() or not info.monotonic:
        raise RuntimeError('pilot requires enabled GC and monotonic clock')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'config.json',config);atomic_json(output/'environment.json',environment)
    rows=[];lookup={c['case']:c for c in cases}
    for index,action in enumerate(schedule):
        case=lookup[action['case']];values=case['values'];expected=sorted(values)
        base={**action,'input_sha256':case['sha256'],'backend_identity':identity(action['backend'])}
        atomic_json(output/'progress.json',{'status':'RUNNING','record_index':index,'action':action})
        row={**base,'status':'PASS','error':None}
        try:
            if action['kind']=='preflight':
                row.update(preflight(values,action['backend'],expected))
            else:
                row.update(trial_batch(values,action['backend'],expected,action['batch_size']))
            if hashlib.sha256(canonical(values)).hexdigest()!=case['sha256']:
                row.update(status='ERROR',error={'type':'InputMutation','message':'sort changed its input'})
        except Exception as exc:
            row.update(status='ERROR',error=error_details(exc))
        try:
            canonical(row)
        except (TypeError,ValueError,OverflowError,RecursionError) as exc:
            row={**base,'status':'ERROR','error':error_details(exc,'SerializationError'),
                 'output_diagnostic':output_diagnostic(row.get('outputs',row.get('output')))}
        commit_record(output,index,row);rows.append(row)
        if row['status']!='PASS':
            atomic_json(output/'failure.json',{'accepted':False,'status':'EXECUTION_ERROR',
                        'record_index':index,'action':action,'performance_eligible':False})
            break
    unchanged=source==source_identity()
    passed=len(rows)==len(schedule) and all(r['status']=='PASS' for r in rows) and unchanged
    if not unchanged:
        atomic_json(output/'failure.json',{'accepted':False,'status':'SOURCE_CHANGED','performance_eligible':False})
    summary={'schema':SCHEMA,'completed_successfully':passed,'source_unchanged':unchanged,
             'performance_eligible':False,'rows':len(rows),'planned_rows':len(schedule),
             'sample_batches':sum(r['kind']=='sample' for r in rows),
             'sample_calls':sum(r.get('completed_calls',0) for r in rows if r['kind']=='sample'),
             'groups':summarize(rows)}
    atomic_json(output/'summary.json',summary)
    atomic_json(output/'progress.json',{'status':'COMPLETE' if passed else 'FAILED','committed_records':len(rows)})
    files=sorted(p for p in output.rglob('*') if p.is_file())
    atomic_json(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    return passed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        return 0 if run(args.output) else 2
    if args.output.exists():raise FileExistsError(args.output)
    return run_bounded([sys.executable,__file__,'--worker','--output',str(args.output)],args.output,180)


if __name__=='__main__':raise SystemExit(main())
