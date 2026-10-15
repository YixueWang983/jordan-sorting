"""Small real-flow and mechanical fault tests; not the fixed development batch."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
import gzip
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import validate_qualification_refactor as runner
import recheck_qualification_refactor as checker
from common_input_protocol import digest
from committed_records import atomic_json,atomic_bytes,read_records,canonical,run_bounded


class RefactorEvidenceTests(unittest.TestCase):
    def directory(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        return Path(temp.name)/'run'

    def small_plan(self):
        plan=runner.plan(); case=dict(plan['cases'][0],case='test-flat',n=8,values=list(range(1,9)),input_sha256=digest(list(range(1,9))))
        plan['cases']=[case]; return plan

    def fixture(self,output):
        cfg=self.small_plan();env=runner.environment();env['dirty']=False
        def worker(command,directory,budget):
            request=json.loads(Path(command[command.index('--worker')+1]).read_text())
            return runner.run_case(request,directory)
        with patch.object(runner,'plan',return_value=cfg),patch.object(runner,'environment',return_value=env),patch.object(runner,'run_bounded',side_effect=worker):
            self.assertTrue(runner.run(output))
        return cfg

    def test_raw_comparison_and_summary_reconstruction(self):
        output=self.directory(); cfg=self.fixture(output)
        with patch.object(checker,'plan',return_value=cfg):report=checker.recheck(output)
        self.assertEqual(report['old_new_prefix_comparisons'],12)
        self.assertEqual(report['runs'],{'reference':2,'synchronous_v2':2,'fresh_minimal':2})
        self.assertFalse(report['full_140_qualified'])

    def test_worker_error_retains_completed_reference(self):
        output=self.directory(); case=self.small_plan()['cases'][0]; evaluate=runner.evaluate
        def fail(case,name,mode,out):
            if mode=='synchronous_v2':raise RuntimeError('injected failure')
            return evaluate(case,name,mode,out)
        with patch.object(runner,'evaluate',fail):self.assertEqual(runner.run_case(case,output),2)
        rows=read_records(output);self.assertEqual([r['status'] for r in rows],['PASS','ERROR'])

    def test_serialization_failure_commits_error(self):
        output=self.directory();case=self.small_plan()['cases'][0]
        with patch.object(runner,'evaluate',return_value={'invalid':object()}):
            self.assertEqual(runner.run_case(case,output),2)
        self.assertEqual(read_records(output)[0]['error']['type'],'SerializationError')

    def test_true_timeout_retains_prior_version_and_current_prefix(self):
        output=self.directory(); script=output.parent/'worker.py'
        script.write_text('''import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1])/'experiments'))
import validate_qualification_refactor as r
case=dict(r.cases()[0],case='timeout',n=8,values=list(range(1,9)),input_sha256=r.digest(list(range(1,9))))
real=r.evaluate
def evaluate(case,name,mode,out):
 if mode=='synchronous_v2':time.sleep(30)
 return real(case,name,mode,out)
r.evaluate=evaluate
raise SystemExit(r.run_case(case,Path(sys.argv[2])))
''')
        self.assertEqual(run_bounded([sys.executable,str(script),str(ROOT),str(output)],output,2),2)
        self.assertEqual(len(read_records(output)),1)
        fail=json.loads((output/'failure.json').read_text())
        self.assertEqual(fail['current']['mode'],'synchronous_v2')
        self.assertFalse(fail['accepted'])

    def test_resealed_environment_mode_work_and_fingerprint_corruption_rejected(self):
        original=self.directory();cfg=self.fixture(original)
        for kind in ('environment','fingerprint','replay-count','work','missing-mode','extra-directory'):
            with self.subTest(kind=kind):
                output=self.directory();shutil.copytree(original,output)
                if kind=='environment':
                    doc=json.loads((output/'environment.json').read_text());del doc['hardware'];atomic_json(output/'environment.json',doc)
                elif kind=='missing-mode': (output/'jobs/test-flat/records/000005.json.gz').unlink()
                elif kind=='extra-directory': (output/'extra').mkdir()
                else:
                    path=output/'jobs/test-flat/records/000001.json.gz';row=json.loads(gzip.decompress(path.read_bytes()))
                    if kind=='fingerprint':row['prefixes'][0]['state_sha256']='0'*64
                    elif kind=='replay-count':row['report']['fresh_final_replays']=True
                    else:row['history_work']['linked_points']+=1
                    atomic_bytes(path,gzip.compress(canonical(row),mtime=0))
                runner.seal(output)
                with patch.object(checker,'plan',return_value=cfg),self.assertRaises(ValueError):checker.recheck(output)

    def test_optimization_guards_including_worker(self):
        for script in ('validate_qualification_refactor.py','recheck_qualification_refactor.py'):
            r=subprocess.run([sys.executable,'-O',str(ROOT/'experiments'/script),'--help'],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('optimization level 0',r.stderr)


if __name__=='__main__':unittest.main()
