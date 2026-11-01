import copy
from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from committed_records import atomic_bytes, atomic_json, canonical, read_records
from input_suite_registry import load_suite
from qualify_common_inputs import seal
import run_host_stability as runner
import validate_host_stability as checker
from stability_protocol import select_cases
import test_input_suite_pipeline as pipeline_fixtures


class HostStabilityTests(unittest.TestCase):
    def test_panel_is_fixed_before_timing_and_targeted_selection_is_explicit(self):
        suite=load_suite();panel=select_cases(suite)
        self.assertEqual(len(panel),10)
        self.assertEqual(len({e['source'] for e in panel}),5)
        cid=panel[0]['case_id']
        self.assertEqual([e['case_id'] for e in select_cases(suite,[cid])],[cid])
        for ids in ([cid,cid],['unknown']):
            with self.assertRaises(ValueError):select_cases(suite,ids)

    def diagnostic(self):
        helper=pipeline_fixtures.UnifiedPipelineTests(methodName='runTest');helper.setUp()
        self.addCleanup(helper.doCleanups)
        stack=ExitStack();self.addCleanup(stack.close)
        for module in (runner,checker):
            stack.enter_context(patch.object(module,'load_suite',return_value=helper.suite))
        def environment(**kwargs):
            result=copy.deepcopy(helper.env)
            result['execution']['captured_at']=datetime.now(timezone.utc).isoformat()
            return result
        stack.enter_context(patch.object(runner,'capture_environment',side_effect=environment))
        stack.enter_context(patch.object(runner,'power_observation',return_value=pipeline_fixtures.POWER))
        def bounded(command,folder,budget):
            request=json.loads(Path(command[command.index('--worker')+1]).read_bytes())
            return runner.worker(request,folder)
        stack.enter_context(patch.object(runner,'run_bounded',side_effect=bounded))
        folder=helper.root/'diagnostic'
        result=runner.run(folder,case_ids=[helper.suite['entries'][0]['case_id']])
        return folder,result

    def test_records_rebuild_without_trusting_summary_and_reject_tampered_output(self):
        folder,result=self.diagnostic()
        self.assertTrue(result['complete'])
        self.assertFalse(result['performance_eligible'])
        self.assertEqual(result['total_sample_batches'],120)
        self.assertEqual(len(result['rows']),2)
        for p in (folder/'jobs').glob('s*/summary.json'):
            p.write_bytes(b'not parsed for independent statistics')
        seal(folder)
        self.assertEqual(checker.validate(folder)['aggregate'],result['aggregate'])
        path=next((folder/'jobs').glob('s*/records/000010.json.gz'))
        row=json.loads(gzip.decompress(path.read_bytes()))
        row['outputs'][0]['output']=[999]
        atomic_bytes(path,gzip.compress(canonical(row)+b'\n',mtime=0));seal(folder)
        with self.assertRaisesRegex(ValueError,'external output'):checker.validate(folder)

    def test_comparison_rejects_changed_sources_and_reconstructs_variation(self):
        _,left=self.diagnostic();right=copy.deepcopy(left)
        comparison=checker.compare(left,right)
        for value in comparison['aggregate'].values():
            self.assertEqual(value['left_lower_within_case_variation'],0)
        right['environment']['execution']['source_sha256']['src/example.py']='0'*64
        with self.assertRaisesRegex(ValueError,'source'):checker.compare(left,right)

    def test_failed_attempt_is_not_a_comparison_and_output_is_not_overwritten(self):
        folder,_=self.diagnostic()
        with self.assertRaises(FileExistsError):runner.run(folder)
        atomic_json(folder/'failure.json',{'complete':False});seal(folder)
        with self.assertRaisesRegex(ValueError,'failed diagnostic'):checker.validate(folder)
