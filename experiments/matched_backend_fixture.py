"""Mechanical matched-run fixture. Synthetic ticks only; formal timing disabled."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Evidence checks require optimization level 0; disable -O/-OO/PYTHONOPTIMIZE')

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
from heterogeneous_finger_backend import HeterogeneousFingerBackend
from oracle import oracle
from paper_jordan_sort import paper_jordan_sort_valid, paper_jordan_diagnostics_valid
from sibling_backend_contract import SiblingBackendSpec, resolve_sibling_backend

SCHEMA='matched_backend_fixture_v2'
BACKENDS=('ordinary_list','heterogeneous_finger')
SOURCE_FILES=tuple(sorted(str(p.relative_to(ROOT)) for p in (ROOT/'src').glob('*.py')))+(
    'experiments/matched_backend_fixture.py','experiments/validate_matched_backend_fixture.py')
PROTOCOL={'stage':'fixture','measurement_kind':'synthetic_ticks','performance_eligible':False,
          'execution_mode':'minimal','audit_execution_mode':'checked','tree_detailed_work':False,
          'warmups':1,'repetitions':2,'max_cases':8,'max_n':64,
          'boundary':'fresh public sort call including initialization and output recovery; external checks outside',
          'order':'alternate first backend by case index plus round index'}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def source_identity():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCE_FILES}


def backend_spec(name):
    if name=='ordinary_list':
        return resolve_sibling_backend(name)
    if name=='heterogeneous_finger':
        return SiblingBackendSpec(HeterogeneousFingerBackend,(('detailed_work',False),))
    raise ValueError('unknown backend')


def identity(name):
    return json.loads(canonical(backend_spec(name).identity))


def describe_atom(value):
    """Bounded built-in diagnostics without invoking arbitrary repr methods."""
    kind=type(value)
    if kind is int:
        return str(value) if value.bit_length()<=512 else f'<int bit_length={value.bit_length()}>'
    if kind in (float,bool,type(None)):
        return repr(value)
    if kind is str:
        return repr(value[:96])[:128]
    if kind in (list,tuple,dict,set,bytes):
        return f'<{kind.__name__} length={len(value)}>'
    return '<'+kind.__name__[:80]+'>'


def output_diagnostic(value):
    sequence=type(value) in (list,tuple)
    return {'python_type':type(value).__name__[:80],
            'length':len(value) if sequence else None,
            'preview':[describe_atom(v) for v in value[:8]] if sequence else [describe_atom(value)],
            'truncated':sequence and len(value)>8}


def capture_output(value):
    if type(value) is list and all(type(x) is int for x in value):
        return {'output':value,'output_diagnostic':None}
    return {'output':None,'output_diagnostic':output_diagnostic(value)}


def error_details(exc,kind=None):
    try:
        message=str(exc)[:512]
    except Exception:
        message='<exception message unavailable>'
    return {'type':kind or type(exc).__name__[:80],'message':message}


def encode_row(base,row):
    """Serialization failures become a final ERROR before any bytes are written.

    Filesystem write/flush errors are deliberately not caught here: no complete
    archive can be promised when the destination itself is no longer writable.
    """
    try:
        return row,canonical(row)+b'\n'
    except (TypeError,ValueError,OverflowError,RecursionError) as exc:
        failed={**base,'status':'ERROR','output':None,
                'output_diagnostic':output_diagnostic(row.get('output')),
                'error':error_details(exc,'SerializationError')}
        if base['kind'] in ('warmup','sample'):
            failed['synthetic_ticks']=row['synthetic_ticks']
        return failed,canonical(failed)+b'\n'


class FixtureClock:
    """Deterministic boundary sentinel, deliberately not a wall clock."""
    def __init__(self): self.value=0
    def __call__(self):
        self.value+=1
        return self.value


def trial(values,name,expected,clock):
    # Constructor and output recovery belong inside the public call, not here.
    spec=backend_spec(name)
    output=None; error=None
    captured={'output':None,'output_diagnostic':None}
    start=clock()
    try:
        output=paper_jordan_sort_valid(values,'minimal',backend=spec)
    except Exception as exc:
        error=error_details(exc)
    finally:
        finish=clock()
    # Output checking is outside the two sentinels, including on failure.
    if error is None:
        captured=capture_output(output)
        if captured['output'] is None or output!=expected:
            error={'type':'OutputMismatch','message':'external output check failed'}
    return {'status':'ERROR' if error else 'PASS',**captured,
            'synthetic_ticks':finish-start,'error':error}


def actions(cases):
    for index,case in enumerate(cases):
        yield {'case':case['case'],'kind':'input','backend':None,'round':None}
        for name in BACKENDS:
            yield {'case':case['case'],'kind':'qualification','backend':name,'round':None}
        for kind,count in (('warmup',PROTOCOL['warmups']),('sample',PROTOCOL['repetitions'])):
            for rep in range(count):
                order=BACKENDS if (index+rep)%2==0 else tuple(reversed(BACKENDS))
                for name in order:
                    yield {'case':case['case'],'kind':kind,'backend':name,'round':rep}


def summarize(rows):
    return {name:{'samples':sum(r['kind']=='sample' and r['backend']==name for r in rows),
                  'passed_samples':sum(r['kind']=='sample' and r['backend']==name and r['status']=='PASS' for r in rows),
                  'sample_synthetic_ticks':sum(r.get('synthetic_ticks',0) for r in rows if r['kind']=='sample' and r['backend']==name)}
            for name in BACKENDS}


def run(cases,output,stage='fixture'):
    if stage!='fixture':
        raise RuntimeError('pilot/formal timing disabled; only mechanical fixture is available')
    if type(cases) is not list or not 1<=len(cases)<=PROTOCOL['max_cases']:
        raise ValueError('fixture requires one to eight inputs')
    if any(type(v) is not list or not 3<=len(v)<=PROTOCOL['max_n'] or
           any(type(x) is not int for x in v) for v in cases):
        raise ValueError('fixture inputs must contain 3..64 integer values')
    if len({digest(v) for v in cases})!=len(cases):
        raise ValueError('duplicate inputs cannot increase the case count')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    source=source_identity()
    inputs=[{'case':f'case-{i:02d}','values':v,'sha256':digest(v)} for i,v in enumerate(cases)]
    config={'schema':SCHEMA,'protocol':PROTOCOL,'inputs':inputs,
            'backends':{name:identity(name) for name in BACKENDS}}
    (output/'config.json').write_bytes(canonical(config)+b'\n')
    environment={'source_sha256':source,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                 'dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),
                 'python':sys.version,'platform':platform.platform(),
                 'python_optimize':sys.flags.optimize,
                 'captured_at':datetime.now(timezone.utc).isoformat(),'measurement_kind':'synthetic_ticks'}
    (output/'environment.json').write_bytes(canonical(environment)+b'\n')
    rows=[]; clock=FixtureClock(); lookup={c['case']:c['values'] for c in inputs}
    with (output/'raw.jsonl').open('wb') as stream:
        for action in actions(inputs):
            values=lookup[action['case']]; expected=sorted(values)
            base={**action,'input_sha256':digest(values),'backend_identity':None if action['backend'] is None else identity(action['backend'])}
            row={**base,'output':None,'output_diagnostic':None,'error':None}
            try:
                if action['kind']=='input':
                    if len(set(values))!=len(values) or not oracle(values)['valid']:
                        raise ValueError('illegal Jordan input; no replacement or deletion permitted')
                    row.update(status='PASS',output=None,error=None)
                elif action['kind']=='qualification':
                    result=paper_jordan_diagnostics_valid(values,backend=backend_spec(action['backend']))
                    if type(result) is not dict:
                        row.update(capture_output(result))
                        raise RuntimeError('qualification returned a non-dictionary result')
                    row.update(capture_output(result.get('output')))
                    if type(result.get('processed_count')) is not int or result['processed_count']!=len(values):
                        raise RuntimeError('qualification processed_count must be an integer equal to input length')
                    if (row['output']!=expected or result['invariants_valid'] is not True or
                        canonical(result['backend_identity'])!=canonical(identity(action['backend']))):
                        raise RuntimeError('qualification output, audit or backend identity mismatch')
                    row.update(status='PASS',output=result['output'],error=None,
                               processed_count=result['processed_count'],same_backend_replay=True)
                else:
                    row.update(trial(values,action['backend'],expected,clock))
            except Exception as exc:
                row.update(status='ERROR',error=error_details(exc))
            row,encoded=encode_row(base,row)
            stream.write(encoded); stream.flush(); rows.append(row)
            if row['status']!='PASS':
                break
    unchanged=source==source_identity()
    passed=rows[-1]['status']=='PASS' and len(rows)==len(list(actions(inputs))) and unchanged
    result={'schema':SCHEMA,'completed_successfully':passed,'source_unchanged':unchanged,
            'performance_eligible':False,'rows':len(rows),'planned_rows':len(list(actions(inputs))),
            'summary':summarize(rows)}
    (output/'summary.json').write_bytes(canonical(result)+b'\n')
    (output/'manifest.json').write_bytes(canonical({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()})+b'\n')
    return passed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--stage',default='fixture',choices=('fixture','pilot','formal'))
    args=p.parse_args()
    try:
        return 0 if run(json.loads(args.inputs.read_text()),args.output,args.stage) else 2
    except OSError as exc:
        print(f'Archive I/O failure; evidence may be incomplete: {exc}',file=sys.stderr)
        return 2


if __name__=='__main__': raise SystemExit(main())
