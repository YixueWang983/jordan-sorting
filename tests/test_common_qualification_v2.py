"""Small actual flows and mechanical corruption checks, not the 140-input batch."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'experiments')]
from contextlib import ExitStack
import gzip
import json
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import common_qualification_v2_protocol as protocol
import qualify_common_inputs_v2 as runner
import validate_common_qualification_v2 as checker
import paper_jordan_sort
from common_input_protocol import digest
from committed_records import atomic_json, atomic_bytes, canonical, read_records, run_bounded


class CommonV2Tests(unittest.TestCase):
    def directory(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return Path(temp.name)/'run'

    def fixture_rules(self):
        selected = protocol.frozen_selection()
        selected['cases'] = [c for c in selected['cases'] if c['spec']['n'] == 32 and c['spec']['requested_category'] == 'strict_flat']
        selected['selection_sha256'] = digest(selected['cases'])
        cfg = protocol.plan(); cfg['selection_sha256'] = selected['selection_sha256']
        return selected, cfg

    def scope(self, selected, cfg):
        scope = ExitStack()
        for module in (runner, checker):
            scope.enter_context(patch.object(module, 'frozen_selection', return_value=selected))
            scope.enter_context(patch.object(module, 'plan', return_value=cfg))
        # This small fixture runs uncommitted code with an explicitly mocked
        # source freeze; it is not a qualification archive.
        scope.enter_context(patch.object(checker,'validate_revision'))
        scope.enter_context(patch.object(checker,'SIZES',(32,)))
        scope.enter_context(patch.object(checker,'CATEGORIES',('strict_flat',)))
        return scope

    def fixture(self, output, worker=None, seconds=None):
        selected, cfg = self.fixture_rules(); env = runner.environment(); env['dirty'] = False
        if seconds is not None: cfg['case_seconds'] = seconds
        def in_process(command, directory, budget):
            return runner.qualify_case(runner.read(Path(command[command.index('--worker')+1])), directory)
        with self.scope(selected,cfg), patch.object(runner,'environment',return_value=env), \
             patch.object(runner,'run_bounded',side_effect=worker or in_process):
            result = runner.run(output)
        return selected,cfg,result

    def request(self):
        return dict(schema=protocol.SCHEMA,case='real-small',values=[1,2,3,4,6,7,0,5],backends=list(runner.BACKENDS))

    def test_frozen_selection_identity(self):
        selected = protocol.frozen_selection()
        self.assertEqual(len(selected['cases']),140)
        self.assertEqual(digest(selected['cases']),protocol.SELECTION_SHA256)
        self.assertEqual(len({c['input_sha256'] for c in selected['cases']}),140)

    def test_actual_sync_route_and_fresh_minimal_no_legacy_diagnostics(self):
        out = self.directory(); request = self.request()
        with patch.object(paper_jordan_sort,'paper_jordan_diagnostics_valid',side_effect=AssertionError('legacy path')):
            self.assertEqual(runner.qualify_case(request,out),0)
        rows = checker.validate_job(out,request,digest(request['values']),passing=True)
        self.assertEqual([len(r['initializations']) for r in rows],[3,1,3,1])
        self.assertTrue(any(e.get('performed') for e in rows[2]['final']['trace']))

    def test_real_fixture_independent_reconstruction(self):
        out = self.directory(); selected,cfg,passed = self.fixture(out)
        self.assertTrue(passed)
        with self.scope(selected,cfg): report = checker.validate(out)
        self.assertEqual(report['status_counts'],{'PASS':2})
        self.assertEqual(report['completed_modes'],{'synchronous_v2':4,'fresh_minimal':4})
        self.assertEqual(report['per_backend_initializations'],dict.fromkeys(runner.BACKENDS,8))
        self.assertFalse(report['performance_eligible'])

    def test_incomplete_report_rejected_before_minimal(self):
        original = runner.run_synchronous_qualification
        for value in (True,5.0,0):
            def broken(*a,**kw):
                state,report = original(*a,**kw); report['prefix_comparisons'] = value; return state,report
            out = self.directory()
            with patch.object(runner,'run_synchronous_qualification',side_effect=broken), patch.object(runner,'paper_jordan_sort_valid') as minimal:
                self.assertEqual(runner.qualify_case(self.request(),out),2); minimal.assert_not_called()
            self.assertEqual(read_records(out)[0]['status'],'ERROR')

    def test_wrong_actual_backend_configuration_rejected(self):
        original = runner.backend_spec
        def wrong(name): return original('ordinary_list')
        out = self.directory()
        with patch.object(runner,'backend_spec',side_effect=wrong):
            self.assertEqual(runner.qualify_case(self.request(),out),2)
        self.assertEqual([r['status'] for r in read_records(out)],['PASS','PASS','ERROR'])

    def test_wrong_output_and_serialization_error_retained(self):
        original = runner.evaluate
        def wrong(values,name,mode,out,action):
            row = original(values,name,mode,out,action)
            if mode == 'fresh_minimal': row['output']=[999]
            return row
        out = self.directory()
        with patch.object(runner,'evaluate',side_effect=wrong): self.assertEqual(runner.qualify_case(self.request(),out),2)
        self.assertEqual(read_records(out)[-1]['output'],[999])
        out = self.directory()
        with patch.object(runner,'evaluate',return_value={'output':object()}): self.assertEqual(runner.qualify_case(self.request(),out),2)
        self.assertEqual(read_records(out)[0]['error']['type'],'SerializationError')

    def test_worker_exception_stops_and_archive_rebuilds(self):
        out = self.directory(); original=runner.evaluate
        def fail(values,name,mode,out,action):
            if mode == 'fresh_minimal': raise RuntimeError('injected')
            return original(values,name,mode,out,action)
        def worker(command,directory,budget):
            request=runner.read(Path(command[command.index('--worker')+1]))
            with patch.object(runner,'evaluate',side_effect=fail): code=runner.qualify_case(request,directory)
            atomic_json(directory/'failure.json',dict(status='WORKER_ERROR',accepted=False,performance_eligible=False,
                committed_records=len(read_records(directory)),current=runner.read(directory/'progress.json')))
            return code
        selected,cfg,passed=self.fixture(out,worker)
        self.assertFalse(passed)
        with self.scope(selected,cfg): report=checker.validate(out)
        self.assertEqual(report['status_counts'],{'ERROR':1,'NOT_RUN':1})
        self.assertEqual(report['completed_modes'],{'synchronous_v2':1})

    def test_zero_exit_with_missing_records_is_not_pass(self):
        def fake(command,directory,budget):
            directory.mkdir(); atomic_json(directory/'progress.json',dict(status='COMPLETE',committed_records=4)); return 0
        out=self.directory(); selected,cfg,passed=self.fixture(out,fake)
        self.assertFalse(passed)
        with self.scope(selected,cfg): self.assertFalse(checker.validate(out)['all_selected_qualified'])

    def test_real_process_timeout_recovers_completed_sync(self):
        out=self.directory(); script=out.parent/'worker.py'
        script.write_text('''import sys,time
from pathlib import Path
sys.path[:0]=[str(Path(sys.argv[1])/'experiments'),str(Path(sys.argv[1])/'src')]
import qualify_common_inputs_v2 as r
real=r.evaluate
def evaluate(values,name,mode,out,action):
 if mode=='fresh_minimal':time.sleep(30)
 return real(values,name,mode,out,action)
r.evaluate=evaluate
raise SystemExit(r.qualify_case(dict(case='timeout',values=list(range(1,9)),backends=list(r.BACKENDS)),Path(sys.argv[2])))
''')
        self.assertEqual(run_bounded([sys.executable,str(script),str(ROOT),str(out)],out,2),2)
        rows=read_records(out); self.assertEqual(len(rows),1); self.assertEqual(rows[0]['status'],'PASS')
        failure=runner.read(out/'failure.json')
        self.assertEqual(failure['status'],'RESOURCE_TIMEOUT'); self.assertEqual(failure['current']['mode'],'fresh_minimal')
        self.assertFalse(failure['accepted'])

    def test_full_timeout_archive_retains_completed_mode_and_stops(self):
        out=self.directory(); script=out.parent/'worker.py'
        script.write_text("""import sys,time,json
from pathlib import Path
sys.path[:0]=[str(Path(sys.argv[1])/'experiments'),str(Path(sys.argv[1])/'src')]
import qualify_common_inputs_v2 as r
real=r.evaluate
def evaluate(values,name,mode,out,action):
 if mode=='fresh_minimal':time.sleep(30)
 return real(values,name,mode,out,action)
r.evaluate=evaluate
raise SystemExit(r.qualify_case(json.loads(Path(sys.argv[2]).read_text()),Path(sys.argv[3])))
""")
        def worker(command,directory,budget):
            request=command[command.index('--worker')+1]
            return run_bounded([sys.executable,str(script),str(ROOT),request,str(directory)],directory,budget)
        selected,cfg,passed=self.fixture(out,worker,seconds=2)
        self.assertFalse(passed)
        with self.scope(selected,cfg):report=checker.validate(out)
        self.assertEqual(report['status_counts'],{'TIMEOUT':1,'NOT_RUN':1})
        self.assertEqual(report['completed_modes'],{'synchronous_v2':1})

    def test_invented_source_revision_rejected(self):
        env=runner.environment();env['head']='0'*40
        with self.assertRaises(ValueError):checker.validate_revision(env)

    def test_resealed_tampering_rejected(self):
        original=self.directory(); selected,cfg,_=self.fixture(original)
        cid=selected['cases'][0]['spec']['case']
        for kind in ('environment','float-count','missing-mode','configuration','prefix-output','history','input','summary','extra-directory','trace'):
            with self.subTest(kind=kind):
                out=self.directory(); shutil.copytree(original,out)
                if kind=='environment':
                    value=runner.read(out/'environment.json'); del value['hardware']; atomic_json(out/'environment.json',value)
                elif kind=='missing-mode': (out/'jobs'/cid/'records/000003.json.gz').unlink()
                elif kind=='extra-directory': (out/'extra').mkdir()
                elif kind=='input':
                    value=runner.read(out/'selected.json');value['cases'][0]['values'].reverse();atomic_json(out/'selected.json',value)
                elif kind=='summary':
                    value=runner.read(out/'summary.json');value['performance_eligible']=True;atomic_json(out/'summary.json',value)
                else:
                    path=out/'jobs'/cid/'records/000000.json.gz';row=json.loads(gzip.decompress(path.read_bytes()))
                    if kind=='float-count':row['report']['initialized_instances']=3.0
                    elif kind=='configuration':row['initializations'][0]['policy']='minimal'
                    elif kind=='prefix-output':row['prefixes'][0]['output_sha256']='0'*64
                    elif kind=='history':row['report']['history_work']['removed_points']+=1
                    elif kind=='trace':row['final']['trace'].pop()
                    atomic_bytes(path,gzip.compress(canonical(row),mtime=0))
                runner.seal(out)
                with self.scope(selected,cfg), self.assertRaises((ValueError,KeyError,FileNotFoundError)): checker.validate(out)

    def test_optimization_guard_before_worker_or_output(self):
        for script in ('qualify_common_inputs_v2.py','validate_common_qualification_v2.py'):
            for flag in ('-O','-OO'):
                result=subprocess.run([sys.executable,flag,str(ROOT/'experiments'/script),'--help'],capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0);self.assertIn('optimization level 0',result.stderr)


if __name__ == '__main__': unittest.main()
