"""Check the frozen probe scope and its use of the unchanged audit path."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from preflight_next_stage import block_sequence, run as run_batch
from probe_large_qualification import campaign_config, run as run_campaign
from oracle import oracle
from generators import generate_sequence
from stats import structure_profile
from validate_ordinary_list_extended import evaluate, read_json, write_json


class LargeQualificationTests(unittest.TestCase):
    def test_resource_failure_keeps_other_batches_but_correctness_failure_stops_them(self):
        for failure, expected_batches in [('TIMEOUT', 4), ('OUTPUT_MISMATCH', 1)]:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                def batch_runner(output, run_config):
                    (output/'cases').mkdir(parents=True)
                    first = run_config['plan'][0]['n'] == 256
                    for spec in run_config['plan']:
                        write_json(output/'cases'/f"{spec['case_id']}.json", dict(
                            spec, status=failure if first else 'PASS'))
                    write_json(output/'summary.json', {'test_stub': True})
                    return 2 if first else 0
                output = Path(tmp)/'campaign'
                with patch('probe_large_qualification.run_batch', side_effect=batch_runner) as calls, patch(
                    'probe_large_qualification.git', return_value='test'
                ), patch('probe_large_qualification.source_hashes', return_value={}):
                    self.assertEqual(run_campaign(output), 2)
                self.assertEqual(calls.call_count, expected_batches)
                summary = read_json(output/'campaign_summary.json')
                self.assertEqual(summary['recorded'], expected_batches*4)
                self.assertEqual(summary['not_run_after_campaign_stop'], 16-expected_batches*4)
                self.assertEqual(summary['status_counts'][failure], 4)

    def test_frozen_candidates_are_valid_and_cover_intended_structures(self):
        expected = ['strict_flat', 'low_nesting_valid', 'medium_nesting_valid', 'nested_heavy_valid']
        for batch in campaign_config()['batches']:
            for spec, category in zip(batch['plan'], expected):
                with self.subTest(case=spec['case_id']):
                    family = spec['family']
                    seq = (block_sequence(spec['n'], spec['seed'], family.split('_')[1])
                           if family.startswith('blocks_') else
                           generate_sequence(family, spec['n'], seed=spec['seed']))
                    self.assertTrue(oracle(seq)['valid'])
                    self.assertEqual(structure_profile(seq)['category'], category)

    def test_supplied_configuration_is_frozen_and_worker_budget_is_forwarded(self):
        cfg = campaign_config()['batches'][0]
        cfg['plan'] = [dict(cfg['plan'][0], n=3, fixed_sequence=[1, 2, 3])]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'probe'
            def worker(spec, known, base, path, seconds):
                self.assertEqual(read_json(output/'config.json'), cfg)
                self.assertEqual(seconds, 180)
                return evaluate(spec, known, base)
            with patch('preflight_next_stage.bounded_case', side_effect=worker), patch(
                'preflight_next_stage.git', return_value='test'
            ), patch('preflight_next_stage.source_hashes', return_value={}):
                self.assertEqual(run_batch(output, run_config=cfg), 0)
            self.assertEqual(read_json(output/'cases'/f"{cfg['plan'][0]['case_id']}.json")['mode_calls'],
                             {'checked': 'COMPLETED', 'minimal': 'COMPLETED'})


if __name__ == '__main__':
    unittest.main()
