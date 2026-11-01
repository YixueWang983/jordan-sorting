"""New configuration isolation and power gates; timing fixtures are synthetic."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from common_input_protocol import BACKENDS as OLD_BACKENDS, digest, source_identity
from committed_records import atomic_json, read_records
import uninstrumented_protocol as protocol
import matched_measurement as timing
import validate_matched_measurement as timing_checker
import qualify_common_inputs_v2 as qualification
import validate_common_qualification_v2 as qualification_checker
import validate_uninstrumented_equivalence as equivalence
import test_matched_measurement_tools as mechanical
import run_uninstrumented_formal as author_entry
import analyze_uninstrumented_measurement as analysis


def power(source='AC Power', mode='0'):
    return dict(power=f"Now drawing from '{source}'\n -InternalBattery-0 40%",
                power_settings='Currently in use:\n lowpowermode '+mode,
                power_source=source,lowpowermode=mode)


class UninstrumentedProtocolTests(unittest.TestCase):
    def test_new_identity_fixed_inputs_and_unchanged_old_backends(self):
        self.assertEqual(OLD_BACKENDS,('ordinary_list','heterogeneous_finger'))
        for dataset,count in [('common',140),('targeted_split',12)]:
            cfg,selection,rules=protocol.qualification_config(dataset)
            old=timing.dataset_config(dataset);new=timing.dataset_config(dataset,'uninstrumented')
            self.assertEqual(len(selection['cases']),count)
            self.assertEqual(old['selection_sha256'],new['selection_sha256'])
            self.assertEqual(old['cases'],new['cases'])
            self.assertEqual(old['rules'],new['rules'])
            self.assertNotEqual(old['schema'],new['schema'])
            self.assertEqual(set(new['backend_identities']),set(protocol.BACKENDS))
        with self.assertRaises(ValueError):timing.dataset_config('structural_split','uninstrumented')

    def test_power_gate_parses_raw_evidence(self):
        protocol.require_power(power())
        for observation in (power('Battery Power'),power(mode='1')):
            with self.assertRaisesRegex(RuntimeError,'Connect AC'):protocol.require_power(observation)
        tampered=power();tampered['lowpowermode']='1'
        with self.assertRaises(ValueError):protocol.require_power(tampered)
        with self.assertRaises(ValueError):protocol.parsed_power('unknown','lowpowermode 0')
        with self.assertRaises(ValueError):protocol.parsed_power(power()['power'],'lowpowermode 0\nlowpowermode 1')

    def test_real_one_case_qualification_routes_and_rebuilds(self):
        cfg,selected,rules=protocol.qualification_config('targeted_split')
        selected['cases']=selected['cases'][:1];selected['selection_sha256']=digest(selected['cases'])
        cfg['selection_sha256']=selected['selection_sha256']
        env=qualification.environment(include_power_settings=True);env['dirty']=False
        def worker(command,directory,budget):
            return qualification.qualify_case(qualification.read(Path(command[command.index('--worker')+1])),directory)
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(protocol,'qualification_config',return_value=(cfg,selected,rules)), \
                patch.object(qualification,'environment',return_value=env), \
                patch.object(qualification,'run_bounded',side_effect=worker), \
                patch.object(qualification_checker,'validate_revision'):
            out=Path(temp)/'qualified'
            self.assertTrue(qualification.run(out,dataset='targeted_split',configuration='uninstrumented'))
            report=qualification_checker.validate(out,dataset='targeted_split')
            self.assertEqual(report['configuration'],'uninstrumented')
            self.assertEqual(set(report['per_backend_nonempty_splits']),set(protocol.BACKENDS))

    def test_synthetic_complete_campaign_and_missing_author_receipt(self):
        helper=mechanical.MatchedToolTests(methodName='runTest');self.addCleanup(helper.doCleanups)
        root=helper.directory();scope,q,env=helper.fixture_scope(root)
        env['execution']['hardware'].update(power())
        fake_q=dict(all_selected_qualified=True,selection_sha256='fixture-selection',configuration='uninstrumented')
        # Test-only approval fixture, never exported or used for real sampling.
        review=dict(schema='representation_locality_cost_review_v1',approved=True,
                    production_sha256={p:h for p,h in source_identity().items() if p.startswith('src/')},
                    review_references=['TEST STUB ONLY; no proof reviewed'])
        with scope, patch.object(timing_checker,'validate_qualification',return_value=fake_q), \
                patch.object(protocol,'power_observation',return_value=power()):
            self.assertTrue(timing.run(root/'cal','calibration','common',q,configuration='uninstrumented'))
            report=timing_checker.validate(root/'cal',qualification=q)
            self.assertTrue(report['complete']);self.assertEqual(report['configuration'],'uninstrumented')
            with self.assertRaisesRegex(ValueError,'explicit manual review'):
                timing.run(root/'forbidden','formal','common',q,configuration='uninstrumented',calibration=root/'cal')
            self.assertFalse((root/'forbidden').exists())
            self.assertTrue(timing.run(root/'formal','formal','common',q,configuration='uninstrumented',calibration=root/'cal',review=review))
            report=timing_checker.validate(root/'formal',qualification=q,calibration=root/'cal')
            self.assertEqual(report['statistics']['mechanical-eight']['tree_over_list_median'],1.6)
            with self.assertRaisesRegex(ValueError,'configuration mismatch'):
                timing.run(root/'wrong','formal','common',q,calibration=root/'cal',review=review)
            bad=timing.read(root/'formal/jobs/mechanical-eight/power.json');bad['after']=power('Battery Power')
            atomic_json(root/'formal/jobs/mechanical-eight/power.json',bad)
            with self.assertRaises(RuntimeError):
                timing_checker.check_job(root/'formal/jobs/mechanical-eight',timing.read(root/'formal/requests/mechanical-eight.json'),passing=True)

    def test_worker_power_gate_stops_before_sampling_or_preserves_completed_rows(self):
        helper=mechanical.MatchedToolTests(methodName='runTest');self.addCleanup(helper.doCleanups)
        req=helper.request('formal');req['configuration']='uninstrumented'
        out=helper.directory()/'blocked'
        with patch.object(protocol,'power_observation',return_value=power('Battery Power')), \
                patch.object(timing,'trial_batch') as trial:
            self.assertEqual(timing.execute_case(req,out),2);trial.assert_not_called()
            self.assertEqual(read_records(out),[])
        out=helper.directory()/'interrupted'
        with patch.object(protocol,'power_observation',side_effect=[power(),power('Battery Power')]):
            self.assertEqual(helper.run_case(out,req),2)
            self.assertEqual(len(read_records(out)),50)
            self.assertFalse((out/'summary.json').exists())
            self.assertFalse(timing.read(out/'failure.json')['accepted'])

    def test_equivalence_selection_and_one_real_counted_comparison(self):
        selected=equivalence.selection()
        self.assertEqual(len(selected),192)
        self.assertEqual({g:sum(c['group']==g for c in selected) for g in ('common','targeted_split','seeded')},
                         dict(common=140,targeted_split=12,seeded=40))
        case=next(c for c in selected if c['group']=='targeted_split')
        result=equivalence.evaluate(case,counted=True)
        self.assertTrue(result['legacy_trace_equal'])
        self.assertGreater(result['counted']['work']['operations']['node_visits'],0)

    def test_author_entry_stops_after_common_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);receipt=root/'test-only.json'
            atomic_json(receipt,{'scope':'TEST STUB; not an approval'})
            with patch.object(author_entry,'run',return_value=False) as run:
                self.assertFalse(author_entry.execute(root/'out',root/'q',root/'cal',receipt))
                self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[2],'common')
            with patch.object(author_entry,'run',return_value=True) as run:
                self.assertTrue(author_entry.execute(root/'out',root/'q',root/'cal',receipt))
                self.assertEqual([c.args[2] for c in run.call_args_list],['common','targeted_split'])

    def test_descriptive_analysis_uses_input_ratios(self):
        rows=[dict(list_ms=1,tree_ms=2,ratio=2),dict(list_ms=100,tree_ms=50,ratio=.5)]
        result=analysis.aggregate(rows)
        self.assertEqual(result['ratio_median'],1.25)
        self.assertEqual(result['tree_faster'],1)
        self.assertEqual(analysis.r7([1,2,8,10],.25),1.75)


if __name__=='__main__':
    unittest.main()
