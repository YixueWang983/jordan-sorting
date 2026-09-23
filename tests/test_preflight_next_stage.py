"""Tests for structural sampling and evidence identity, not benchmark results."""
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from preflight_next_stage import block_sequence, config, rank_normalize, run
from oracle import oracle
from validate_ordinary_list_extended import evaluate
from stats import structure_profile

class PreflightTests(unittest.TestCase):
    def test_order_preserving_transforms_have_one_identity(self):
        self.assertEqual(rank_normalize([20,10,40,30]),rank_normalize([2,1,4,3]))
        self.assertNotEqual(rank_normalize([20,10,40,30]),rank_normalize([-20,-10,-40,-30]))

    def test_blocks_are_valid_and_reach_measured_low_and_medium(self):
        for n in (32,33,64,65):
            for seed in (1,2,3,4):
                for density in ('low','medium'):
                    values=block_sequence(n,seed,density)
                    self.assertEqual(sorted(values),list(range(1,n+1)))
                    self.assertTrue(oracle(values)['valid'])
                    self.assertEqual(structure_profile(values)['category'],density+'_nesting_valid')

    def test_plan_reproducible_and_reflections_identify_base(self):
        self.assertEqual(config(),config())
        seen=set()
        for spec in config()['plan']:
            if spec['kind']=='derived':
                self.assertIn(spec['base_case_id'],seen)
            seen.add(spec['case_id'])

    def test_final_resource_error_returns_nonzero_without_unexecuted_cases(self):
        cfg = config()
        cfg['plan'] = cfg['plan'][:2]  # Empty and singleton inputs.
        for final_status, expected_code in [('PASS', 0), ('RESOURCE_ERROR', 2)]:
            with self.subTest(final_status=final_status), tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / 'run'

                def worker(spec, known, base, path, seconds):
                    if spec['case_id'] == cfg['plan'][-1]['case_id'] and final_status == 'RESOURCE_ERROR':
                        return dict(spec, status='RESOURCE_ERROR', phase='checked',
                                    error='MemoryError: injected', mode_calls={})
                    return evaluate(spec, known, base)

                with patch('preflight_next_stage.config', return_value=cfg), patch(
                    'preflight_next_stage.bounded_case', side_effect=worker
                ) as calls, patch('preflight_next_stage.git', return_value='test'), patch(
                    'preflight_next_stage.source_hashes', return_value={}
                ), patch('builtins.print'):
                    exit_code = run(output)

                report = json.loads((output / 'summary.json').read_text())
                self.assertEqual(calls.call_count, 2)
                self.assertEqual(report['failed'], 0)
                self.assertEqual(report['timed_out'], 0)
                self.assertEqual(report['not_run'], 0)
                self.assertTrue(report['source_unchanged'])
                self.assertEqual(report['resource_errors'], int(final_status == 'RESOURCE_ERROR'))
                self.assertEqual(report['passed'], 1 if final_status == 'RESOURCE_ERROR' else 2)
                last = json.loads((output / 'cases' / (cfg['plan'][-1]['case_id'] + '.json')).read_text())
                self.assertEqual(last['status'], final_status)
                self.assertEqual(exit_code, expected_code)

    def test_refuse_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp); (p/'sentinel').write_text('keep')
            with self.assertRaises(FileExistsError): run(p)
            self.assertEqual((p/'sentinel').read_text(),'keep')

if __name__=='__main__': unittest.main()
