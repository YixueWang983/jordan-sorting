"""Bounded, archived equivalence checks; --check only reads saved evidence."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time

from common_input_protocol import ROOT, digest, source_identity
from common_qualification_v2_protocol import frozen_selection
from split_qualification_protocol import split_selection
from committed_records import atomic_json, commit_record, read_records, run_bounded, canonical
from qualify_common_inputs import environment, read, seal
from matched_backend_fixture import backend_spec, identity
from paper_jordan_validation import run_synchronous_qualification
from paper_jordan_sort import paper_jordan_sort_valid
from sibling_backend_contract import SiblingBackendSpec
from heterogeneous_finger_backend import HeterogeneousFingerBackend
from qualification_trace_semantics import check_trace
from uninstrumented_finger import prepare_uninstrumented
from uninstrumented_protocol import registration

SCHEMA = 'uninstrumented_equivalence_v1'
NAMES = ('heterogeneous_finger', 'heterogeneous_finger_uninstrumented')
SUPPLEMENT = ROOT/'docs/validation/thesis_revision_20261020/local_supplement'


def selection():
    cases=[]
    for group, selected in (('common',frozen_selection()),('targeted_split',split_selection())):
        for c in selected['cases']:
            cases.append(dict(case=group+'--'+c['spec']['case'], original_case=c['spec']['case'],
                              group=group, values=c['values'], input_sha256=c['input_sha256']))
    old=read(SUPPLEMENT/'protocol.json'); values=read(SUPPLEMENT/'inputs.json')
    if hashlib.sha256((SUPPLEMENT/'inputs.json').read_bytes()).hexdigest()!=old['inputs_sha256']:
        raise ValueError('seeded input archive changed')
    for c in old['stress']:
        v=values[c['case']]
        cases.append(dict(case='seeded--'+c['case'], original_case=c['case'],group='seeded',
                          values=v,input_sha256=digest(v)))
    if len(cases)!=192 or max(len(c['values']) for c in cases)>1500:
        raise ValueError('equivalence input inventory changed')
    return cases


def legacy_trace(case):
    if case['group']=='seeded':
        rows=read_records(SUPPLEMENT/('stress-'+case['original_case']))
        return rows[0]['trace']
    base = ROOT/'docs/validation'/(
        'common_qualification_v2_20261015' if case['group']=='common' else 'split_trace_followup_20261015')/'qualification'
    rows=read_records(base/'jobs'/case['original_case'])
    return next(r['final']['trace'] for r in rows if r['backend']=='heterogeneous_finger' and r['mode']=='synchronous_v2')


def state_fingerprint(state, snapshots):
    # The backend identity is deliberately separate: the two options differ.
    # All logical/physical state, stage outcomes, counters and traces are compared.
    payload=dict(prefix=state.processed_count,initial_lists=state.initial_sibling_list_ids,
                 points=state.partial_order.to_point_ids(),pairs=state.pair_by_end_index,
                 stages=state.stage_results,trace=state.trace,metrics=state.metrics,
                 backend_work=state.backend_work,snapshots=snapshots)
    encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False,default=asdict).encode()
    return hashlib.sha256(encoded).hexdigest()


def checked(values, spec):
    prefixes=[]
    def observe(state, views):
        k=state.processed_count; output=state.partial_order.to_list()
        if output!=sorted(values[:k]):raise ValueError('incorrect completed prefix')
        prefixes.append(dict(prefix=k,output_sha256=digest(output),state_sha256=state_fingerprint(state,views)))
    state,report=run_synchronous_qualification(values,backend=spec,prefix_callback=observe)
    return dict(output=state.partial_order.to_list(),trace=state.trace,metrics=state.metrics,
                prefixes=prefixes,qualification_report=report,backend_identity=spec.identity),state


def evaluate(case, counted=False):
    values=case['values']; reports={}; minimal={}
    for name in NAMES:
        reports[name],_=checked(values,backend_spec(name))
        minimal[name]=paper_jordan_sort_valid(values,'minimal',backend=backend_spec(name))
    left,right=(reports[n] for n in NAMES)
    for field in ('output','trace','metrics','prefixes','qualification_report'):
        if canonical(left[field])!=canonical(right[field]):raise ValueError('configuration divergence: '+field)
    if any(v!=sorted(values) for v in minimal.values()) or left['output']!=sorted(values):
        raise ValueError('incorrect output')
    original=legacy_trace(case)
    if canonical(left['trace'])!=canonical(original):raise ValueError('default trace differs from original archive')
    detailed=None
    if counted:
        detailed,state=checked(values,SiblingBackendSpec(HeterogeneousFingerBackend))
        for field in ('output','trace','metrics','prefixes','qualification_report'):
            if canonical(left[field])!=canonical(detailed[field]):raise ValueError('counter-enabled divergence: '+field)
        detailed['work']=state.sibling_backend.work.snapshot()
        if detailed['work']['operations']['node_visits']<=0:raise ValueError('counted run did not collect work')
    return dict(case=case['case'],input_sha256=case['input_sha256'],checked=reports,minimal=minimal,
                counted=detailed,legacy_trace_sha256=digest(original),legacy_trace_equal=True,status='PASS')


def run(output):
    cases=selection();env=environment(include_power_settings=True)
    if env['dirty']:raise RuntimeError('commit source before equivalence campaign')
    cfg=dict(schema=SCHEMA,preregistration=registration(),cases=cases,case_seconds=600,campaign_seconds=7200,
             counted_case=next(c['case'] for c in cases if c['group']=='targeted_split'),
             interpretation='finite checked/minimal equivalence evidence, not a general proof')
    output.mkdir(parents=True,exist_ok=False)
    atomic_json(output/'config.json',cfg);atomic_json(output/'environment.json',env)
    family=prepare_uninstrumented()
    atomic_json(output/'projection.json',dict(source_sha256=family.source_sha256,removed=family.projection))
    (output/'requests').mkdir();(output/'jobs').mkdir()
    deadline=time.monotonic()+cfg['campaign_seconds'];stop=None;rows=[]
    for i,case in enumerate(cases):
        req=dict(case=case,counted=case['case']==cfg['counted_case'])
        path=output/'requests'/(case['case']+'.json');atomic_json(path,req)
        seconds=max(0,min(cfg['case_seconds'],deadline-time.monotonic()))
        row=dict(case=case['case'],status='NOT_RUN',reason=stop)
        if stop is None and seconds>0:
            job=output/'jobs'/case['case']
            code=run_bounded([sys.executable,str(Path(__file__).resolve()),'--worker',str(path),'--output',str(job)],job,seconds)
            row['status']='PASS' if code==0 else 'ERROR'
            if code:stop='equivalence failed: '+case['case'];row['reason']=stop
        elif stop is None:stop='equivalence campaign budget exhausted';row['reason']=stop
        commit_record(output,i,row);rows.append(row)
        print(f"{i+1}/192 {case['case']}: {row['status']}",flush=True)
    complete=all(r['status']=='PASS' for r in rows) and source_identity()==env['source_sha256']
    atomic_json(output/'summary.json',dict(complete=complete,inputs=len(cases),passed=sum(r['status']=='PASS' for r in rows),source_unchanged=source_identity()==env['source_sha256']))
    seal(output)
    return complete


def validate(output, *, historical=False):
    from validate_common_qualification_v2 import validate_environment
    cfg=read(output/'config.json');cases=selection();env=read(output/'environment.json')
    validate_environment(env,power_fields=True,historical=historical)
    if cfg['schema']!=SCHEMA or cfg['cases']!=cases or cfg['preregistration']!=registration():
        raise ValueError('equivalence configuration/input binding')
    statuses=read_records(output)
    if len(statuses)!=192 or not all(r['status']=='PASS' for r in statuses):raise ValueError('incomplete equivalence')
    prefixes=0;counted=0
    for case,status in zip(cases,statuses,strict=True):
        if status!=dict(case=case['case'],status='PASS',reason=None):raise ValueError('case order/status')
        record,=read_records(output/'jobs'/case['case'])
        if record['case']!=case['case'] or record['input_sha256']!=digest(case['values']):raise ValueError('case binding')
        for name in NAMES:
            r=record['checked'][name]
            if canonical(r['backend_identity'])!=canonical(identity(name)):raise ValueError('backend identity')
            if r['output']!=sorted(case['values']) or record['minimal'][name]!=r['output']:raise ValueError('output')
            if [p['prefix'] for p in r['prefixes']]!=list(range(3,len(case['values'])+1)):raise ValueError('prefix coverage')
            for p in r['prefixes']:
                if p['output_sha256']!=digest(sorted(case['values'][:p['prefix']])):raise ValueError('prefix output')
            check_trace(case['values'],r['trace'],r['metrics'],name)
        left,right=(record['checked'][n] for n in NAMES)
        for field in ('output','trace','metrics','prefixes','qualification_report'):
            if canonical(left[field])!=canonical(right[field]):raise ValueError('saved configuration divergence')
        if digest(left['trace'])!=record['legacy_trace_sha256'] or canonical(left['trace'])!=canonical(legacy_trace(case)):
            raise ValueError('original trace mismatch')
        prefixes+=len(left['prefixes'])
        if record['counted'] is not None:
            if case['case']!=cfg['counted_case']:raise ValueError('unexpected counted case')
            for field in ('output','trace','metrics','prefixes','qualification_report'):
                if canonical(left[field])!=canonical(record['counted'][field]):raise ValueError('counted divergence')
            counted+=1
    if counted!=1:raise ValueError('missing counted comparison')
    manifest=read(output/'manifest.json')
    actual={p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in output.rglob('*') if p.is_file() and p.name!='manifest.json'}
    if manifest!=actual:raise ValueError('manifest mismatch')
    if read(output/'summary.json')!=dict(complete=True,inputs=192,passed=192,source_unchanged=True):raise ValueError('summary')
    return dict(archive_valid=True,inputs=192,completed_prefixes_per_configuration=prefixes,trace_equal=True,
                legacy_traces_unchanged=192,counted_comparisons=counted,source_head=env['head'],performance_evidence=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--worker',type=Path);p.add_argument('--check',action='store_true')
    p.add_argument('--historical',action='store_true');a=p.parse_args()
    if a.historical and not a.check:
        p.error('--historical is only available with --check')
    if a.worker:
        a.output.mkdir(parents=True,exist_ok=False);request=read(a.worker)
        result=evaluate(**request);commit_record(a.output,0,result);raise SystemExit(0)
    if a.check:print(json.dumps(validate(a.output,historical=a.historical),indent=2))
    else:raise SystemExit(0 if run(a.output) else 2)
