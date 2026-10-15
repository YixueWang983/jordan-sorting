"""Independent schedule, calibration and batch-statistics reconstruction.

Reads records and qualification evidence; never runs sorting or runner schedules.
"""
import sys
if sys.flags.optimize != 0:raise RuntimeError('Matched validation requires optimization level 0')
import argparse,hashlib,json,math,random
from pathlib import Path
from common_input_protocol import BACKENDS,source_identity,digest,measurement_protocol
from common_qualification_v2_protocol import frozen_selection
from split_qualification_protocol import split_selection
from committed_records import canonical,read_records
from matched_backend_fixture import identity
from validate_common_qualification import require,number
from validate_common_qualification_v2 import validate_environment,validate as validate_qualification


def read(path):return json.loads(Path(path).read_text())


def check_review(receipt,source):
    require(type(receipt) is dict and set(receipt)=={'schema','approved','production_sha256','review_references'},'manual review receipt fields')
    require(receipt['schema']=='representation_locality_cost_review_v1' and receipt['approved'] is True,'manual review not approved')
    require(receipt['production_sha256']=={p:h for p,h in source.items() if p.startswith('src/')},'manual review source')
    require(type(receipt['review_references']) is list and receipt['review_references']
            and all(type(r) is str and r.strip() for r in receipt['review_references']),'manual review references')


def percentile(samples,p):
    values=sorted(samples);at=(len(values)-1)*p;lower=math.floor(at);upper=math.ceil(at)
    return values[lower]*(upper-at)+values[upper]*(at-lower) if upper!=lower else values[lower]


def rebuild_statistics(rows,batch):
    groups={}
    for name in BACKENDS:
        values=[r['elapsed_ns']/batch for r in rows if r['kind']=='sample' and r['backend']==name and r['status']=='PASS']
        if values:
            lo,hi=percentile(values,.25),percentile(values,.75)
            groups[name]=dict(batches=len(values),median_ns_per_call=percentile(values,.5),q25_ns_per_call=lo,q75_ns_per_call=hi,iqr_ns_per_call=hi-lo)
    return dict(groups=groups,tree_over_list_median=groups[BACKENDS[1]]['median_ns_per_call']/groups[BACKENDS[0]]['median_ns_per_call'] if len(groups)==2 else None)


def check_job(job,request,*,passing):
    rows=read_records(job);case=request['case'];rules=request['rules'];stage=request['stage'];i=request['index'];cursor=0
    def consume(kind,backend,batch,repeat):
        nonlocal cursor
        if cursor==len(rows):return False
        row=rows[cursor];cursor+=1
        expected=dict(case=case['case'],kind=kind,backend=backend,batch_size=batch,round=repeat,
                      input_sha256=case['input_sha256'],backend_identity=identity(backend))
        require(all(canonical(row.get(k))==canonical(v) for k,v in expected.items()),'batch action/config/order')
        if row.get('status')=='ERROR':
            require(not passing and cursor==len(rows) and type(row.get('error')) is dict
                    and type(row['error'].get('type')) is str and type(row['error'].get('message')) is str,'failed row')
            return False
        require(set(row)==set(expected)|{'status','error','elapsed_ns','completed_calls','outputs'},'batch row fields')
        require(row['status']=='PASS' and row['error'] is None,'batch status')
        require(type(row['elapsed_ns']) is int and row['elapsed_ns']>0,'clock interval')
        require(type(row['completed_calls']) is int and row['completed_calls']==batch,'batch completed calls')
        require(type(row['outputs']) is list and len(row['outputs'])==batch,'batch outputs')
        for output in row['outputs']:
            require(type(output) is dict and set(output)=={'output','output_diagnostic'} and output['output_diagnostic'] is None,'output capture')
            require(type(output['output']) is list and all(type(x) is int for x in output['output'])
                    and output['output']==sorted(case['values']),'external output')
        return True
    chosen=None;full=True;result=None
    if stage=='calibration':
        cfg=rules['calibration']
        for bidx,batch in enumerate(cfg['batch_candidates']):
            for rep in range(cfg['repetitions']):
                order=BACKENDS if (i+bidx+rep)%2==0 else BACKENDS[::-1]
                for name in order:
                    if not consume('calibration',name,batch,rep):full=False;break
                if not full:break
            if not full:break
            medians={name:percentile([r['elapsed_ns'] for r in rows[:cursor] if r['batch_size']==batch and r['backend']==name],.5) for name in BACKENDS}
            if all(medians[name]>=cfg['target_batch_ns'] for name in BACKENDS):
                chosen=batch;result=dict(chosen_batch=batch,median_batch_ns=medians);break
        full=full and chosen is not None
    elif stage=='formal':
        batch=request['batch_size'];require(type(batch) is int and batch in rules['calibration']['batch_candidates'],'frozen batch size')
        for kind,count,size in (('warmup',rules['warmups_per_backend'],1),('sample',rules['repetitions'],batch)):
            for rep in range(count):
                for name in (BACKENDS if (i+rep)%2==0 else BACKENDS[::-1]):
                    if not consume(kind,name,size,rep):full=False;break
                if not full:break
            if not full:break
        if full:result=rebuild_statistics(rows,batch)
    else:raise ValueError('unknown stage')
    require(cursor==len(rows),'extra/continued measurement rows')
    if passing:
        require(full,'incomplete case schedule or no qualifying common batch')
        require(canonical(read(job/'summary.json'))==canonical(dict(stage=stage,completed=True,records=len(rows),result=result)),'case summary/statistics')
        require(read(job/'progress.json')==dict(status='COMPLETE',committed_records=len(rows)),'case completion cursor')
    return dict(full=full,rows=len(rows),result=result)


def check_environment(env):
    require(type(env) is dict and set(env)=={'execution','clock'},'measurement environment fields')
    validate_environment(env['execution'],purpose='matched calibration or formal measurement')
    clock=env['clock']
    require(type(clock) is dict and set(clock)=={'implementation','resolution_seconds','monotonic','adjustable','successive_read_deltas_ns'},'clock fields')
    require(type(clock['implementation']) is str and clock['implementation'] and number(clock['resolution_seconds']) and clock['resolution_seconds']>0,'clock metadata')
    require(clock['monotonic'] is True and type(clock['adjustable']) is bool,'clock properties')
    deltas=clock['successive_read_deltas_ns']
    require(type(deltas) is list and len(deltas)==1000 and all(type(d) is int and d>=0 for d in deltas) and any(deltas),'clock observations')


def validate(output,*,qualification,calibration=None):
    output=Path(output);cfg=read(output/'config.json');env=read(output/'environment.json');check_environment(env)
    require(type(cfg) is dict and set(cfg)=={'schema','dataset','selection_sha256','cases','rules','backend_identities',
        'calibration_backend_first','interpretation','stage','scope','qualification','calibration_manifest_sha256','review','batch_sizes','performance_eligible'},'configuration fields')
    dataset=cfg['dataset'];require(dataset in ('common','targeted_split'),'dataset')
    selection=frozen_selection() if dataset=='common' else split_selection()
    cases=[dict(case=c['spec']['case'],values=c['values'],input_sha256=c['input_sha256']) for c in selection['cases']]
    require(cfg['schema']=='matched_measurement_tools_v1' and cfg['scope']=='actual' and cfg['performance_eligible'] is False,'measurement identity')
    require(canonical(cfg['rules'])==canonical(measurement_protocol()) and canonical(cfg['cases'])==canonical(cases)
            and cfg['selection_sha256']==selection['selection_sha256'],'rules/input binding')
    require(canonical(cfg['backend_identities'])==canonical({n:identity(n) for n in BACKENDS}),'backend config')
    require(cfg['calibration_backend_first']=='alternate case index + candidate index + repeat'
            and cfg['interpretation']=='datasets analyzed separately; mirrors and related constructions are dependent; batch is statistical unit','schedule/scope')
    q=validate_qualification(qualification,historical=True,dataset=dataset);require(q['all_selected_qualified'],'qualification incomplete')
    qenv=read(Path(qualification)/'environment.json');production={p:h for p,h in source_identity().items() if p.startswith('src/')}
    require({p:h for p,h in qenv['source_sha256'].items() if p.startswith('src/')}==production,'qualified production changed')
    expected_binding=dict(producing_head=qenv['head'],selection_sha256=q['selection_sha256'],
        archive_manifest_sha256=digest(read(Path(qualification)/'manifest.json')),production_sources_identical=True,current_production_sha256=production)
    require(canonical(cfg['qualification'])==canonical(expected_binding),'qualification provenance')
    stage=cfg['stage'];require(stage in ('calibration','formal'),'stage')
    if stage=='formal':
        require(calibration is not None,'calibration archive required')
        cal=validate(calibration,qualification=qualification)
        require(cal['stage']=='calibration' and cal['complete'],'calibration is incomplete')
        require(cfg['batch_sizes']==cal['batch_sizes'] and cfg['calibration_manifest_sha256']==digest(read(Path(calibration)/'manifest.json')),'calibration freeze')
        calenv=read(Path(calibration)/'environment.json')['execution']
        for key in ('source_sha256','python','executable','platform','machine','gc_thresholds'):
            require(canonical(calenv[key])==canonical(env['execution'][key]),'calibration environment/source mismatch')
        require({k:v for k,v in calenv['hardware'].items() if k!='power'}=={k:v for k,v in env['execution']['hardware'].items() if k!='power'},'calibration hardware mismatch')
        check_review(cfg['review'],env['execution']['source_sha256'])
        random.Random(cfg['rules']['order']['case_shuffle_seed']).shuffle(cases)
    else:require(cfg['batch_sizes']=={} and cfg['review'] is None and cfg['calibration_manifest_sha256'] is None,'calibration scope')
    statuses=read_records(output);require(len(statuses)==len(cases),'case statuses')
    files={'config.json','environment.json','summary.json'};stopped=False;batches={};statistics_by_case={}
    for i,(case,status) in enumerate(zip(cases,statuses)):
        cid=case['case'];request=dict(stage=stage,case=case,index=i,rules=cfg['rules'],batch_size=cfg['batch_sizes'].get(cid),gc_thresholds=env['execution']['gc_thresholds'])
        require(canonical(read(output/'requests'/f'{cid}.json'))==canonical(request),'request order/config')
        files|={f'requests/{cid}.json',f'records/{i:06d}.json.gz'}
        require(set(status)=={'case','status','reason','budget_seconds'} and status['case']==cid,'case status fields')
        maximum=cfg['rules']['calibration']['budget_seconds'] if stage=='calibration' else cfg['rules']['input_seconds']
        require(number(status['budget_seconds']) and status['budget_seconds']<=maximum,'case budget')
        if status['status']=='NOT_RUN':
            require(type(status['reason']) is str and status['reason'] and (stopped or status['reason']=='campaign budget exhausted'),'not-run reason')
            stopped=True;continue
        require(not stopped and status['status'] in ('PASS','ERROR','TIMEOUT') and status['budget_seconds']>0,'continued after failed case')
        passing=status['status']=='PASS';job=output/'jobs'/cid;result=check_job(job,request,passing=passing)
        files|={f'jobs/{cid}/records/{j:06d}.json.gz' for j in range(result['rows'])}
        for leaf in ('progress.json','summary.json'):
            if (job/leaf).is_file():files.add(f'jobs/{cid}/{leaf}')
        if passing:
            require(status['reason'] is None,'pass reason')
            if stage=='calibration':batches[cid]=result['result']['chosen_batch']
            else:statistics_by_case[cid]=result['result']
        else:
            stopped=True;failure=read(job/'failure.json');files.add(f'jobs/{cid}/failure.json')
            require(type(status['reason']) is str and status['reason'] and failure.get('accepted') is False
                    and failure.get('performance_eligible') is False,'failure evidence')
            require(type(failure.get('committed_records')) is int and failure['committed_records']==result['rows'],'recovered count')
            require(failure.get('status') in (('RESOURCE_TIMEOUT',) if status['status']=='TIMEOUT' else ('WORKER_ERROR','INVALID_WORKER_EVIDENCE')),'failure type')
            if status['status']=='TIMEOUT':require(failure.get('budget_seconds')==status['budget_seconds'],'timeout budget')
            if 'current' in failure:require(failure['current']==(read(job/'progress.json') if (job/'progress.json').exists() else None),'failure cursor')
            files|={str(p.relative_to(output)) for p in job.rglob('*.partial') if p.name.startswith('.')}
    complete=all(r['status']=='PASS' for r in statuses)
    require(canonical(read(output/'summary.json'))==canonical(dict(stage=stage,complete=complete,
        status_counts={s:sum(r['status']==s for r in statuses) for s in ('PASS','ERROR','TIMEOUT','NOT_RUN')},source_unchanged=True,performance_eligible=False)),'summary reconstruction')
    manifest=read(output/'manifest.json');require(type(manifest) is dict and set(manifest)==files,'manifest inventory')
    dirs={str(p) for f in files for p in Path(f).parents if str(p)!='.'}|{'jobs','requests'}
    require({str(p.relative_to(output)) for p in output.rglob('*')}==files|dirs|{'manifest.json'},'extra entries')
    require(not any(p.is_symlink() for p in output.rglob('*')),'symlink')
    require(all((output/f).is_file() and hashlib.sha256((output/f).read_bytes()).hexdigest()==h for f,h in manifest.items()),'manifest hashes')
    return dict(archive_valid=True,stage=stage,complete=complete,dataset=dataset,inputs=len(cases),batch_sizes=batches,
        statistics=statistics_by_case,source_head=env['execution']['head'],performance_eligible=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    parser.add_argument('--qualification',type=Path,required=True);parser.add_argument('--calibration',type=Path)
    args=parser.parse_args();report=validate(args.directory,qualification=args.qualification,calibration=args.calibration)
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['complete'] else 2)
