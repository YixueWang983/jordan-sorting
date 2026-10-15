"""One fixed diagnostic profile after qualification timeout; not performance data.

Exactly n=64 ascending, both backends, checked then minimal, one call each.
Whole worker budget 60 seconds. No retries, input selection or code changes.
"""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Profiling evidence requires optimization level 0')
import argparse
import cProfile
import hashlib
import pstats
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'experiments'))
from common_input_protocol import source_identity, digest
from committed_records import atomic_json, commit_record, run_bounded
from matched_backend_fixture import backend_spec, identity
from paper_jordan_sort import paper_jordan_diagnostics_valid, paper_jordan_sort_valid


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    before = source_identity(); values = list(range(1,65))
    atomic_json(output/'plan.json', dict(n=64, values=values, input_sha256=digest(values),
        backends=['ordinary_list','heterogeneous_finger'], modes=['checked','minimal'], calls_per_cell=1,
        budget_seconds=60, purpose='locate qualification audit overhead; profiler-perturbed, not matched timing',
        performance_eligible=False, source_sha256=before,
        profile_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    index = 0
    for name in ('ordinary_list','heterogeneous_finger'):
        for mode in ('checked','minimal'):
            atomic_json(output/'progress.json', dict(backend=name, mode=mode))
            profiler = cProfile.Profile()
            spec = backend_spec(name)
            profiler.enable()
            try:
                result = (paper_jordan_diagnostics_valid(values, backend=spec) if mode == 'checked' else
                          paper_jordan_sort_valid(values, 'minimal', backend=spec))
            finally:
                profiler.disable()
            actual = result['output'] if mode == 'checked' else result
            if actual != values:
                raise ValueError('external output mismatch')
            entries = []
            for (filename,line,function), (primitive,total,self_seconds,cumulative,callers) in pstats.Stats(profiler).stats.items():
                path = Path(filename)
                label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else filename
                entries.append(dict(file=label,line=line,function=function,primitive_calls=primitive,
                    total_calls=total,self_seconds=self_seconds,cumulative_seconds=cumulative))
            entries.sort(key=lambda r:(-r['cumulative_seconds'],r['file'],r['line']))
            commit_record(output,index,dict(backend=name,mode=mode,backend_identity=identity(name),
                output=actual,output_verified=True,performance_eligible=False,functions=entries))
            index += 1
    if source_identity() != before:
        raise RuntimeError('profile source changed')
    atomic_json(output/'summary.json', dict(calls=4, source_unchanged=True, performance_eligible=False,
        limitation='cumulative times overlap; profiler overhead changes timings; no extrapolated 513 duration or causal explanation of pilot ratio'))
    return 0


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    if args.worker: raise SystemExit(run(args.output))
    raise SystemExit(run_bounded([sys.executable,__file__,'--worker','--output',str(args.output)], args.output,60))
