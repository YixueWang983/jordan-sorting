"""Regressions for the 844ea6d evidence review; real checkout except named faults."""
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import matched_backend_fixture as runner
from validate_matched_backend_fixture import validate
import test_matched_backend_fixture as fixture_tests

ROOT=Path(__file__).resolve().parents[1]
CHECKER='docs/validation/finger_cost_and_fixture_20261014/recheck_evidence.py'


class FixtureReviewRegressions(unittest.TestCase):
    # Reuse archive editing helpers, without inheriting/duplicating test methods.
    directory=fixture_tests.MatchedBackendFixtureTests.directory
    seal=fixture_tests.MatchedBackendFixtureTests.seal
    rewrite=fixture_tests.MatchedBackendFixtureTests.rewrite

    def raw(self,path):
        return [json.loads(line) for line in (path/'raw.jsonl').read_text().splitlines()]

    def rewrite_rows(self,path,update):
        rows=self.raw(path); update(rows)
        (path/'raw.jsonl').write_bytes(b'\n'.join(runner.canonical(r) for r in rows)+b'\n')
        self.seal(path)

    def test_nonserializable_outputs_leave_a_complete_failed_archive(self):
        cycle=[]; cycle.append(cycle)
        class BrokenRepr:
            def __repr__(self): raise RuntimeError('repr must not run')
        for value in ([object()],[float('nan')],[float('inf')],cycle,object(),[BrokenRepr()]):
            with self.subTest(type=type(value).__name__):
                path=self.directory()
                with patch.object(runner,'paper_jordan_sort_valid',return_value=value):
                    self.assertFalse(runner.run([[1,2,3]],path))
                self.assertFalse(validate(path)['completed_successfully'])
                rows=self.raw(path); self.assertEqual(len(rows),4)
                self.assertEqual(rows[-1]['error']['type'],'OutputMismatch')
                self.assertIsNone(rows[-1]['output'])
                self.assertIsNotNone(rows[-1]['output_diagnostic'])
                self.assertEqual(rows[-1]['kind'],'warmup')
                self.assertEqual(rows[-1]['synthetic_ticks'],1)
                self.assertEqual(json.loads((path/'config.json').read_text())['inputs'][0]['values'],[1,2,3])

    def test_output_diagnostic_is_bounded_without_recursive_representation(self):
        value=['x'*10000]*100
        diagnostic=runner.output_diagnostic(value)
        self.assertEqual(diagnostic['length'],100)
        self.assertTrue(diagnostic['truncated'])
        self.assertEqual(len(diagnostic['preview']),8)
        self.assertLess(len(runner.canonical(diagnostic)),1500)
        self.assertTrue(all(len(x)<=160 for x in diagnostic['preview']))

    def test_row_serialization_failure_itself_is_retained(self):
        cycle=[]; cycle.append(cycle)
        for output in ([object()],[float('nan')],cycle):
            path=self.directory()
            # Bypass the output sanitizer to exercise the final serialization fence.
            unsafe={'status':'ERROR','output':output,'output_diagnostic':None,
                    'synthetic_ticks':1,'error':{'type':'Injected','message':'unsafe row'}}
            with patch.object(runner,'trial',return_value=unsafe):
                self.assertFalse(runner.run([[1,2,3]],path))
            self.assertFalse(validate(path)['completed_successfully'])
            self.assertEqual(self.raw(path)[-1]['error']['type'],'SerializationError')

    def test_io_failure_is_reported_without_claiming_a_complete_archive(self):
        path=self.directory(); original=Path.open
        def opening(p,*args,**kwargs):
            if p.name=='raw.jsonl': raise OSError('injected disk failure')
            return original(p,*args,**kwargs)
        with patch.object(Path,'open',opening),self.assertRaisesRegex(OSError,'disk failure'):
            runner.run([[1,2,3]],path)
        self.assertFalse((path/'summary.json').exists())
        self.assertFalse((path/'manifest.json').exists())
        inputs=path/'inputs.json'; inputs.write_text('[[1,2,3]]')
        with patch.object(sys,'argv',['runner','--inputs',str(inputs),'--output',str(path/'new')]), \
             patch.object(runner,'run',side_effect=OSError('injected disk failure')), \
             patch.object(sys,'stderr',new_callable=io.StringIO) as stderr:
            self.assertEqual(runner.main(),2)
            self.assertIn('evidence may be incomplete',stderr.getvalue())

    def test_validator_rejects_missing_environment_fields_after_resealing(self):
        for field in ('head','dirty','python','platform','captured_at','python_optimize','measurement_kind','source_sha256'):
            with self.subTest(field=field):
                path=self.directory();runner.run([[1,2,3]],path)
                self.rewrite(path,'environment.json',lambda v:v.pop(field))
                with self.assertRaises(ValueError):validate(path)

    def test_validator_rejects_invalid_environment_types_and_values(self):
        bad=(('head',False),('head','not-a-hash'),('dirty','unknown'),('dirty',0),
             ('python',None),('python',''),('platform',[]),('platform','  '),
             ('captured_at','not-a-date'),('captured_at','2026-02-30T10:00:00+00:00'),
             ('captured_at','2026-10-14T10:00:00'),('captured_at','2026-10-14T10:00:00+02:00'),
             ('python_optimize',True),('python_optimize',0.0),('python_optimize',1))
        for field,value in bad:
            with self.subTest(field=field,value=value):
                path=self.directory();runner.run([[1,2,3]],path)
                self.rewrite(path,'environment.json',lambda v:v.update({field:value}))
                with self.assertRaises(ValueError):validate(path)

    def test_runner_rejects_invalid_qualification_count_before_warmup(self):
        original=runner.paper_jordan_diagnostics_valid
        for value in (0,3.0,True,None):
            with self.subTest(value=value):
                path=self.directory()
                def diagnostics(*args,**kwargs):
                    result=original(*args,**kwargs);result['processed_count']=value;return result
                with patch.object(runner,'paper_jordan_diagnostics_valid',diagnostics):
                    self.assertFalse(runner.run([[1,2,3]],path))
                self.assertFalse(validate(path)['completed_successfully'])
                self.assertEqual(len(self.raw(path)),2)
                self.assertEqual(self.raw(path)[-1]['kind'],'qualification')

    def test_validator_requires_integer_qualification_count(self):
        path=self.directory(); runner.run([[1,2,3]],path)
        self.rewrite_rows(path,lambda rows:rows[1].update(processed_count=3.0))
        with self.assertRaisesRegex(ValueError,'qualification incomplete'):validate(path)

    def test_validator_enforces_row_fields_and_error_diagnostic_types(self):
        changes=(lambda r:r.pop('output_diagnostic'),lambda r:r.update(unexpected=True),
                 lambda r:r['error'].update(message=[]),lambda r:r['error'].update(type=False),
                 lambda r:r['output_diagnostic'].update(preview=['x'*161]),
                 lambda r:r['output_diagnostic'].update(truncated=1))
        for change in changes:
            path=self.directory()
            with patch.object(runner,'paper_jordan_sort_valid',return_value=[object()]):runner.run([[1,2,3]],path)
            self.rewrite_rows(path,lambda rows:change(rows[-1]))
            with self.assertRaises(ValueError):validate(path)

    def test_unmanifested_files_and_directories_are_rejected(self):
        for name,directory in (('README.md',False),('extra.json',False),('extra',True)):
            path=self.directory(); runner.run([[1,2,3]],path)
            (path/name).mkdir() if directory else (path/name).write_text('not covered')
            with self.assertRaisesRegex(ValueError,'unexpected archive entry'):validate(path)


class EvidenceOptimizationRegressions(unittest.TestCase):
    def test_cli_and_direct_worker_reject_optimized_python_before_writing(self):
        entries=[('experiments/probe_finger_cost_lemmas.py',[]),
                 ('experiments/validate_finger_middle_splits.py',[]),
                 ('experiments/validate_finger_middle_splits.py',['--worker']),
                 ('experiments/matched_backend_fixture.py',[]),
                 ('experiments/validate_matched_backend_fixture.py',[]),(CHECKER,[])]
        for script,extra in entries:
            for flags,setting in ((['-O'],None),(['-OO'],None),([], '1'),([], '2')):
                with self.subTest(script=script,extra=extra,flags=flags,env=setting),tempfile.TemporaryDirectory() as tmp:
                    out=Path(tmp)/'evidence'
                    env=os.environ.copy();env.pop('PYTHONOPTIMIZE',None)
                    if setting is not None:env['PYTHONOPTIMIZE']=setting
                    result=subprocess.run([sys.executable,*flags,script,*extra,'--output',str(out)],
                                          cwd=ROOT,env=env,text=True,capture_output=True,timeout=15)
                    self.assertNotEqual(result.returncode,0)
                    self.assertIn('Evidence checks require optimization level 0',result.stderr)
                    self.assertFalse(out.exists())
                    self.assertEqual(result.stdout,'')

    def test_normal_interpreter_keeps_source_checks_and_entry_points_available(self):
        env=os.environ.copy();env.pop('PYTHONOPTIMIZE',None)
        for script in ('experiments/probe_finger_cost_lemmas.py','experiments/validate_finger_middle_splits.py',
                       'experiments/matched_backend_fixture.py','experiments/validate_matched_backend_fixture.py',CHECKER):
            result=subprocess.run([sys.executable,script,'--help'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
        sources=runpy.run_path(str(ROOT/CHECKER))['sources']
        for mapping in ({},{'definitely-missing-file':'0'*64},{'README.md':'0'*64}):
            with self.assertRaises((AssertionError,FileNotFoundError)):sources(mapping)


if __name__=='__main__':unittest.main()
