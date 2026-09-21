"""Tests for structural sampling and evidence identity, not benchmark results."""
import tempfile
from pathlib import Path
import unittest
from preflight_next_stage import block_sequence, config, rank_normalize, run
from oracle import oracle
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

    def test_refuse_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp); (p/'sentinel').write_text('keep')
            with self.assertRaises(FileExistsError): run(p)
            self.assertEqual((p/'sentinel').read_text(),'keep')

if __name__=='__main__': unittest.main()
