"""Frozen matched calibration / paired measurement tools.

Actual formal sampling requires qualified inputs, validated calibration and an
explicit manual-review receipt. Tests use labelled mechanical fixtures only.
"""
import sys
if sys.flags.optimize != 0:raise RuntimeError('Matched evidence requires optimization level 0')
import argparse,gc,json,random,statistics,time
from pathlib import Path
from common_input_protocol import BACKENDS,source_identity,digest,measurement_protocol
from common_qualification_v2_protocol import frozen_selection
from split_qualification_protocol import split_selection,split_measurement_protocol
from committed_records import atomic_json,commit_record,read_records,run_bounded,canonical
from qualify_common_inputs import environment,read,seal
from matched_backend_fixture import identity,error_details,output_diagnostic
from development_backend_pilot import trial_batch

SCHEMA='matched_measurement_tools_v1'
PURPOSE='matched calibration or formal measurement'


def dataset_config(dataset):
    if dataset=='common':selection=frozen_selection();rules=measurement_protocol()
    elif dataset=='targeted_split':selection=split_selection();rules=split_measurement_protocol()['rules']
    else:raise ValueError('unknown dataset')
    return dict(schema=SCHEMA,dataset=dataset,selection_sha256=selection['selection_sha256'],
        cases=[dict(case=c['spec']['case'],values=c['values'],input_sha256=c['input_sha256']) for c in selection['cases']],
        rules=rules,backend_identities={n:identity(n) for n in BACKENDS},
        calibration_backend_first='alternate case index + candidate index + repeat',
        interpretation='datasets analyzed separately; mirrors and related constructions are dependent; batch is statistical unit')


def capture_environment():
    execution=environment();execution['purpose']=PURPOSE
    info=time.get_clock_info('perf_counter');ticks=[time.perf_counter_ns() for _ in range(1001)]
    if not info.monotonic or not gc.isenabled():raise RuntimeError('requires monotonic clock and enabled GC')
    return dict(execution=execution,clock=dict(implementation=info.implementation,resolution_seconds=info.resolution,
        monotonic=info.monotonic,adjustable=info.adjustable,successive_read_deltas_ns=[b-a for a,b in zip(ticks,ticks[1:])]))


def action(case,kind,name,batch,rep):
    return dict(case=case['case'],kind=kind,backend=name,batch_size=batch,round=rep,
                input_sha256=case['input_sha256'],backend_identity=identity(name))


def quantile(values,p):
    ordered=sorted(values);x=(len(ordered)-1)*p;i=int(x)
    return ordered[i]+(ordered[min(i+1,len(ordered)-1)]-ordered[i])*(x-i)


def case_statistics(rows,batch):
    groups={}
    for name in BACKENDS:
        samples=[r['elapsed_ns']/batch for r in rows if r['kind']=='sample' and r['backend']==name and r['status']=='PASS']
        if samples:
            q1,q3=quantile(samples,.25),quantile(samples,.75)
            groups[name]=dict(batches=len(samples),median_ns_per_call=statistics.median(samples),q25_ns_per_call=q1,q75_ns_per_call=q3,iqr_ns_per_call=q3-q1)
    return dict(groups=groups,tree_over_list_median=groups[BACKENDS[1]]['median_ns_per_call']/groups[BACKENDS[0]]['median_ns_per_call'] if len(groups)==2 else None)


def execute_case(request,output):
    output.mkdir(parents=True,exist_ok=False)
    case=request['case'];rules=request['rules'];stage=request['stage'];case_index=request['index']
    expected=sorted(case['values']);rows=[];index=0;chosen=None
    thresholds=gc.get_threshold()
    if list(thresholds)!=request['gc_thresholds'] or not gc.isenabled():raise RuntimeError('worker GC differs from frozen environment')
    def perform(kind,name,batch,rep):
        nonlocal index
        base=action(case,kind,name,batch,rep)
        atomic_json(output/'progress.json',dict(status='RUNNING',record_index=index,action=base))
        row={**base,'status':'PASS','error':None}
        try:
            if not gc.isenabled() or gc.get_threshold()!=thresholds:raise RuntimeError('GC configuration changed')
            row.update(trial_batch(case['values'],name,expected,batch,clock=time.perf_counter_ns))
            if digest(case['values'])!=case['input_sha256']:raise ValueError('input mutation')
        except Exception as exc:row.update(status='ERROR',error=error_details(exc))
        try:canonical(row)
        except (TypeError,ValueError,OverflowError,RecursionError) as exc:
            row={**base,'status':'ERROR','error':error_details(exc,'SerializationError'),
                 'output_diagnostic':output_diagnostic(row.get('outputs'))}
        commit_record(output,index,row);index+=1;rows.append(row)
        return row['status']=='PASS'
    if stage=='calibration':
        cfg=rules['calibration']
        for bidx,batch in enumerate(cfg['batch_candidates']):
            for rep in range(cfg['repetitions']):
                for name in (BACKENDS if (case_index+bidx+rep)%2==0 else BACKENDS[::-1]):
                    if not perform('calibration',name,batch,rep):return 2
            medians={name:statistics.median(r['elapsed_ns'] for r in rows if r['batch_size']==batch and r['backend']==name) for name in BACKENDS}
            if min(medians.values())>=cfg['target_batch_ns']:
                chosen=batch;break
        if chosen is None:
            atomic_json(output/'failure.json',dict(status='NO_COMMON_BATCH',cause='NO_COMMON_BATCH',accepted=False,performance_eligible=False))
            return 2
        result=dict(chosen_batch=chosen,median_batch_ns=medians)
    elif stage=='formal':
        batch=request['batch_size']
        for rep in range(rules['warmups_per_backend']):
            for name in (BACKENDS if (case_index+rep)%2==0 else BACKENDS[::-1]):
                if not perform('warmup',name,1,rep):return 2
        for rep in range(rules['repetitions']):
            for name in (BACKENDS if (case_index+rep)%2==0 else BACKENDS[::-1]):
                if not perform('sample',name,batch,rep):return 2
        result=case_statistics(rows,batch)
    else:raise ValueError('unknown stage')
    atomic_json(output/'summary.json',dict(stage=stage,completed=True,records=len(rows),result=result))
    atomic_json(output/'progress.json',dict(status='COMPLETE',committed_records=len(rows)))
    return 0


def qualify_binding(path,dataset):
    from validate_common_qualification_v2 import validate
    report=validate(path,historical=True,dataset=dataset)
    if not report['all_selected_qualified']:raise ValueError('dataset is not qualified')
    env=read(Path(path)/'environment.json');current=source_identity()
    if {p:h for p,h in env['source_sha256'].items() if p.startswith('src/')}!={p:h for p,h in current.items() if p.startswith('src/')}:
        raise ValueError('production changed since qualification; requalify affected paths')
    return dict(producing_head=env['head'],selection_sha256=report['selection_sha256'],
        archive_manifest_sha256=digest(read(Path(path)/'manifest.json')),production_sources_identical=True,
        current_production_sha256={p:h for p,h in current.items() if p.startswith('src/')})


def run(output,stage,dataset,qualification,*,calibration=None,review=None):
    # No output or timing until qualification and, for formal, calibration and
    # manual-review provenance are checked. This is not a proof validator.
    from validate_matched_measurement import validate,check_review,check_job
    cfg=dataset_config(dataset);binding=qualify_binding(qualification,dataset);batches={};calibration_binding=None
    env=capture_environment()
    if env['execution']['dirty']:raise RuntimeError('freeze tools before actual calibration/measurement')
    if stage=='formal':
        if calibration is None or review is None:raise ValueError('formal needs calibration and explicit manual review receipt')
        report=validate(calibration,qualification=qualification)
        if not report['complete'] or report['stage']!='calibration':raise ValueError('incomplete calibration')
        calenv=read(Path(calibration)/'environment.json')
        if calenv['execution']['source_sha256']!=env['execution']['source_sha256']:raise ValueError('source changed after calibration')
        for key in ('python','executable','platform','machine','gc_thresholds'):
            if calenv['execution'][key]!=env['execution'][key]:raise ValueError('calibration environment changed')
        if {k:v for k,v in calenv['execution']['hardware'].items() if k!='power'}!={k:v for k,v in env['execution']['hardware'].items() if k!='power'}:
            raise ValueError('calibration hardware changed')
        check_review(review,env['execution']['source_sha256'])
        batches=report['batch_sizes'];calibration_binding=digest(read(Path(calibration)/'manifest.json'))
    cfg.update(stage=stage,scope='actual',qualification=binding,calibration_manifest_sha256=calibration_binding,
               review=review,batch_sizes=batches,performance_eligible=False)
    output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'config.json',cfg);atomic_json(output/'environment.json',env)
    (output/'jobs').mkdir();(output/'requests').mkdir()
    cases=list(cfg['cases'])
    if stage=='formal':random.Random(cfg['rules']['order']['case_shuffle_seed']).shuffle(cases)
    budget=cfg['rules']['calibration']['budget_seconds'] if stage=='calibration' else cfg['rules']['campaign_seconds']
    deadline=time.monotonic()+budget;statuses=[];stop=None
    for i,case in enumerate(cases):
        request=dict(stage=stage,case=case,index=i,rules=cfg['rules'],batch_size=batches.get(case['case']),gc_thresholds=env['execution']['gc_thresholds'])
        path=output/'requests'/f"{case['case']}.json";atomic_json(path,request);job=output/'jobs'/case['case']
        remaining=deadline-time.monotonic();seconds=max(0,min(remaining,budget if stage=='calibration' else cfg['rules']['input_seconds']))
        row=dict(case=case['case'],status='NOT_RUN',reason=stop,budget_seconds=seconds)
        if stop is None and remaining>0:
            code=run_bounded([sys.executable,str(Path(__file__).resolve()),'--worker',str(path),'--output',str(job)],job,seconds)
            if code==0:
                try:check_job(job,request,passing=True)
                except (ValueError,TypeError,KeyError,OSError) as exc:
                    code=2;atomic_json(job/'failure.json',dict(status='INVALID_WORKER_EVIDENCE',accepted=False,error=error_details(exc),performance_eligible=False,committed_records=len(read_records(job))))
            row['status']='PASS' if not code else ('TIMEOUT' if read(job/'failure.json')['status']=='RESOURCE_TIMEOUT' else 'ERROR')
            if code:stop=f"{case['case']}: {row['status']}";row['reason']=stop
        elif stop is None:stop='campaign budget exhausted';row['reason']=stop
        commit_record(output,i,row);statuses.append(row)
    complete=all(r['status']=='PASS' for r in statuses) and source_identity()==env['execution']['source_sha256']
    atomic_json(output/'summary.json',dict(stage=stage,complete=complete,status_counts={s:sum(r['status']==s for r in statuses) for s in ('PASS','ERROR','TIMEOUT','NOT_RUN')},
        source_unchanged=source_identity()==env['execution']['source_sha256'],performance_eligible=False))
    seal(output);return complete


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--worker',type=Path);parser.add_argument('--stage',choices=('calibration','formal'))
    parser.add_argument('--dataset',choices=('common','targeted_split'));parser.add_argument('--qualification',type=Path)
    parser.add_argument('--calibration',type=Path);parser.add_argument('--review',type=Path)
    args=parser.parse_args()
    if args.worker:raise SystemExit(execute_case(read(args.worker),args.output))
    if not args.stage or not args.dataset or not args.qualification:parser.error('stage, dataset and qualification required')
    raise SystemExit(0 if run(args.output,args.stage,args.dataset,args.qualification,calibration=args.calibration,
                              review=read(args.review) if args.review else None) else 2)
