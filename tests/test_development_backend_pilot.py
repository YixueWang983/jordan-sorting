"""Pilot mechanics/boundary tests. Test archives are never performance data."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
import development_backend_pilot as runner
from validate_development_backend_pilot import validate
from committed_records import atomic_json,atomic_bytes,read_records,canonical,run_bounded
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
import paper_jordan as core
from partial_sorted_list import SortedOrderList
import gzip


def fake_preflight(values,name,expected):
    return {'status':'PASS','processed_count':len(values),'same_backend_replay':True,
            'output':expected,'output_diagnostic':None,'error':None}


def fake_trial(values,name,expected,batch_size):
    return {'status':'PASS','elapsed_ns':100*batch_size,'completed_calls':batch_size,
            'outputs':[{'output':expected,'output_diagnostic':None} for _ in range(batch_size)],'error':None}


class DevelopmentPilotTests(unittest.TestCase):
    def directory(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        return Path(temp.name)/'pilot'

    def fixture(self,out):
        with patch.object(runner,'preflight',fake_preflight),patch.object(runner,'trial_batch',fake_trial):
            self.assertTrue(runner.run(out))

    def reseal(self,out):
        files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='manifest.json')
        atomic_json(out/'manifest.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

    def test_real_public_calls_fresh_unobserved_trees_inside_timer_checks_outside(self):
        active=False;events=[];instances=[]
        init=Tree.__init__;recover=SortedOrderList.to_list;capture=runner.capture_output
        def clock():
            nonlocal active
            active=not active;events.append('start' if active else 'stop');return len(events)
        def initialize(b,*a,**kw):
            self.assertTrue(active);init(b,*a,**kw);instances.append(b);events.append('init')
        def output(order):
            self.assertTrue(active);events.append('output');return recover(order)
        def check(value):
            self.assertFalse(active);return capture(value)
        with patch.object(Tree,'__init__',initialize),patch.object(SortedOrderList,'to_list',output),patch.object(runner,'capture_output',check):
            row=runner.trial_batch([1,2,3,4,6,7,0,5],'heterogeneous_finger',list(range(8)),3,clock)
        self.assertEqual(row['status'],'PASS')
        self.assertEqual(events,['start','init','output','init','output','init','output','stop'])
        self.assertEqual(len({id(b._nodes) for b in instances}),3)
        self.assertTrue(all(not b.detailed_work and b.work.buckets is None for b in instances))

    def test_wrong_output_is_retained_after_clock_closes(self):
        ticks=iter((100,110))
        with patch.object(runner,'paper_jordan_sort_valid',return_value=[99]):
            row=runner.trial_batch([1,2,3],'ordinary_list',[1,2,3],1,lambda:next(ticks))
        self.assertEqual(row['status'],'ERROR');self.assertEqual(row['elapsed_ns'],10)
        self.assertEqual(row['outputs'][0]['output'],[99])

    def test_fixed_schedule_and_independent_reconstruction(self):
        out=self.directory();self.fixture(out);report=validate(out)
        self.assertEqual(report['sample_batches'],144);self.assertEqual(report['sample_calls'],1008)
        self.assertEqual(report['rows'],192);self.assertFalse(report['performance_eligible'])
        rows=read_records(out)
        self.assertTrue(all(r['kind']=='preflight' for r in rows[:16]))
        self.assertTrue(all(r['kind']!='preflight' for r in rows[16:]))

    def test_preflight_boolean_count_stops_before_warmup(self):
        out=self.directory();values=runner.inputs()[0]['values']
        bad={'output':sorted(values),'processed_count':True,'invariants_valid':True,
             'backend_identity':runner.identity('ordinary_list')}
        with patch.object(runner,'paper_jordan_diagnostics_valid',return_value=bad),patch.object(runner,'trial_batch') as trial:
            self.assertFalse(runner.run(out));trial.assert_not_called()
        rows=read_records(out);self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['status'],'ERROR')
        self.assertEqual(rows[0]['output'],sorted(values))
        self.assertFalse(validate(out)['completed_successfully'])

    def test_warmup_failure_stops_and_retains_committed_preflight(self):
        out=self.directory()
        with patch.object(runner,'preflight',fake_preflight),patch.object(runner,'paper_jordan_sort_valid',return_value=[99]):
            self.assertFalse(runner.run(out))
        rows=read_records(out)
        self.assertEqual(len(rows),17);self.assertEqual(rows[-1]['outputs'][0]['output'],[99])
        self.assertEqual(validate(out)['committed_records_recovered'],17)

    def test_validator_rejects_resealed_protocol_environment_rows_and_summary(self):
        source=self.directory();self.fixture(source)
        mutations=('protocol','environment','elapsed','boolean_count','missing_row','wrong_output','summary','extra_directory')
        for kind in mutations:
            out=self.directory();shutil.copytree(source,out)
            with self.subTest(kind=kind):
                if kind=='protocol':
                    doc=json.loads((out/'config.json').read_text());doc['protocol']['tree_detailed_work']=True;atomic_json(out/'config.json',doc)
                elif kind=='environment':
                    doc=json.loads((out/'environment.json').read_text());del doc['gc_enabled'];atomic_json(out/'environment.json',doc)
                elif kind=='summary':
                    doc=json.loads((out/'summary.json').read_text());doc['sample_calls']+=1;atomic_json(out/'summary.json',doc)
                elif kind=='extra_directory':(out/'extra').mkdir()
                elif kind=='missing_row':(out/'records/000191.json.gz').unlink()
                else:
                    rows=read_records(out);row=rows[-1]
                    if kind=='elapsed':row['elapsed_ns']=0
                    elif kind=='boolean_count':row['completed_calls']=True
                    elif kind=='wrong_output':row['outputs'][0]['output'][0]=False
                    atomic_bytes(out/'records/000191.json.gz',gzip.compress(canonical(row),mtime=0))
                self.reseal(out)
                with self.assertRaises(ValueError):validate(out)

    def test_optimized_pilot_entrypoints_reject_before_outputs(self):
        for filename in ('development_backend_pilot.py','validate_development_backend_pilot.py'):
            result=subprocess.run([sys.executable,'-O',str(ROOT/'experiments'/filename),'--help'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('optimization level 0',result.stderr)

    def test_real_pilot_worker_timeout_recovers_committed_preflight(self):
        out=self.directory();worker=out.parent/'worker.py'
        worker.write_text('''import sys,time
from pathlib import Path
sys.path[:0]=[str(Path(sys.argv[1])/'experiments'),str(Path(sys.argv[1])/'tests')]
import development_backend_pilot as runner
from test_development_backend_pilot import fake_preflight
runner.preflight=fake_preflight  # Mechanical timeout test, not sorting evidence.
def blocked(*args):time.sleep(30)
runner.trial_batch=blocked
runner.run(Path(sys.argv[2]))
''')
        self.assertEqual(run_bounded([sys.executable,str(worker),str(ROOT),str(out)],out,2),2)
        report=validate(out)
        self.assertFalse(report['completed_successfully'])
        self.assertEqual(report['committed_records_recovered'],16)
        self.assertEqual(report['current']['action']['kind'],'warmup')


if __name__=='__main__':unittest.main()
