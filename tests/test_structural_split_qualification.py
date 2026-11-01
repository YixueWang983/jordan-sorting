"""Structural coverage gates and dataset isolation, not timing observations."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'experiments'), str(ROOT/'tests')]
import copy
import gzip
import json
import tempfile
import unittest
from unittest.mock import patch

from common_input_protocol import BACKENDS, digest, measurement_protocol, source_identity
from common_qualification_v2_protocol import frozen_selection
from committed_records import read_records
from qualification_trace_semantics import check_trace
from split_qualification_protocol import split_selection
import structural_split_protocol as protocol
import qualify_common_inputs_v2 as runner
import validate_common_qualification_v2 as checker
import matched_measurement as timing
import validate_matched_measurement as timing_checker
import test_matched_measurement_tools as mechanical_fixtures
from validate_finger_work_modes import sequence


class StructuralSplitTests(unittest.TestCase):
    def test_selection_reuses_all_original_inputs_without_overlap_or_filtering(self):
        selected = protocol.structural_selection()
        old = ROOT/'docs/validation/heterogeneous_work_modes_20261013/structural_campaign'
        expected = json.loads((old/'config.json').read_text())['plan']
        self.assertEqual([c['spec']['case'] for c in selected['cases']], [c['case'] for c in expected])
        for case in selected['cases']:
            original = json.loads(gzip.decompress((old/(case['spec']['case']+'.json.gz')).read_bytes()))
            self.assertEqual(case['values'], original['values'])
        hashes = {c['rank_sha256'] for c in selected['cases']}
        self.assertEqual(len(hashes), 18)
        for previous in (frozen_selection(), split_selection()):
            self.assertFalse(hashes & {c['rank_sha256'] for c in previous['cases']})
        self.assertEqual(protocol.structural_plan()['selection_sha256'], selected['selection_sha256'])
        self.assertEqual(protocol.structural_measurement_protocol()['rules'], measurement_protocol())
        self.assertEqual(timing.dataset_config('structural_split')['selection_sha256'], selected['selection_sha256'])

    def test_real_small_traces_cover_each_shape_and_direction(self):
        with tempfile.TemporaryDirectory() as temp:
            for n in (32, 33):
                for shape in protocol.SHAPES:
                    with self.subTest(n=n, shape=shape):
                        values = sequence(n, shape, bool(n % 2))
                        out = Path(temp)/f'{shape}-{n}'
                        req = dict(case=out.name, values=values, backends=list(BACKENDS))
                        self.assertEqual(runner.qualify_case(req, out), 0)
                        for row in read_records(out):
                            if row['mode'] != 'synchronous_v2':
                                continue
                            coverage = check_trace(values, row['final']['trace'], row['final']['metrics'], row['backend'])
                            summary = protocol.require_structural_coverage(dict(n=n, shape=shape), coverage)
                            self.assertGreater(summary['retained_inserts']+summary['acquired_inserts'], 0)
                            missing = copy.deepcopy(coverage)
                            missing['splits'] = [s for s in missing['splits'] if not s['smaller_side']]
                            with self.assertRaisesRegex(ValueError, 'missing actual'):
                                protocol.require_structural_coverage(dict(n=n, shape=shape), missing)
                            if shape == 'repeated':
                                missing = copy.deepcopy(coverage)
                                for i, event in enumerate(missing['splits']):
                                    event['source_list_id'] = -1000-i
                                with self.assertRaisesRegex(ValueError, 'repeated split/update'):
                                    protocol.require_structural_coverage(dict(n=n, shape=shape), missing)

    def qualification_fixture(self, out, wrong_shape=False):
        selected = protocol.structural_selection()
        selected['cases'] = selected['cases'][:1]
        if wrong_shape:
            selected['cases'][0]['spec']['shape'] = 'repeated'
        selected['selection_sha256'] = digest(selected['cases'])
        cfg = protocol.structural_plan(); cfg['selection_sha256'] = selected['selection_sha256']
        measured = protocol.structural_measurement_protocol()
        measured['selection_sha256'] = selected['selection_sha256']
        env = runner.environment(); env['dirty'] = False
        def worker(command, directory, budget):
            return runner.qualify_case(runner.read(Path(command[command.index('--worker')+1])), directory)
        with patch.object(protocol, 'structural_selection', return_value=selected), \
             patch.object(protocol, 'structural_plan', return_value=cfg), \
             patch.object(protocol, 'structural_measurement_protocol', return_value=measured), \
             patch.object(runner, 'environment', return_value=env), \
             patch.object(runner, 'run_bounded', side_effect=worker), \
             patch.object(checker, 'validate_revision'):
            passed = runner.run(out, dataset='structural_split')
            report = checker.validate(out, dataset='structural_split')
        return passed, report

    def test_actual_single_case_qualification_routing_and_rebuild(self):
        with tempfile.TemporaryDirectory() as temp:
            passed, report = self.qualification_fixture(Path(temp)/'run')
        self.assertTrue(passed)
        self.assertEqual(report['per_backend_nonempty_splits'], dict.fromkeys(BACKENDS, 1))
        self.assertEqual(len(report['split_coverage']), 2)

    def test_correct_output_without_required_workload_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as temp:
            passed, report = self.qualification_fixture(Path(temp)/'run', wrong_shape=True)
        self.assertFalse(passed)
        self.assertFalse(report['all_selected_qualified'])
        self.assertEqual(report['status_counts'], {'ERROR': 1})

    def test_measurement_route_and_cross_dataset_rejection(self):
        helper = mechanical_fixtures.MatchedToolTests(methodName='runTest')
        self.addCleanup(helper.doCleanups)
        root = helper.directory()
        scope, qualification, env = helper.fixture_scope(root)
        selected = dict(cases=[dict(spec={'case':'mechanical-eight'}, values=list(range(1,9)),
                                  input_sha256=digest(list(range(1,9))))],
                        selection_sha256='fixture-selection')
        review = dict(schema='representation_locality_cost_review_v1', approved=True,
                      production_sha256={p:h for p,h in source_identity().items() if p.startswith('src/')},
                      review_references=['TEST STUB ONLY; no proof reviewed'])
        with scope, patch.object(protocol, 'structural_selection', return_value=selected):
            self.assertTrue(timing.run(root/'cal', 'calibration', 'structural_split', qualification))
            result = timing_checker.validate(root/'cal', qualification=qualification)
            self.assertEqual(result['dataset'], 'structural_split')
            with self.assertRaisesRegex(ValueError, 'different dataset'):
                timing.run(root/'forbidden', 'formal', 'common', qualification,
                           calibration=root/'cal', review=review)
            self.assertFalse((root/'forbidden').exists())
            self.assertTrue(timing.run(root/'formal', 'formal', 'structural_split', qualification,
                                       calibration=root/'cal', review=review))
            result = timing_checker.validate(root/'formal', qualification=qualification, calibration=root/'cal')
            self.assertTrue(result['complete'])
            self.assertEqual(result['statistics']['mechanical-eight']['tree_over_list_median'], 1.6)


if __name__ == '__main__':
    unittest.main()
