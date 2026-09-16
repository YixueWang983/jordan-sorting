"""Failure-detection tests for the supplemental validator, not algorithm evidence."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'experiments'),str(ROOT/'src')]
import validate_ordinary_list_extended as v


def fixed(seq):
    return dict(case_id='test',n=len(seq),kind='base',family='fixed',seed=None,
                base_case_id=None,transform=None,prefix_check=False,fixed_sequence=seq)


class ExtendedValidatorTests(unittest.TestCase):
    def test_fixed_plan_and_seed_identity_reproducible(self):
        self.assertEqual(v.build_plan(),v.build_plan())
        plan=v.build_plan();self.assertEqual(len(plan),220)
        bases=[r for r in plan if r['family']=='incremental_valid' and r['kind']=='base']
        self.assertEqual(len(bases),172)
        self.assertEqual(len({r['case_id'] for r in plan}),220)
        s=bases[0]
        a=v.generate_sequence(s['family'],s['n'],seed=s['seed'])
        b=v.generate_sequence(s['family'],s['n'],seed=s['seed'])
        self.assertEqual(a,b);self.assertEqual(v.sequence_hash(a),v.sequence_hash(b))

    def test_duplicate_does_not_call_core_or_inflate_pass_count(self):
        spec=fixed([3,2,1,4]);digest=v.sequence_hash(spec['fixed_sequence'])
        with patch.object(v,'paper_jordan_diagnostics_valid') as checked,patch.object(v,'paper_jordan_sort_valid') as minimal:
            result=v.evaluate(spec,{digest:'historical:known'})
        self.assertEqual(result['status'],'DUPLICATE');checked.assert_not_called();minimal.assert_not_called()
        summary=v.summarize([result]);self.assertEqual(summary['passed'],0);self.assertEqual(summary['new_unique_inputs_executed'],0)

    def test_mode_mismatch_is_output_failure(self):
        with patch.object(v,'paper_jordan_sort_valid',return_value=[1,2,4,3]):
            r=v.evaluate(fixed([3,2,1,4]),{})
        self.assertEqual(r['status'],'OUTPUT_MISMATCH');self.assertFalse(r['modes_equal'])
        self.assertTrue(r['checked']['passed']);self.assertIn('failure_trace_tail',r)

    def test_common_wrong_output_is_not_accepted_as_mode_agreement(self):
        self.assertFalse(v.outputs_agree([3,2,1,4],[1,2,4,3],[1,2,4,3]))

    def test_invalid_final_generator_output_is_recorded(self):
        spec=dict(fixed([1,2,3,4]));spec.pop('fixed_sequence');spec['family']='incremental_valid'
        with patch.object(v,'generate_sequence',return_value=[1,3,2,4]),patch.object(v,'paper_jordan_diagnostics_valid') as call:
            r=v.evaluate(spec,{})
        self.assertEqual(r['status'],'GENERATION_ERROR');self.assertEqual(r['sequence'],[1,3,2,4]);call.assert_not_called()

    def test_certification_exception_is_separate(self):
        with patch.object(v,'oracle',side_effect=OSError('unavailable')):
            r=v.evaluate(fixed([1,2,3]),{})
        self.assertEqual(r['status'],'CERTIFICATION_ERROR');self.assertNotIn('checked',r['mode_calls'])

    def test_wrong_processed_count_is_state_failure(self):
        d=v.paper_jordan_diagnostics_valid([1,2,3,4]);d['processed_count']=3
        with patch.object(v,'paper_jordan_diagnostics_valid',return_value=d):
            r=v.evaluate(fixed([1,2,3,4]),{})
        self.assertEqual(r['status'],'STATE_INVARIANT_ERROR')

    def test_timeout_and_not_run_never_count_as_pass(self):
        rows=[dict(fixed([1,2,3]),status=s,mode_calls={}) for s in ['TIMEOUT','NOT_RUN_BUDGET','NOT_RUN_DEPENDENCY','NOT_RUN_STOPPED']]
        report=v.summarize(rows)
        self.assertEqual(report['passed'],0);self.assertEqual(report['timed_out'],1);self.assertEqual(report['not_run'],3);self.assertEqual(report['completed'],0)

    def test_timeout_kills_worker_and_preserves_phase(self):
        from subprocess import TimeoutExpired
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'case.json'
            v.write_json(path,dict(fixed([1]),status='RUNNING',phase='checked',mode_calls={'checked':'STARTED'},sequence=[1]))
            with patch.object(v.subprocess,'Popen') as start:
                start.return_value.communicate.side_effect=[TimeoutExpired('worker',0.01),('','')]
                r=v.bounded_case(fixed([1]),{},None,path,0.01)
                start.return_value.kill.assert_called_once()
            self.assertEqual(r['status'],'TIMEOUT');self.assertEqual(r['phase'],'checked');self.assertEqual(r['sequence'],[1])

    def test_coverage_requires_a_witness(self):
        r=v.evaluate(fixed([3,2,1,4]),{})
        self.assertEqual(r['status'],'PASS')
        real=v.merge_coverage([r]);self.assertEqual(real['branches']['endpoint.mismatch']['status'],'OBSERVED')
        self.assertEqual(real['branches']['endpoint.mismatch']['witness']['iteration'],4)
        bad=copy.deepcopy(r);bad['coverage']['witnesses'].pop('endpoint.mismatch')
        with self.assertRaisesRegex(ValueError,'without witness'):v.merge_coverage([bad])
        absent=v.merge_coverage([]);self.assertTrue(all(c['status']=='NOT_OBSERVED' for c in absent['branches'].values()))

    def test_existing_output_refused_without_changes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'run';v.reserve(p);(p/'keep').write_text('unchanged')
            with self.assertRaises(FileExistsError):v.reserve(p)
            self.assertEqual((p/'keep').read_text(),'unchanged')

    def test_summary_matches_case_records_and_two_calls_are_one_input(self):
        a=v.evaluate(fixed([3,2,1,4]),{});b=dict(fixed([1]),status='TIMEOUT',mode_calls={})
        c=dict(fixed([1,2]),status='NOT_RUN_BUDGET',mode_calls={});report=v.summarize([a,b,c])
        self.assertEqual(report['planned'],3);self.assertEqual(report['attempted'],2);self.assertEqual(report['completed'],1)
        self.assertEqual(report['passed'],1);self.assertEqual(report['mode_calls_completed']['checked'],1);self.assertEqual(report['mode_calls_completed']['minimal'],1)
        self.assertEqual(report['new_unique_inputs_executed'],1)

    def test_apis_receive_distinct_fresh_inputs(self):
        seq=[3,2,1,4];seen=[]
        checked=v.paper_jordan_diagnostics_valid;minimal=v.paper_jordan_sort_valid
        def c(values):seen.append(values);return checked(values)
        def m(values,execution_mode):seen.append(values);return minimal(values,execution_mode=execution_mode)
        with patch.object(v,'paper_jordan_diagnostics_valid',side_effect=c),patch.object(v,'paper_jordan_sort_valid',side_effect=m):
            r=v.evaluate(fixed(seq),{})
        self.assertEqual(r['status'],'PASS');self.assertIsNot(seen[0],seen[1]);self.assertIsNot(seen[0],seq)

    def test_reflection_records_base_and_certifies_again(self):
        spec=dict(fixed([3,2,1,4]),kind='derived',base_case_id='base')
        with patch.object(v,'oracle',wraps=v.oracle) as cert:
            r=v.evaluate(spec,{},base_sequence=[3,2,1,4])
        cert.assert_called_once_with([2,3,4,1]);self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['base_sequence_sha256'],v.sequence_hash([3,2,1,4]))


if __name__=='__main__':unittest.main()
