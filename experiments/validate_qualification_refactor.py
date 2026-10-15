"""Fixed v2 development checks, never a 140-input campaign or timing run."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification refinement requires optimization level 0')
import argparse
from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
import time
from unittest.mock import patch
from common_input_protocol import ROOT, source_identity, digest, BACKENDS
from committed_records import atomic_json, canonical, commit_record, read_records, run_bounded
from matched_backend_fixture import backend_spec, identity, capture_output, error_details
from qualify_common_inputs import environment, seal
from validate_finger_middle_splits import values_for
from oracle import oracle
import paper_jordan as core
from paper_jordan_validation import run_synchronous_qualification, QUALIFICATION_SCHEMA
from paper_jordan_sort import paper_jordan_sort_valid
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree

OLD_SELECTION = ROOT/'docs/validation/common_qualification_20261015/qualification/selected.json'
INPUT_SET_SHA256 = 'c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b'
SCHEMA = 'qualification_refactor_development_v2'


def cases():
    frozen = json.loads(OLD_SELECTION.read_text())
    if digest(frozen['cases']) != INPUT_SET_SHA256:
        raise ValueError('original 140-input selection changed')
    selected = {c['spec']['case']:c for c in frozen['cases']}
    result=[]
    for n in (64,129,257,513):
        for shape in (('flat','middle') if n<200 else ('flat','middle','heavy')):
            for mirror in (False,True):
                if shape=='middle':
                    k=7 if n==64 else 19
                    values=values_for(n,k,mirror); source=f'values_for({n},{k},{mirror})'
                else:
                    category='strict_flat' if shape=='flat' else 'nested_heavy_valid'
                    source=f'n{n}-{category}-00'+('-mirror' if mirror else '')
                    values=selected[source]['values']
                result.append(dict(case=f'n{n}-{shape}'+('-mirror' if mirror else ''), n=n,
                    shape=shape,mirror=mirror,values=values,input_sha256=digest(values),source=source,
                    compare_reference=n<200))
    return result


def plan():
    return dict(schema=SCHEMA,qualification_schema=QUALIFICATION_SCHEMA,cases=cases(),
                frozen_140_selection_sha256=INPUT_SET_SHA256,case_seconds=180,campaign_seconds=1200,
                scheduling='two independent checked states at every prefix; one fresh checked final replay; separately fresh public minimal output',
                difference_from_v1='no fresh constructor at every prefix; fewer redundant early updates; original v1 timeout archive retained',
                reference='64/129 only, original repeated-filter predicates and fresh-prefix replay; compare every completed prefix view',
                instrumentation='tree _audit calls, actual initialization calls, neighbor reconstruction/link/removal and reference filter/index counts; observer/persistence included in resource wall time',
                failure='stop first case failure/timeout; retain completed version records and mark later cases NOT_RUN',
                performance_eligible=False)


def fingerprint(state, snapshots):
    payload = dict(prefix=state.processed_count, backend=state.backend_identity,
        initial_lists=state.initial_sibling_list_ids, points=state.partial_order.to_point_ids(),
        pairs=state.pair_by_end_index, stages=state.stage_results, trace=state.trace,
        metrics=state.metrics, backend_work=state.backend_work, snapshots=snapshots)
    encoded=json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False,
                       default=lambda x:asdict(x) if is_dataclass(x) else (_ for _ in ()).throw(TypeError(type(x).__name__))).encode()
    return hashlib.sha256(encoded).hexdigest()


def evaluate(case, name, mode, output):
    values=case['values']; expected=sorted(values); prefixes=[]; work={}; counts={'tree_audit_calls':0,'initializations':0}
    audit=Tree._audit; initialize=core._initialize_paper_jordan_state_values
    def counted_audit(b,*a,**kw):
        counts['tree_audit_calls']+=1; return audit(b,*a,**kw)
    def counted_init(*a,**kw):
        counts['initializations']+=1; return initialize(*a,**kw)
    def observe(state, snapshots):
        k=state.processed_count
        if state.partial_order.to_list()!=sorted(values[:k]):
            raise ValueError('external completed-prefix output mismatch')
        prefixes.append(dict(prefix=k,state_sha256=fingerprint(state,snapshots)))
        atomic_json(output/'progress.json',dict(status='RUNNING',case=case['case'],backend=name,
                                               mode=mode,last_completed_prefix=k))
    def reference(state):
        snapshots=core.validate_paper_jordan_state_reference(state,history_work=work,return_snapshots=True)
        observe(state,snapshots)
    started=time.monotonic(); report=None
    with patch.object(Tree,'_audit',counted_audit), patch.object(core,'_initialize_paper_jordan_state_values',counted_init):
        if mode=='reference':
            state=core._run_paper_jordan_state_values(list(values),backend=backend_spec(name),invariant_callback=reference)
        elif mode=='synchronous_v2':
            state,report=run_synchronous_qualification(values,backend=backend_spec(name),prefix_callback=observe)
            work=report['history_work']
        else:
            captured=capture_output(paper_jordan_sort_valid(values,'minimal',backend=backend_spec(name)))
            if captured['output']!=expected: raise ValueError('external minimal output mismatch')
            return dict(**captured,prefixes=[],history_work={},counts=counts,report=None,
                        resource_wall_seconds=time.monotonic()-started,final=None)
    captured=capture_output(state.partial_order.to_list())
    if captured['output']!=expected: raise ValueError('external final output mismatch')
    return dict(**captured,prefixes=prefixes,history_work=work,counts=counts,report=report,
                resource_wall_seconds=time.monotonic()-started,
                final=dict(metrics=dict(state.metrics),trace=state.trace,
                           backend_work={str(i):asdict(v) for i,v in state.backend_work.items()}))


def run_case(case, output):
    output.mkdir(parents=True,exist_ok=False)
    if not oracle(case['values'])['valid']: raise ValueError('illegal fixed case')
    previous={}; index=0
    for name in BACKENDS:
        for mode in (('reference','synchronous_v2','fresh_minimal') if case['compare_reference'] else ('synchronous_v2','fresh_minimal')):
            atomic_json(output/'progress.json',dict(status='RUNNING',case=case['case'],backend=name,mode=mode))
            base=dict(case=case['case'],backend=name,backend_identity=identity(name),mode=mode,
                      input_sha256=case['input_sha256'],status='PASS',error=None)
            try:
                row={**base,**evaluate(case,name,mode,output)}
                if digest(case['values']) != case['input_sha256']:
                    raise ValueError('input mutation')
                if mode=='reference': previous[name]=row
                if mode=='synchronous_v2' and case['compare_reference']:
                    old=previous[name]
                    if row['prefixes']!=old['prefixes'] or row['final']!=old['final']:
                        raise ValueError('reference/new prefix state or final evidence mismatch')
            except Exception as exc:
                row={**base,'status':'ERROR','error':error_details(exc)}
            try:
                canonical(row)
            except (ValueError,TypeError,OverflowError,RecursionError) as exc:
                row={**base,'status':'ERROR','error':error_details(exc,'SerializationError')}
            commit_record(output,index,row); index+=1
            if row['status']!='PASS': return 2
    atomic_json(output/'progress.json',dict(status='COMPLETE',records=index))
    return 0


def run(output):
    env=environment()
    if env['dirty']: raise RuntimeError('freeze source before actual development campaign')
    output.mkdir(parents=True,exist_ok=False)
    cfg=plan(); atomic_json(output/'plan.json',cfg); atomic_json(output/'environment.json',env)
    (output/'jobs').mkdir(); (output/'requests').mkdir()
    rows=[]; stop=None; deadline=time.monotonic()+cfg['campaign_seconds']
    for i,case in enumerate(cfg['cases']):
        path=output/'requests'/f"{case['case']}.json"; atomic_json(path,case)
        remaining=deadline-time.monotonic(); budget=max(0,min(remaining,cfg['case_seconds']))
        row=dict(case=case['case'],status='NOT_RUN',reason=stop,budget_seconds=budget)
        if stop is None and remaining>0:
            code=run_bounded([sys.executable,__file__,'--worker',str(path),'--output',str(output/'jobs'/case['case'])],output/'jobs'/case['case'],budget)
            if code==0:
                records=read_records(output/'jobs'/case['case'])
                if len(records)!=(6 if case['compare_reference'] else 4) or any(r.get('status')!='PASS' for r in records):
                    code=2
                    atomic_json(output/'jobs'/case['case']/'failure.json',dict(accepted=False,status='INCOMPLETE_WORKER_RECORDS'))
            row['status']='PASS' if code==0 else 'FAILED'
            if code:
                stop=f"{case['case']}: FAILED"; row['reason']=stop
        elif stop is None:
            stop='campaign resource budget exhausted';row['reason']=stop
        commit_record(output,i,row);rows.append(row)
        print(f"{i+1}/{len(cfg['cases'])} {case['case']}: {row['status']}",flush=True)
    passed=all(r['status']=='PASS' for r in rows) and source_identity()==env['source_sha256']
    atomic_json(output/'summary.json',dict(completed=passed,source_unchanged=source_identity()==env['source_sha256'],
        cases=len(rows),passed=sum(r['status']=='PASS' for r in rows),performance_eligible=False,
        full_140_qualified=False,efficient_backend_accepted=False))
    seal(output); return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--worker',type=Path,help=argparse.SUPPRESS);args=parser.parse_args()
    if args.worker: raise SystemExit(run_case(json.loads(args.worker.read_text()),args.output))
    raise SystemExit(0 if run(args.output) else 2)
