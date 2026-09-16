"""Bounded, non-timing correctness/coverage supplement; never invokes a timing runner."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments')]
from audit_generator_coverage import sequence_hash
from generators import generate_sequence
from oracle import oracle
from paper_jordan_sort import paper_jordan_diagnostics_valid, paper_jordan_sort_valid, _run_paper_jordan_valid
from stats import structure_profile

FROZEN = ['results/runs/week11_pilot_v1__run003', 'results/runs/week12_formal_sorting_v1__run001']
HISTORY = ROOT / FROZEN[1]
ERRORS = {'GENERATION_ERROR', 'CERTIFICATION_ERROR', 'OUTPUT_MISMATCH', 'STATE_INVARIANT_ERROR', 'EXECUTION_ERROR'}
STOP_ERRORS = {'OUTPUT_MISMATCH', 'STATE_INVARIANT_ERROR', 'EXECUTION_ERROR'}
PROFILE_FIELDS = ['max_depth', 'nesting_count', 'parented_interval_ratio', 'containment_pair_count', 'containment_pair_density', 'upper_root_count', 'lower_root_count']
LIMITATIONS = {
    'rollback': 'NOT MEASURABLE WITH CURRENT OBSERVABILITY: success traces do not expose injected failures; separate rollback regression tests are required.',
    'all_prefix_tree_depths': 'NOT MEASURABLE WITH CURRENT OBSERVABILITY: public diagnostics return trace, not every historical tree snapshot. Final profile is measured; dynamic depths would require a state callback on every case.',
    'minimal_branch_coverage': 'NOT MEASURABLE WITH CURRENT OBSERVABILITY: minimal disables trace/counters. Its output is independently recovered, but branch witnesses come from checked only.',
    'universal_correctness': 'Finite cases and same-core replay are not a proof or a second independent Jordan Sorting implementation.',
}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n')
    temp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def frozen_snapshot():
    return {str(p.relative_to(ROOT)): sha(p) for directory in FROZEN for p in sorted((ROOT / directory).rglob('*')) if p.is_file()}


def reserve(path):
    Path(path).mkdir(parents=True, exist_ok=False)


def build_plan():
    plan = []
    counts = {32: 20, 33: 20, 64: 20, 65: 20, 128: 20, 129: 20, 256: 20, 257: 20, 512: 5, 513: 5, 1024: 1, 1025: 1}
    def add(family, n, index=1, sequence=None, reflect=False, prefix=False, source=None):
        cid = f'{family}_n{n}_{index:03d}'
        item = dict(case_id=cid, family=family, n=n, seed=20260916+n*1000+index if family=='incremental_valid' else None,
                    kind='base', base_case_id=None, transform=None, prefix_check=prefix, source=source)
        if sequence is not None:
            item['fixed_sequence'] = sequence
        plan.append(item)
        if reflect:
            plan.append(dict(item, case_id=cid+'_reflect', kind='derived', base_case_id=cid,
                             transform='min(sequence)+max(sequence)-x', prefix_check=False))
    fixed = [[], [1], [1, 2], [2, 1], [3, 2, 1, 4], [1, 2, 3, 4, 6, 7, 0], [1, 2, 3, 4, 6, 7, 0, 5], [2, 3, 1, 7, 6, 4, 5]]
    for i, seq in enumerate(fixed, 1):
        add('fixed', len(seq), i, seq, reflect=len(seq)>=4, prefix=len(seq)>=4,
            source='tests/test_paper_jordan.py; tests/test_paper_jordan_sort.py (endpoint/z1/split cases), plus small-size API boundaries')
    for n, count in counts.items():
        for i in range(1, count+1):
            add('incremental_valid', n, i, reflect=i==1, prefix=i==1 and n in [32,33,128,129])
        if n in [32,33,128,129,512,513]:
            for family in ['flat_valid','nested_valid']:
                add(family,n,reflect=True)
    return sorted(plan, key=lambda c:(c['n'], c['case_id']))


def default_config():
    return {'schema':'ordinary_list_extended_correctness_v1', 'plan':build_plan(), 'batch_seconds':1800,
            'case_seconds':120, 'seed_base':20260916, 'generator_max_attempts_per_step':20,
            'order':'ascending n, then case_id (base before its reflection)',
            'duplicates':'record duplicate_of; do not execute again, do not replace seed or count as new input',
            'large_cases':'n>=1024 only if no prior errors/timeouts and enough batch time; otherwise explicitly not run',
            'prefix_policy':'selected fixed cases and first incremental base at 32,33,128,129; callback checks k in {3,4,n//2,n}; one extra fresh run',
            'resource_scope':'wall time controls resources only; no algorithm timing results, warmups, ratios or repeated calls',
            'sampling_boundary':'heuristic seeded base constructions; reflected cases are derived, not independent random samples'}


def coverage_definitions():
    d = {}
    for value in ['increasing','decreasing']:
        d['orientation.'+value] = 'step3a_insert_pair.orientation == '+value
    for value in ['upper','lower']:
        d['family.'+value] = 'step3a_insert_pair.family == '+value
    for value in ['even','odd']:
        d['end_index.'+value] = 'step3a_insert_pair.iteration parity == '+value
    for value in ['singleton_list','boundary_insertion']:
        d['step3a.'+value] = 'step3a_insert_pair.insertion_mode == '+value
        for direction in ['increasing','decreasing']:
            d[f'step3a.{value}.{direction}'] = d['step3a.'+value]+' and orientation == '+direction
    d.update({
        'step3b.skip':'step3b_split_sibling_list.performed is False',
        'step3b.split':'step3b_split_sibling_list.performed is True',
        'split.left_only':'performed and left_size>0 and right_size==0',
        'split.right_only':'performed and right_size>0 and left_size==0',
        'split.both':'performed and left_size>0 and right_size>0',
        'children.none':'Step3b skipped or acquired side size == 0; new pair has no children before 3b',
        'children.one':'Step3b acquired side size == 1',
        'children.multiple':'Step3b acquired side size > 1',
        'ownership.transfer':'Step3b performed and acquired side size > 0; size is number of transferred pairs',
        'endpoint.mismatch':'Step3c child_pair_id != None and base_anchor_point_id != child_pair_id (second stored point ID equals pair end index)',
        'z1.boundary.predecessor':'step1_find_predecessor.adjusted_for_z1 is True',
        'z1.boundary.successor':'step2_find_successor.adjusted_for_z1 is True',
        'z1.output':'step3c_insert_output_point.adjusted_for_z1 is True',
    })
    for v in ['increasing','decreasing']:
        d['endpoint.mismatch.'+v]=d['endpoint.mismatch']+' and orientation == '+v
        d['z1.output.'+v]=d['z1.output']+' and orientation == '+v
    return d


def extract_coverage(sequence, trace):
    counts = Counter(); witnesses = {}; live = {}; maximum = {'value':0,'event':None}; transferred = 0
    def hit(key,event,**extra):
        counts[key]+=1
        witnesses.setdefault(key, {'iteration':event.get('iteration',3),'execution_mode':'checked','event':event,**extra})
    for e in trace:
        step=e['step']
        if step=='initialize_pair_families':
            live={e['upper_list_id']:1,e['lower_list_id']:1}
        elif step=='step3a_insert_pair':
            hit('orientation.'+e['orientation'],e);hit('family.'+e['family'],e)
            hit('end_index.'+('odd' if e['iteration']%2 else 'even'),e)
            hit('step3a.'+e['insertion_mode'],e);hit('step3a.'+e['insertion_mode']+'.'+e['orientation'],e)
            lid=e['sibling_list_id']
            if e['insertion_mode']=='singleton_list':
                live[lid]=1
            else:
                live[lid]+=1
        elif step=='step3b_split_sibling_list':
            size=0
            if not e['performed']:
                hit('step3b.skip',e)
            else:
                hit('step3b.split',e)
                left,right=e['left_size'],e['right_size']
                assert live.pop(e['input_list_id'])==e['input_size']==left+right
                for side in ['left','right']:
                    if e[side+'_list_id'] is not None:
                        live[e[side+'_list_id']]=e[side+'_size']
                hit('split.'+('both' if left and right else 'left_only' if left else 'right_only'),e)
                size=e[e['acquired_side']+'_size'];transferred+=size
                if size:
                    hit('ownership.transfer',e,transferred_pair_count=size)
            hit('children.'+('none' if size==0 else 'one' if size==1 else 'multiple'),e,child_count=size)
        elif step in ['step1_find_predecessor','step2_find_successor'] and e['adjusted_for_z1']:
            hit('z1.boundary.'+('predecessor' if step.startswith('step1') else 'successor'),e)
        elif step=='step3c_insert_output_point':
            child=e['child_pair_id']
            if child is not None and e['base_anchor_point_id']!=child:
                extra={'child_stored_values':sequence[child-2:child], 'geometric_anchor_value':sequence[e['base_anchor_point_id']-1]}
                hit('endpoint.mismatch',e,**extra);hit('endpoint.mismatch.'+e['orientation'],e,**extra)
            if e['adjusted_for_z1']:
                hit('z1.output',e);hit('z1.output.'+e['orientation'],e)
        size=max(live.values(),default=0)
        if size>maximum['value']:
            maximum={'value':size,'event':e,'iteration':e.get('iteration',3),'execution_mode':'checked'}
    return {'counts':dict(counts),'witnesses':witnesses,'transferred_pairs':transferred,'max_live_sibling_list_length':maximum}


def output_checks(seq, output, expected):
    return {'matches_expected':output==expected, 'length':len(output)==len(seq),
            'elements':Counter(output)==Counter(seq), 'strictly_increasing':all(a<b for a,b in zip(output,output[1:]))}


def outputs_agree(seq, checked, minimal):
    expected=sorted(seq)
    return all(output_checks(seq,checked,expected).values()) and all(output_checks(seq,minimal,expected).values()) and checked==minimal


def evaluate(spec, known, base_sequence=None, checkpoint=lambda r:None):
    """One unique input: certify, then call two fresh APIs. Mockable only in tests."""
    r=dict(spec,status='RUNNING',phase='generation',mode_calls={})
    diagnostics=None
    def save(): checkpoint(r)
    save()
    try:
        if spec['kind']=='derived':
            if base_sequence is None:
                r.update(status='NOT_RUN_DEPENDENCY',reason='base sequence unavailable');return r
            seq=[min(base_sequence)+max(base_sequence)-x for x in base_sequence]
            r['base_sequence_sha256']=sequence_hash(base_sequence)
        elif 'fixed_sequence' in spec:
            seq=list(spec['fixed_sequence'])
        else:
            seq=generate_sequence(spec['family'],spec['n'],seed=spec['seed'])
        r.update(sequence=seq,sequence_sha256=sequence_hash(seq))
        if len(seq)!=spec['n']:
            r.update(status='GENERATION_ERROR',reason='generator returned wrong length');return r
        r['phase']='certification';save()
        cert=oracle(list(seq));r['certification']={k:v for k,v in cert.items() if k!='sorted'}
        if cert.get('valid') is not True or cert.get('distinct_values') is not True or len(set(seq))!=len(seq):
            r.update(status='GENERATION_ERROR',reason='final generated/transformed input is invalid');return r
        if r['sequence_sha256'] in known:
            r.update(status='DUPLICATE',duplicate_of=known[r['sequence_sha256']]);return r
        expected=sorted(seq);r['expected_sha256']=sequence_hash(expected)
        r['phase']='checked';r['mode_calls']['checked']='STARTED';save()
        diagnostics=paper_jordan_diagnostics_valid(list(seq))
        checked=diagnostics['output'];checks=output_checks(seq,checked,expected)
        r['checked']={'checks':checks,'output_sha256':sequence_hash(checked),'processed_count':diagnostics['processed_count'],'invariants_valid':diagnostics['invariants_valid']}
        r['mode_calls']['checked']='COMPLETED'
        if not all(checks.values()):
            r.update(status='OUTPUT_MISMATCH',actual_output=checked);return r
        if diagnostics['processed_count']!=len(seq) or diagnostics['invariants_valid'] is not True:
            r.update(status='STATE_INVARIANT_ERROR');return r
        r['checked']['passed']=True;r['metrics']=diagnostics['metrics']
        r['phase']='minimal';r['mode_calls']['minimal']='STARTED';save()
        minimal=paper_jordan_sort_valid(list(seq),execution_mode='minimal')
        r['mode_calls']['minimal']='COMPLETED'
        r['minimal']={'checks':output_checks(seq,minimal,expected),'output_sha256':sequence_hash(minimal)}
        r['modes_equal']=checked==minimal
        if not outputs_agree(seq,checked,minimal):
            r.update(status='OUTPUT_MISMATCH',actual_output=minimal);return r
        r['minimal']['passed']=True
        r['phase']='coverage';save()
        r['coverage']=extract_coverage(seq,diagnostics['trace'])
        assert r['coverage']['transferred_pairs']==r['metrics']['split_items_transferred']
        r['structure']=structure_profile(seq,oracle_result=cert)
        r['prefix_snapshots']=[]
        if spec['prefix_check'] and len(seq)>=3:
            r['phase']='prefix';r['mode_calls']['prefix']='STARTED';save()
            selected={3,4,len(seq)//2,len(seq)}
            def check_prefix(state):
                k=state.processed_count
                if k in selected:
                    actual=state.partial_order.to_list();expected_prefix=sorted(seq[:k])
                    if actual!=expected_prefix:
                        raise AssertionError(f'prefix mismatch at {k}: {actual}')
                    r['prefix_snapshots'].append({'processed_count':k,'output':actual,'point_ids':state.partial_order.to_point_ids(),'passed':True})
            _run_paper_jordan_valid(list(seq),invariant_callback=check_prefix)
            r['mode_calls']['prefix']='COMPLETED'
        r.update(status='PASS',phase='complete')
    except Exception as exc:
        phase=r['phase']
        status='RESOURCE_ERROR' if isinstance(exc,MemoryError) else 'GENERATION_ERROR' if phase=='generation' else 'CERTIFICATION_ERROR' if phase=='certification' else 'STATE_INVARIANT_ERROR' if isinstance(exc,(RuntimeError,AssertionError)) and phase in ['checked','prefix'] else 'EXECUTION_ERROR'
        r.update(status=status,error=repr(exc),error_traceback=traceback.format_exc())
    finally:
        if r['status'] in STOP_ERRORS and diagnostics is not None:
            r['failure_trace_tail']=diagnostics['trace'][-21:]
        save()
    return r


def worker(request_path, result_path):
    request=read_json(request_path)
    result=evaluate(request['spec'],request['known'],request.get('base_sequence'),lambda r:write_json(result_path,r))
    write_json(result_path,result)


def bounded_case(spec,known,base,path,seconds):
    request=path.with_suffix('.request.json');write_json(request,{'spec':spec,'known':known,'base_sequence':base})
    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker',str(request),str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        stdout,stderr=process.communicate(timeout=seconds)
        result=read_json(path) if path.exists() else dict(spec,status='EXECUTION_ERROR',mode_calls={})
        if process.returncode!=0:
            result.update(status='EXECUTION_ERROR',worker_returncode=process.returncode,error=stderr[-6000:])
    except subprocess.TimeoutExpired:
        process.kill();process.communicate()
        result=read_json(path) if path.exists() else dict(spec,mode_calls={})
        result.update(status='TIMEOUT',reason='per-case or remaining batch wall budget expired')
    finally:
        request.unlink(missing_ok=True)
    write_json(path,result)
    return result


def historical_report():
    rows=list(csv.DictReader((HISTORY/'case_audit.csv').open()))
    manifest=read_json(HISTORY/'manifest.json');config=read_json(HISTORY/'config.json')
    assert len(rows)==manifest['row_counts']['case_audit']==60
    for entry in manifest['files'].values():
        assert sha(HISTORY/entry['path'])==entry['sha256']
    hashes=Counter(r['sequence_sha256'] for r in rows)
    evidence={}
    mappings={'step3a.singleton_list':'paper_sibling_lists_created','step3a.boundary_insertion':'paper_sibling_list_insertions','step3b.split':'paper_sibling_list_splits','ownership.transfer':'paper_split_items_transferred','z1.boundary':'paper_z1_boundary_adjustments','z1.output':'paper_z1_output_anchor_adjustments'}
    for label,field in mappings.items():
        positive=[r for r in rows if int(r[field])>0]
        evidence[label]={'status':'OBSERVED' if positive else 'NOT_OBSERVED','field':field,'positive_cases':len(positive),'total':sum(int(r[field]) for r in rows),
                         'witness':{k:positive[0][k] for k in ['case_id','sequence_sha256',field]} if positive else None,'scope':'case-level aggregate, no iteration/subbranch witness'}
    skip=[r for r in rows if int(r['n'])-3-int(r['paper_sibling_list_splits'])>0]
    evidence['step3b.skip']={'status':'OBSERVED' if skip else 'NOT_OBSERVED','positive_cases':len(skip),'definition':'n-3 minus successful split count; one 3b event per completed iteration','witness':{k:skip[0][k] for k in ['case_id','sequence_sha256','n','paper_sibling_list_splits']} if skip else None}
    evidence['odd_length']={'status':'NOT_OBSERVED','definition':'n % 2 == 1','positive_cases':sum(int(r['n'])%2 for r in rows)}
    unknown=['orientation','family/orientation intersections','split sides single/both nonempty','children zero/one/multiple','endpoint mismatch','z1 adjustment direction','maximum live sibling-list length']
    return {'source_commit':manifest['source_commit'],'config':config,'recorded_cases':len(rows),'recorded_unique_hashes':len(hashes),'duplicate_hashes':{k:v for k,v in hashes.items() if v>1},
            'input_hash_scope':'hashes recorded in manifest-verified case_audit; historical input bytes not re-generated in this task',
            'group_counts':dict(Counter(f"{r['n']}/{r['family']}" for r in rows)), 'categories':dict(Counter(r['category'] for r in rows)),
            'structure_ranges':{k:{'min':min(float(r[k]) for r in rows),'max':max(float(r[k]) for r in rows)} for k in PROFILE_FIELDS},
            'group_structure_ranges':{key:{k:[min(float(r[k]) for r in rows if f"{r['n']}/{r['family']}"==key),max(float(r[k]) for r in rows if f"{r['n']}/{r['family']}"==key)] for k in PROFILE_FIELDS} for key in sorted({f"{r['n']}/{r['family']}" for r in rows})},
            'branch_evidence':evidence,'insufficient_fields':{k:'INSUFFICIENT_ARCHIVED_FIELDS; no historical trace rerun' for k in unknown},
            'hash_to_case':{r['sequence_sha256']:'historical:'+r['case_id'] for r in rows}}


def summarize(rows):
    statuses=Counter(r['status'] for r in rows);passed=[r for r in rows if r['status']=='PASS']
    attempted=[r for r in rows if not r['status'].startswith('NOT_RUN')]
    return {'planned':len(rows),'attempted':len(attempted),'completed':sum(r['status']=='PASS' or r['status'] in ERRORS or r['status'] in {'DUPLICATE','RESOURCE_ERROR'} for r in rows),
            'passed':len(passed),'failed':sum(statuses[s] for s in ERRORS),'timed_out':statuses['TIMEOUT'],
            'not_run':sum(v for k,v in statuses.items() if k.startswith('NOT_RUN')),'duplicates':statuses['DUPLICATE'],'resource_errors':statuses['RESOURCE_ERROR'],'statuses':dict(statuses),
            'generated_unique_inputs':len({r['sequence_sha256'] for r in rows if 'sequence_sha256' in r}),
            'new_unique_inputs_executed':len({r['sequence_sha256'] for r in rows if r.get('mode_calls')}),
            'passed_by_kind':dict(Counter(r['kind'] for r in passed)),
            'passed_by_family':dict(Counter(r['family'] for r in passed)),
            'mode_calls_started':{m:sum(m in r.get('mode_calls',{}) for r in rows) for m in ['checked','minimal','prefix']},
            'mode_calls_completed':{m:sum(r.get('mode_calls',{}).get(m)=='COMPLETED' for r in rows) for m in ['checked','minimal','prefix']},
            'mode_output_passes':{m:sum(r.get(m,{}).get('passed',False) for r in rows) for m in ['checked','minimal']},
            'max_passed_n':max((r['n'] for r in passed),default=None),
            'by_n':{str(n):dict(Counter(r['status'] for r in rows if r['n']==n)) for n in sorted({r['n'] for r in rows})},
            'prefix_snapshots_passed':sum(len(r.get('prefix_snapshots',[])) for r in passed),
            'count_semantics':'completed excludes TIMEOUT and NOT_RUN; duplicate certification is completed but not a new core execution; calls count top-level APIs, not internal deterministic replay'}


def merge_coverage(rows):
    result={k:{'definition':v,'event_count':0,'case_count':0,'witness':None,'status':'NOT_OBSERVED'} for k,v in coverage_definitions().items()}
    passed=[r for r in rows if r['status']=='PASS']
    for r in passed:
        c=r['coverage']
        for key,count in c['counts'].items():
            if count and key not in c['witnesses']:
                raise ValueError('coverage count without witness: '+key)
            dest=result[key];dest['event_count']+=count;dest['case_count']+=int(count>0)
            if count and dest['witness'] is None:
                dest['witness']={'case_id':r['case_id'],'sequence_sha256':r['sequence_sha256'],**c['witnesses'][key]};dest['status']='OBSERVED'
    ranges={}
    for field in PROFILE_FIELDS:
        if passed:
            lo=min(passed,key=lambda r:r['structure'][field]);hi=max(passed,key=lambda r:r['structure'][field])
            ranges[field]={'min':lo['structure'][field],'max':hi['structure'][field],'min_case':lo['case_id'],'max_case':hi['case_id']}
    return {'branches':result,'structure_ranges':ranges,'categories':dict(Counter(r['structure']['category'] for r in passed)),
            'max_sibling_list':max(({'case_id':r['case_id'],'sequence_sha256':r['sequence_sha256'],**r['coverage']['max_live_sibling_list_length']} for r in passed),key=lambda x:x['value'],default=None),
            'sibling_length_definition':'reconstruct live list sizes from initialization, 3a singleton/boundary insertion and 3b retirement/output sizes; maximum across these stages',
            'limitations':LIMITATIONS}


def run(output, batch_seconds=1800, case_seconds=120):
    # Refuse ambiguous core versions before reserving any evidence directory.
    if git('diff','HEAD','--','src','experiments/audit_generator_coverage.py','experiments/validate_paper_algorithm.py'):
        raise RuntimeError('uncommitted validation/core dependencies; stop')
    if batch_seconds<=0 or case_seconds<=0:
        raise ValueError('resource limits must be positive')
    reserve(output);output=Path(output);(output/'cases').mkdir()
    config=default_config();config.update(batch_seconds=batch_seconds,case_seconds=case_seconds);write_json(output/'config.json',config)
    frozen=frozen_snapshot();write_json(output/'frozen_before.json',frozen)
    history=historical_report();write_json(output/'historical_coverage.json',history)
    dependencies=sorted(list((ROOT/'src').glob('*.py'))+[ROOT/'experiments/audit_generator_coverage.py',ROOT/'experiments/validate_paper_algorithm.py',ROOT/'experiments/validate_week12_formal_sorting_outputs.py',Path(__file__).resolve(),ROOT/'tests/test_validate_ordinary_list_extended.py'])
    source={str(p.relative_to(ROOT)):{'sha256':sha(p),'matches_HEAD':subprocess.check_output(['git','show','HEAD:'+str(p.relative_to(ROOT))],cwd=ROOT)==p.read_bytes() if str(p.relative_to(ROOT)) in git('ls-files').splitlines() else False} for p in dependencies}
    historical_diff=git('diff','--name-only',history['source_commit'],'HEAD','--','src','experiments/audit_generator_coverage.py','experiments/validate_paper_algorithm.py','experiments/validate_week12_formal_sorting_outputs.py')
    manifest={'source_commit':git('rev-parse','HEAD'),'origin_main':git('rev-parse','origin/main'),'historical_source_commit':history['source_commit'],'historical_dependency_diff':historical_diff.splitlines(),
              'git_status_at_start':git('status','--short'),'source_files':source,'uncommitted_tool_boundary':'new tool/tests are content-hashed; HEAD does not contain them',
              'python':sys.version,'started_at_utc':datetime.now(timezone.utc).isoformat()}
    write_json(output/'manifest.json',manifest)
    started=time.monotonic();known=dict(history['hash_to_case']);rows=[];by_id={};stop=False
    try:
        for spec in config['plan']:
            path=output/'cases'/(spec['case_id']+'.json');remaining=config['batch_seconds']-(time.monotonic()-started)
            if stop:
                r=dict(spec,status='NOT_RUN_STOPPED',reason='earlier certified-input output/state/execution failure',mode_calls={})
            elif remaining<1:
                r=dict(spec,status='NOT_RUN_BUDGET',reason='batch budget exhausted',mode_calls={})
            elif spec['n']>=1024 and any(r['status'] in ERRORS or r['status'] in {'TIMEOUT','RESOURCE_ERROR'} for r in rows):
                r=dict(spec,status='NOT_RUN_BUDGET',reason='large-tier eligibility failed after smaller-case error/timeout',mode_calls={})
            else:
                base=by_id.get(spec['base_case_id'],{}).get('sequence')
                r=bounded_case(spec,known,base,path,min(config['case_seconds'],remaining))
            write_json(path,r);rows.append(r);by_id[spec['case_id']]=r
            if r.get('sequence_sha256') and r['status']!='DUPLICATE':known[r['sequence_sha256']]=spec['case_id']
            stop=stop or (r['status'] in STOP_ERRORS and r.get('certification',{}).get('valid') is True)
            print(spec['case_id'],r['status'],flush=True)
            write_json(output/'summary.json',summarize(rows))
    except KeyboardInterrupt:
        raise
    finally:
        summary=summarize(rows);summary['resource_elapsed_seconds']=time.monotonic()-started
        summary['plan_fully_accounted']=len(rows)==len(config['plan']);summary['limitations']=LIMITATIONS
        after=frozen_snapshot();summary['frozen_unchanged']=frozen==after
        write_json(output/'frozen_after.json',after);write_json(output/'summary.json',summary)
        write_json(output/'coverage.json',merge_coverage(rows))
        manifest['finished_at_utc']=datetime.now(timezone.utc).isoformat()
        manifest['source_hashes_unchanged']=all(sha(ROOT/n)==v['sha256'] for n,v in source.items())
        manifest['files']={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='manifest.json'}
        write_json(output/'manifest.json',manifest)
    assert summary['frozen_unchanged'] and manifest['source_hashes_unchanged']
    return 1 if summary['failed'] else 2 if summary['timed_out'] or summary['resource_errors'] or summary['not_run'] or not summary['plan_fully_accounted'] else 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',nargs=2,metavar=('REQUEST','RESULT'))
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--batch-seconds',type=float,default=1800)
    parser.add_argument('--case-seconds',type=float,default=120)
    args=parser.parse_args()
    if args.worker:
        worker(*args.worker);return 0
    if args.plan:
        print(json.dumps(default_config(),indent=2));return 0
    if args.output is None:parser.error('--output is required')
    return run(args.output,args.batch_seconds,args.case_seconds)


if __name__=='__main__':
    sys.exit(main())
