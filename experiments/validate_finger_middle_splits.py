"""Fixed middle-size split coverage; both parity/direction combinations, no timing."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Evidence checks require optimization level 0; disable -O/-OO/PYTHONOPTIMIZE')

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
from oracle import oracle
from paper_execution_policy import CHECKED_POLICY, MINIMAL_POLICY
from paper_jordan import _run_paper_jordan_state_values,validate_paper_jordan_state
from sibling_backend_contract import SiblingBackendSpec
from validate_heterogeneous_integration import check_geometry
from validate_finger_work_modes import coverage

RESOURCE_SECONDS = 180


def values_for(n,k,mirror):
    m=(n-n%2-6)//2
    values=[x for i in range(m) for x in (4*i,4*i+1)]
    values += [values[-1]+1,4*k-1,4*k-2,values[-1]+2]
    values=[min(values)-2,max(values)+2]+values
    if n%2: values.append(values[-1]+0.5)
    ranks={x:i+1 for i,x in enumerate(sorted(values))}
    values=[ranks[x] for x in values]
    return [n+1-x for x in values] if mirror else values


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    plan=[{'n':n,'k':k,'mirror':mirror} for n in (128,129) for k in (3,7,19) for mirror in (False,True)]
    paths=sorted((ROOT/'src').glob('*.py'))+[Path(__file__).resolve(),ROOT/'experiments/validate_finger_work_modes.py',ROOT/'experiments/validate_heterogeneous_integration.py']
    source=lambda:{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before=source()
    (output/'plan.json').write_text(json.dumps({'scope':'targeted_correctness_only','plan':plan,'source_sha256':before,
        'whole_batch_timeout_seconds':RESOURCE_SECONDS,'retry_or_replacement':False,
        'python_optimize':sys.flags.optimize},indent=2)+'\n')
    records=[]
    for spec in plan:
        values=values_for(**spec); assert oracle(values)['valid']
        row={'spec':spec,'values':values,'input_sha256':hashlib.sha256(repr(values).encode()).hexdigest(),'runs':{}}
        prior={}
        for name,backend in (('ordinary','ordinary_list'),('tree_on',SiblingBackendSpec(Tree,(('detailed_work',True),))),('tree_off',SiblingBackendSpec(Tree,(('detailed_work',False),)))):
            for policy in (CHECKED_POLICY,MINIMAL_POLICY):
                prefixes=[]
                def check(state):
                    assert state.partial_order.to_list()==sorted(values[:state.processed_count])
                    check_geometry(state); state.sibling_backend.validate_invariants()
                    prefixes.append(state.processed_count)
                state=_run_paper_jordan_state_values(values,backend=backend,execution_policy=policy,
                    invariant_callback=check if policy is CHECKED_POLICY else None)
                assert state.partial_order.to_list()==sorted(values)
                check_geometry(state); validate_paper_jordan_state(state)
                view=(state.sibling_backend.logical_snapshot(),state.sibling_backend.audit_snapshot(),
                      state.stage_results,state.backend_work,state.metrics,state.trace)
                if name=='tree_on':prior[policy.name]=view
                elif name=='tree_off':assert view==prior[policy.name]
                record={'output':state.partial_order.to_list(),'prefixes':prefixes,'final_replay_passed':True}
                if policy is CHECKED_POLICY:
                    assert prefixes==list(range(3,len(values)+1))
                    record['coverage']=coverage(state);record['trace']=state.trace
                    sizes=record['coverage']['nonempty_split_sizes']
                    assert any(min(a,b)==spec['k'] for a,b in sizes)
                row['runs'][name+'/'+policy.name]=record
        records.append(row)
        # Persist each completed case before moving on; failures are not filtered.
        with gzip.open(output/f"case-{len(records):02d}.json.gz",'wt') as stream:json.dump(row,stream)
    assert source()==before
    summary={'accepted':True,'inputs':len(records),'original_runs':len(records)*6,'performance_eligible':False,
             'per_checked_configuration':{'prefixes':sum(len(r['runs']['tree_on/checked']['prefixes']) for r in records),
                'nonempty_smaller_sides':[min(a,b) for r in records for a,b in r['runs']['tree_on/checked']['coverage']['nonempty_split_sizes']]}}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=p.parse_args()
    if args.worker:
        run(args.output)
        return 0
    if args.output.exists():
        raise FileExistsError(args.output)
    try:
        result=subprocess.run([sys.executable,__file__,'--worker','--output',str(args.output)],
                              timeout=RESOURCE_SECONDS,check=False)
        if result.returncode==0:
            return 0
        failure={'status':'ERROR','worker_exit_code':result.returncode}
    except subprocess.TimeoutExpired:
        failure={'status':'RESOURCE_TIMEOUT','whole_batch_timeout_seconds':RESOURCE_SECONDS}
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'failure.json').write_text(json.dumps({**failure,'accepted':False,
        'retry_or_replacement':False},indent=2)+'\n')
    return 2


if __name__=='__main__': raise SystemExit(main())
