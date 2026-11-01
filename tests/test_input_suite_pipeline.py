"""TEST ONLY: tiny synthetic inputs and synthetic durations, never the registered suite."""
import copy
from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timedelta, timezone
import gc
import gzip
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'experiments')]
import analyze_input_suite as analysis
import input_suite_worker as worker
import run_input_suite as runner
import validate_input_suite_run as checker
import matched_measurement as measurement
from common_input_protocol import digest, source_identity
from committed_records import atomic_bytes, atomic_json, canonical, read_records
from input_suite_protocol import DEADLINE, limits, profile
from input_suite_registry import SOURCE_ORDER
from matched_backend_fixture import backend_spec
from qualify_common_inputs import read, seal
from uninstrumented_protocol import BACKENDS
from validate_finger_middle_splits import values_for
from validate_finger_work_modes import sequence
from validate_uninstrumented_equivalence import checked


POWER = dict(power="Now drawing from 'AC Power'", power_settings='lowpowermode 0',
             power_source='AC Power', lowpowermode='0')


def fixture_suite():
    values = [list(range(1, 9)), values_for(16, 1, False), sequence(18, 'balanced'),
              list(range(1, 11)), list(range(12))]
    entries = []
    for i, (source, data) in enumerate(zip(SOURCE_ORDER, values)):
        cid = 'TEST_ONLY--' + source
        entries.append(dict(case_id=cid, source=source, source_index=0,
            original_case_id='split-n128-k3' if source == 'targeted_split' else cid,
            values=data, n=len(data), input_sha256=digest(data),
            category='flat' if source == 'common' else None,
            construction_family='values_for' if i in (1, 2) else 'TEST_ONLY',
            shape='targeted' if i == 1 else 'balanced' if i == 2 else None,
            smaller_side_k=1 if i == 1 else 3 if i == 2 else None,
            mirror=False, membership_status='CANONICAL', canonical_case_id=cid, duplicate_of=None))
    return dict(entries=entries, exclusions=[], suite_sha256=digest(entries), registration={'TEST_ONLY': True})


class UnifiedPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.suite = fixture_suite()
        self.t = datetime(2026, 11, 1, tzinfo=timezone.utc)
        self.env = dict(execution=dict(
            head='0' * 40, dirty=False, source_sha256=source_identity(),
            captured_at=self.t.isoformat(), python='3.12.14 TEST FIXTURE', executable=sys.executable,
            platform='macOS TEST FIXTURE', machine='arm64', python_optimize=0, gc_enabled=True,
            gc_thresholds=list(gc.get_threshold()), purpose='matched calibration or formal measurement',
            hardware=dict(POWER, **{'machdep.cpu.brand_string':'Apple M4', 'hw.physicalcpu':'10',
                                   'hw.logicalcpu':'10', 'hw.memsize':'16000000000'})),
            clock=dict(implementation='TEST ONLY', resolution_seconds=1e-9, monotonic=True,
                       adjustable=False, successive_read_deltas_ns=[1] * 1000))
        self.receipt = dict(schema='representation_locality_cost_review_v1', approved=True,
            production_sha256={p:h for p,h in source_identity().items() if p.startswith('src/')},
            review_references=['TEST STUB ONLY: no author approval or proof review'])
        self.traces = {e['case_id']:digest(checked(e['values'], backend_spec('heterogeneous_finger'))[0]['trace'])
                       for e in self.suite['entries']}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        for module in (runner, worker, checker, analysis):
            self.stack.enter_context(patch.object(module, 'load_suite', side_effect=lambda: copy.deepcopy(self.suite)))
        for module in (worker, checker):
            self.stack.enter_context(patch.object(module, 'old_trace_digest', side_effect=lambda e:self.traces[e['case_id']]))
        self.stack.enter_context(patch.object(runner, 'capture_environment', side_effect=lambda **kw:copy.deepcopy(self.env)))
        self.stack.enter_context(patch('validate_common_qualification_v2.validate_revision'))
        self.stack.enter_context(patch.object(worker, 'power_observation', return_value=POWER))
        self.stack.enter_context(patch('uninstrumented_protocol.power_observation', return_value=POWER))
        self.stack.enter_context(patch.object(runner, 'utc_now', side_effect=self.now))
        self.stack.enter_context(patch.object(measurement, 'trial_batch', side_effect=self.synthetic_batch))
        self.stack.enter_context(patch.object(runner, 'run_bounded', side_effect=self.bounded))
        self.fail = None
        self.calls = []

    def now(self):
        self.t += timedelta(milliseconds=1)
        return self.t.isoformat()

    def synthetic_batch(self, values, name, expected, batch, clock=None):
        # No sorting or clock invocation: fabricated durations test only the tools.
        factor = {8:2, 16:.5, 18:1, 10:1.5, 12:.75}[len(values)] if name == BACKENDS[1] else 1
        return dict(status='PASS', error=None, elapsed_ns=int(10_000_000 * batch * factor),
                    completed_calls=batch, outputs=[dict(output=list(expected), output_diagnostic=None) for _ in range(batch)])

    def bounded(self, command, output, seconds):
        request = read(Path(command[command.index('--request') + 1]))
        self.calls.append((request['stage'], request['entry']['source'], seconds))
        if self.fail and (request['stage'], request['entry']['source']) == self.fail[:2]:
            output.mkdir(parents=True)
            atomic_json(output/'failure.json', dict(status=self.fail[2], accepted=False,
                        performance_eligible=False, budget_seconds=seconds, committed_records=0))
            return 2
        return worker.execute(request, output)

    def stage(self, stage, source='all', name=None, **overrides):
        paths = {s:[self.root/s] for s in ('equivalence','qualification','calibration')
                 if s in runner.prerequisite_stages(stage)}
        paths.update(overrides)
        if stage == 'formal':
            paths.setdefault('review', self.receipt)
        output = self.root / (name or stage)
        runner.run_stage(output, stage, source, **paths)
        return checker.validate(output)

    def prepare(self):
        for s in ('equivalence', 'qualification', 'calibration'):
            self.assertTrue(self.stage(s)['complete'])

    def test_end_to_end_raw_statistics_and_figures(self):
        self.prepare()
        result = self.stage('formal')
        self.assertTrue(result['all_sources_complete'])
        self.assertEqual([s for stage,s,_ in self.calls if stage == 'formal'], list(SOURCE_ORDER))
        self.assertEqual(result['sources']['targeted_split']['statistics']['TEST_ONLY--targeted_split']['tree_over_list_median'], .5)
        summary = analysis.analyze(self.root/'formal', self.root/'analysis')
        self.assertEqual(summary['overall'], dict(inputs=5, tree_faster=2, ties=1, median=1, minimum=.5, maximum=2))
        self.assertEqual(summary['strata']['structural']['balanced']['timing']['inputs'], 1)
        self.assertEqual(summary['strata']['common']['flat']['timing']['inputs'], 1)
        self.assertEqual(len(list((self.root/'analysis').glob('*.png'))), 4)
        self.assertEqual(len(list((self.root/'analysis').glob('*.pdf'))), 4)
        rows = read(self.root/'analysis/cases.json')
        self.assertTrue(any(r['S_i'] == 0 and r['p_i'] is None for r in rows))
        self.assertTrue(all(r['I_i'] == len(r['smaller_sides']) for r in rows))

    def test_targeted_new_budget_1800_old_identity_unchanged(self):
        from split_qualification_protocol import split_plan
        self.assertEqual(limits('qualification'), dict(input_seconds=180, source_seconds=1800, total_seconds=None))
        old = split_plan()
        self.assertEqual(old['campaign_seconds'], 180)
        self.assertEqual(profile(self.suite, 'qualification', 'targeted_split')['limits']['source_seconds'], 1800)

    def test_qualification_timeout_only_excludes_its_source(self):
        self.stage('equivalence')
        self.fail = ('qualification', 'targeted_split', 'RESOURCE_TIMEOUT')
        r = self.stage('qualification')
        self.assertEqual(r['sources']['targeted_split']['status'], 'INCOMPLETE')
        self.assertEqual(r['sources']['geometric']['status'], 'COMPLETE')
        self.fail = None
        self.stage('calibration')
        self.stage('formal')
        summary = analysis.analyze(self.root/'formal', self.root/'partial-analysis')
        self.assertEqual(summary['actual_timed_inputs'], 4)
        self.assertEqual(summary['timed_source_composition']['targeted_split'], 0)

    def test_calibration_timeout_continues_and_no_partial_source_sampling(self):
        self.stage('equivalence'); self.stage('qualification')
        self.fail = ('calibration', 'structural', 'RESOURCE_TIMEOUT')
        r = self.stage('calibration')
        self.assertEqual(r['sources']['structural']['status'], 'INCOMPLETE')
        self.assertEqual(r['sources']['seeded']['status'], 'COMPLETE')
        self.fail = None
        r = self.stage('formal')
        self.assertEqual(r['sources']['structural']['status'], 'INCOMPLETE')
        self.assertNotIn(('formal', 'structural'), [c[:2] for c in self.calls])

    def test_correctness_error_stops_remaining_sources(self):
        self.stage('equivalence')
        self.fail = ('qualification', 'targeted_split', 'WORKER_ERROR')
        r = self.stage('qualification')
        self.assertTrue(r['hard_error'])
        self.assertEqual(r['sources']['structural']['status'], 'NOT_RUN')
        with self.assertRaisesRegex(ValueError, 'correctness/configuration'):
            self.stage('calibration')

    def test_formal_timeout_stops_whole_session(self):
        self.prepare()
        self.fail = ('formal', 'targeted_split', 'RESOURCE_TIMEOUT')
        r = self.stage('formal')
        self.assertEqual(r['sources']['common']['status'], 'COMPLETE')
        self.assertEqual(r['sources']['targeted_split']['status'], 'INCOMPLETE')
        self.assertEqual(r['sources']['structural']['status'], 'NOT_RUN')

    def test_equivalence_timeout_stops_remaining_sources(self):
        self.fail = ('equivalence', 'common', 'RESOURCE_TIMEOUT')
        r = self.stage('equivalence')
        self.assertEqual(r['sources']['common']['status'], 'INCOMPLETE')
        self.assertEqual(r['sources']['seeded']['status'], 'NOT_RUN')
        with self.assertRaisesRegex(ValueError, 'equivalence resource failure'):
            self.stage('qualification')
        self.assertFalse((self.root/'qualification').exists())

    def test_deadline_blocks_preparation_and_formal_without_eligible_source(self):
        self.t = datetime.fromisoformat(DEADLINE)
        r = self.stage('equivalence')
        self.assertFalse(self.calls)
        self.assertEqual(r['sources']['common']['status'], 'INCOMPLETE')
        self.stage('qualification'); self.stage('calibration')
        with self.assertRaisesRegex(ValueError, 'no source'):
            self.stage('formal')
        self.assertFalse((self.root/'formal').exists())

    def test_source_budget_exhaustion_and_not_run_reason(self):
        self.stage('equivalence')
        tick = [0]
        def advance():
            tick[0] += 2000
            return tick[0]
        with patch.object(runner.time, 'monotonic', side_effect=advance):
            r = self.stage('qualification')
        self.assertEqual(r['sources']['targeted_split']['status'], 'INCOMPLETE')
        self.assertTrue(r['sources']['targeted_split']['resource_failure'])
        self.assertEqual(read_records(self.root/'qualification/sources/targeted_split')[0]['reason'], 'source_budget')

    def test_single_sources_can_supply_one_merged_preparation(self):
        for s in SOURCE_ORDER:
            self.stage('equivalence', s, name='eq-' + s)
        r = self.stage('qualification', equivalence=[self.root/('eq-' + s) for s in SOURCE_ORDER])
        self.assertTrue(r['complete'])

    def test_duplicate_attempt_prerequisites_rejected(self):
        self.stage('equivalence')
        with self.assertRaisesRegex(ValueError, 'multiple prerequisite attempts'):
            self.stage('qualification', equivalence=[self.root/'equivalence']*2)

    def test_environment_and_receipt_gates_before_workers(self):
        self.env['execution']['dirty'] = True
        with self.assertRaisesRegex(RuntimeError, 'freeze'):
            self.stage('equivalence')
        self.assertFalse(self.calls)
        self.env['execution']['dirty'] = False
        self.env['execution']['hardware'].update(power="Now drawing from 'Battery Power'", power_source='Battery Power')
        with self.assertRaisesRegex(RuntimeError, 'AC power'):
            self.stage('equivalence')
        self.env['execution']['hardware'].update(POWER)
        self.prepare()
        with self.assertRaisesRegex(ValueError, 'receipt'):
            self.stage('formal', review=None)
        self.assertFalse((self.root/'formal').exists())

    def test_summaries_are_ignored_raw_records_control_results(self):
        self.prepare(); self.stage('formal')
        out = self.root/'formal'
        for p in out.rglob('summary.json'):
            p.write_text('not even JSON; independently ignored')
        atomic_json(out/'summary.json', {'tree_faster':999})
        seal(out)
        r = checker.validate(out)
        self.assertEqual(r['sources']['common']['statistics']['TEST_ONLY--common']['tree_over_list_median'], 2)
        s = analysis.analyze(out, self.root/'analysis')
        self.assertEqual(s['overall']['tree_faster'], 2)
        raw = out/'sources/common/jobs/TEST_ONLY--common/records/000010.json.gz'
        row = json.loads(gzip.decompress(raw.read_bytes())); row['round'] = 19
        atomic_bytes(raw, gzip.compress(canonical(row), mtime=0)); seal(out)
        with self.assertRaises(ValueError):
            checker.validate(out)

    def test_request_and_status_tampering_rejected(self):
        self.stage('equivalence')
        p = self.root/'equivalence/sources/common/requests/TEST_ONLY--common.json'
        row = read(p); row['entry']['values'][0] = 99; atomic_json(p, row); seal(self.root/'equivalence')
        with self.assertRaisesRegex(ValueError, 'request binding'):
            checker.validate(self.root/'equivalence')

    def test_source_mutation_marker_rejected(self):
        self.stage('equivalence')
        atomic_json(self.root/'equivalence/source_failure.json', {'accepted':False}); seal(self.root/'equivalence')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            checker.validate(self.root/'equivalence')

    def test_source_timeout_retains_later_input_as_not_run(self):
        extra = copy.deepcopy(self.suite['entries'][0])
        extra.update(case_id='TEST_ONLY--common-second', canonical_case_id='TEST_ONLY--common-second',
                     values=list(range(1, 10)), n=9, input_sha256=digest(list(range(1, 10))))
        self.suite['entries'].insert(1, extra)
        self.traces[extra['case_id']] = digest(checked(extra['values'], backend_spec('heterogeneous_finger'))[0]['trace'])
        self.stage('equivalence')
        self.fail = ('qualification', 'common', 'RESOURCE_TIMEOUT')
        r = self.stage('qualification')
        self.assertEqual([c['status'] for c in r['sources']['common']['cases']], ['TIMEOUT','NOT_RUN'])
        self.assertEqual(r['sources']['seeded']['status'], 'COMPLETE')

    def test_no_common_batch_is_error_not_timeout(self):
        self.stage('equivalence'); self.stage('qualification')
        self.fail = ('calibration', 'common', 'NO_COMMON_BATCH')
        r = self.stage('calibration')
        self.assertTrue(r['hard_error'])
        self.assertEqual(r['sources']['common']['status'], 'ERROR')
        self.assertEqual(r['sources']['targeted_split']['status'], 'NOT_RUN')

    def test_formal_error_reports_only_previously_complete_sources(self):
        self.prepare()
        self.fail = ('formal', 'targeted_split', 'WORKER_ERROR')
        self.stage('formal')
        s = analysis.analyze(self.root/'formal', self.root/'partial')
        self.assertTrue(s['session_hard_error'])
        self.assertFalse(s['all_sources_complete'])
        self.assertEqual(s['actual_timed_inputs'], 1)

    def test_mixed_prerequisite_attempt_chain_rejected(self):
        self.stage('equivalence')
        self.stage('qualification')
        self.stage('equivalence', name='other-equivalence')
        with self.assertRaisesRegex(ValueError, 'inconsistent prerequisite chain'):
            self.stage('calibration', equivalence=[self.root/'other-equivalence'])

    def test_old_schema_and_foreign_environment_rejected(self):
        self.stage('equivalence')
        cfg = read(self.root/'equivalence/config.json')
        cfg['schema'] = 'uninstrumented_equivalence_v1'
        atomic_json(self.root/'equivalence/config.json', cfg); seal(self.root/'equivalence')
        with self.assertRaisesRegex(ValueError, 'schema/stage'):
            self.stage('qualification')
        cfg['schema'] = profile(self.suite, 'equivalence', 'all')['schema']
        atomic_json(self.root/'equivalence/config.json', cfg); seal(self.root/'equivalence')
        self.env['execution']['platform'] = 'macOS different fixture'
        with self.assertRaisesRegex(ValueError, 'environment/source mismatch'):
            self.stage('qualification')

    def test_false_early_budget_skip_and_hidden_job_rejected(self):
        self.stage('equivalence', 'common')
        out = self.root/'equivalence'
        rowpath = out/'sources/common/records/000000.json.gz'
        row = json.loads(gzip.decompress(rowpath.read_bytes()))
        row.update(status='NOT_RUN', reason='equivalence_budget', budget_seconds=0, worker_wall_seconds=0)
        atomic_bytes(rowpath, gzip.compress(canonical(row), mtime=0)); seal(out)
        with self.assertRaisesRegex(ValueError, 'early equivalence budget'):
            checker.validate(out)

    def test_tampered_budget_and_equivalence_cursor_rejected(self):
        self.stage('equivalence')
        out = self.root/'equivalence'
        path = out/'sources/common/jobs/TEST_ONLY--common/progress.json'
        atomic_json(path, dict(status='COMPLETE', committed_records=2)); seal(out)
        with self.assertRaisesRegex(ValueError, 'completion cursor'):
            checker.validate(out)

    def test_empty_summary_and_smaller_side_distribution(self):
        self.assertIsNone(analysis.ratio_summary([])['median'])
        result = analysis.structure_summary([dict(S_i=0, I_i=0, smaller_sides=[]),
                                            dict(S_i=4, I_i=3, smaller_sides=[1, 1, 3])])
        self.assertEqual(result['smaller_side_histogram'], {'1':2, '3':1})
        self.assertEqual(result['inputs_with_no_split'], 1)
        self.assertEqual(result['smaller_side_median'], 1)


if __name__ == '__main__':
    unittest.main()
