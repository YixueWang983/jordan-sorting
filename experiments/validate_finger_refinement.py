"""Fixed, bounded representation/locality evidence; no timing or qualification.

Uses the independent ghost checks in tests/finger_refinement_model.py alongside
original production execution. Failure stops the batch; no replacements/retries.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Refinement evidence requires optimization level 0')
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests'), str(ROOT/'experiments')]
from committed_records import atomic_json, commit_record, run_bounded
from finger_refinement_model import check_run
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
from oracle import oracle
from paper_execution_policy import MINIMAL_POLICY
from sibling_backend_contract import SiblingBackendSpec
from validate_finger_middle_splits import values_for


def cases():
    for n in range(3,8):
        for values in itertools.permutations(range(n)):
            if oracle(values)['valid']:
                yield f'permutation/{n}', list(values)
    for index, base in enumerate(([1,2,3,4,6,7,0,5], [3,2,1,4,5])):
        for mirror in (False,True):
            yield f'fixed/{index}/mirror={mirror}', [-x for x in base] if mirror else base
    for n,k,mirror in itertools.product((128,129),(3,7,19),(False,True)):
        yield f'middle/{n}/{k}/mirror={mirror}', values_for(n,k,mirror)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    sources = sorted((ROOT/'src').glob('*.py')) + [Path(__file__).resolve(),
        ROOT/'tests/finger_refinement_model.py', ROOT/'tests/test_finger_refinement.py',
        ROOT/'experiments/validate_finger_middle_splits.py', ROOT/'experiments/committed_records.py']
    hashes = lambda: {str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sources}
    before = hashes()
    plan = {'archive_schema':'finger_refinement_records_v2', 'scope':'bounded_representation_locality_not_timing',
            'selection':'all legal permutations n=3..7; two fixed cases and mirrors; n=128/129 k=3/7/19 and mirrors',
            'execution_policy':'minimal', 'tree_options':{'detailed_work':False},
            'original_runs_per_case':2, 'replay':False, 'budget_seconds':180,
            'retry_or_replacement':False, 'performance_eligible':False,
            'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),
            'python':sys.version, 'platform':platform.platform(), 'python_optimize':sys.flags.optimize,
            'source_sha256':before}
    atomic_json(output/'plan.json',plan)
    count=0; unique=set(); totals={b:Counter() for b in ('ordinary','tree_off')}
    label='before_first_case'; values=None
    try:
        for label,values in cases():
            atomic_json(output/'progress.json',{'status':'RUNNING','record_index':count,
                'case':label,'input_sha256':digest(json.dumps(values).encode()),'values':values})
            if not oracle(values)['valid']:
                raise AssertionError('fixed input is not qualified')
            row={'case':label,'values':values,'input_sha256':digest(json.dumps(values).encode()),'runs':{}}
            for name,backend in (('ordinary','ordinary_list'),('tree_off',SiblingBackendSpec(Tree,(('detailed_work',False),)))):
                _, counts = check_run(values,backend,MINIMAL_POLICY)
                row['runs'][name]=counts
                totals[name].update(counts)
            commit_record(output,count,row)
            count+=1;unique.add(row['input_sha256'])
        if hashes()!=before:
            raise RuntimeError('sources changed during validation')
        summary={'accepted':True,'scope':plan['scope'],'case_runs':count,'distinct_input_hashes':len(unique),
                 'original_runs':2*count,'totals':{k:dict(v) for k,v in totals.items()},
                 'performance_eligible':False,'formal_proof_certified':False}
        atomic_json(output/'summary.json',summary)
        atomic_json(output/'progress.json',{'status':'COMPLETE','committed_records':count})
        print(json.dumps(summary))
    except Exception:
        atomic_json(output/'failure.json',{'accepted':False,'case':label,'values':values,
            'completed_cases':count,'performance_eligible':False})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        run(args.output)
        return 0
    if args.output.exists():
        raise FileExistsError(args.output)
    return run_bounded([sys.executable,__file__,'--worker','--output',str(args.output)],args.output,180)


if __name__=='__main__':
    raise SystemExit(main())
