"""Protocol and actual single-case plumbing, distinct from the frozen 12 run."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
import tempfile,unittest
from unittest.mock import patch
from committed_records import read_records
import qualify_common_inputs_v2 as runner
import validate_common_qualification_v2 as checker
from split_qualification_protocol import split_selection,split_plan,split_measurement_protocol
from common_qualification_v2_protocol import frozen_selection
from common_input_protocol import digest


class TargetedSplitTests(unittest.TestCase):
    def test_preselection_unique_separate_and_fixed(self):
        selection=split_selection();cases=selection['cases']
        self.assertEqual(len(cases),12)
        self.assertEqual({(c['spec']['n'],c['spec']['k'],c['spec']['mirror']) for c in cases},
                         {(n,k,m) for n in (128,129) for k in (3,7,19) for m in (False,True)})
        self.assertEqual(len({c['input_sha256'] for c in cases}),12)
        self.assertFalse({c['input_sha256'] for c in cases}&{c['input_sha256'] for c in frozen_selection()['cases']})
        self.assertEqual(split_plan()['selection_sha256'],selection['selection_sha256'])
        self.assertFalse(split_measurement_protocol()['performance_eligible'])

    def fixture(self,root,missing=False):
        import split_qualification_protocol as protocol
        selected=split_selection();selected['cases']=selected['cases'][:1];selected['selection_sha256']=digest(selected['cases'])
        if missing: selected['cases'][0]['spec']['k']=999;selected['selection_sha256']=digest(selected['cases'])
        cfg=split_plan();cfg['selection_sha256']=selected['selection_sha256'];measurement=split_measurement_protocol()
        env=runner.environment();env['dirty']=False
        def worker(command,directory,budget):
            return runner.qualify_case(runner.read(Path(command[command.index('--worker')+1])),directory)
        with patch.object(protocol,'split_selection',return_value=selected),patch.object(protocol,'split_plan',return_value=cfg),\
             patch.object(protocol,'split_measurement_protocol',return_value=measurement),patch.object(runner,'environment',return_value=env),\
             patch.object(runner,'run_bounded',side_effect=worker),patch.object(checker,'validate_revision'):
            passed=runner.run(root,dataset='targeted_split')
            report=checker.validate(root,dataset='targeted_split')
        return passed,report

    def test_actual_single_case_routing_and_coverage_reconstruction(self):
        with tempfile.TemporaryDirectory() as temp:passed,report=self.fixture(Path(temp)/'run')
        self.assertTrue(passed);self.assertEqual(report['completed_modes'],{'synchronous_v2':2,'fresh_minimal':2})
        self.assertEqual(len(report['split_coverage']),2)
        self.assertTrue(all(any(s['smaller_side']==3 for s in c['splits']) for c in report['split_coverage']))

    def test_missing_actual_target_cannot_pass_even_if_all_outputs_pass(self):
        with tempfile.TemporaryDirectory() as temp:passed,report=self.fixture(Path(temp)/'run',missing=True)
        self.assertFalse(passed);self.assertFalse(report['all_selected_qualified']);self.assertEqual(report['status_counts'],{'ERROR':1})


if __name__=='__main__':unittest.main()
