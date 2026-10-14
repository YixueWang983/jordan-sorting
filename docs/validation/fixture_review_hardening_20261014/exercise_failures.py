"""Named fault injection using the full checkout; not backend correctness evidence."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

if sys.flags.optimize != 0:
    raise RuntimeError('Evidence checks require optimization level 0; disable -O/-OO/PYTHONOPTIMIZE')

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'experiments'),str(ROOT/'src')]
import matched_backend_fixture as runner
from validate_matched_backend_fixture import validate


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    cycle=[];cycle.append(cycle)
    reports=[]
    for name,value in (('nan',[float('nan')]),('object',[object()]),('cycle',cycle)):
        path=output/name
        with patch.object(runner,'paper_jordan_sort_valid',return_value=value):
            passed=runner.run([[1,2,3]],path)
        if passed: raise RuntimeError('fault accepted')
        reports.append({'injection':name,**validate(path)})
    path=output/'serialization'
    unsafe={'status':'ERROR','output':[object()],'output_diagnostic':None,
            'synthetic_ticks':1,'error':{'type':'Injected','message':'unsafe row'}}
    with patch.object(runner,'trial',return_value=unsafe):
        if runner.run([[1,2,3]],path): raise RuntimeError('serialization fault accepted')
    reports.append({'injection':'serialization',**validate(path)})
    path=output/'qualification_count'
    original=runner.paper_jordan_diagnostics_valid
    def diagnostic(*args,**kwargs):
        result=original(*args,**kwargs);result['processed_count']=0;return result
    with patch.object(runner,'paper_jordan_diagnostics_valid',diagnostic):
        if runner.run([[1,2,3]],path): raise RuntimeError('bad qualification accepted')
    reports.append({'injection':'qualification_count',**validate(path)})
    (output/'report.json').write_text(json.dumps({'python_optimize':sys.flags.optimize,
        'scope':'injected_failures_not_true_backend_validation','cases':reports},indent=2)+'\n')
    print(json.dumps({'faults_retained':len(reports),'all_completed_successfully':False,'performance_eligible':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
