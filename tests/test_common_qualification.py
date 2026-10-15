"""Selection and evidence mechanics; stub archives are not backend evidence."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'experiments')]
import gzip
import hashlib
import json
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import common_input_protocol as protocol
import qualify_common_inputs as runner
import validate_common_qualification as checker
from committed_records import atomic_json, atomic_bytes, canonical, read_records, run_bounded


class CommonQualificationTests(unittest.TestCase):
    def directory(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return Path(temp.name)/'run'

    def fixture(self, output, failing=None):
        specs = [s for s in protocol.candidate_specs() if s['n'] == 32]
        def diagnostics(values, *, backend):
            return dict(output=sorted(values), processed_count=len(values), invariants_valid=True,
                        backend_identity=backend.identity, metrics={}, trace=[])
        def bounded(command, directory, seconds):
            request = runner.read(Path(command[command.index('--worker')+1]))
            if failing and request['case'] == failing:
                directory.mkdir()
                atomic_json(directory/'progress.json', {'status':'RUNNING'})
                atomic_json(directory/'failure.json', {'accepted':False,'status':'RESOURCE_TIMEOUT'})
                return 2
            return runner.qualify_case(request, directory)
        env = runner.environment(); env['dirty'] = False
        with patch.object(runner, 'candidate_specs', return_value=iter(specs)), patch.object(runner, 'environment', return_value=env), \
             patch.object(runner, 'run_bounded', side_effect=bounded), \
             patch.object(runner, 'paper_jordan_diagnostics_valid', side_effect=diagnostics), \
             patch.object(runner, 'paper_jordan_sort_valid', side_effect=lambda values,*a,**k:sorted(values)):
            passed = runner.run(output)
        return passed, specs

    def validate_fixture(self, output, specs):
        with patch.object(checker, 'candidate_specs', return_value=iter(specs)):
            return checker.validate(output)

    def test_fixed_selection_reaches_all_cells_and_records_mirror_dependencies(self):
        output = self.directory(); output.mkdir()
        selected = runner.select(output, time.monotonic()+180)
        self.assertEqual(len(selected['cases']), 140)
        self.assertEqual(selected['deficits'], [])
        self.assertEqual(len({c['input_sha256'] for c in selected['cases']}), 140)
        for c in selected['cases']:
            self.assertEqual(c['profile']['category'], c['spec']['requested_category'])
            if c['spec']['mirror']:
                self.assertTrue(any(b['spec']['case'] == c['spec']['base_id'] for b in selected['cases']))

    def test_real_backends_checked_replay_and_fresh_minimal(self):
        output = self.directory()
        values = [1,2,3,4,6,7,0,5]
        request = dict(case='real-test-only', values=values, backends=list(protocol.BACKENDS))
        self.assertEqual(runner.qualify_case(request, output), 0)
        rows = read_records(output)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r['status'] == 'PASS' and r['output'] == sorted(values) for r in rows))
        self.assertTrue(all(rows[i]['same_backend_replay'] for i in (0,2)))
        self.assertFalse(dict(rows[2]['backend_identity'][3])['detailed_work'])

    def test_bad_checked_count_stops_before_minimal(self):
        for count in (True, 3.0, 2):
            output = self.directory()
            request = dict(case='bad-count', values=[1,2,3], backends=list(protocol.BACKENDS))
            result = dict(output=[1,2,3], processed_count=count, invariants_valid=True,
                          backend_identity=runner.identity('ordinary_list'))
            with patch.object(runner, 'paper_jordan_diagnostics_valid', return_value=result), \
                 patch.object(runner, 'paper_jordan_sort_valid') as minimal:
                self.assertEqual(runner.qualify_case(request, output), 2)
                minimal.assert_not_called()
            self.assertEqual(read_records(output)[0]['status'], 'ERROR')

    def test_wrong_minimal_output_retained(self):
        output = self.directory()
        request = dict(case='bad-output', values=[1,2,3], backends=list(protocol.BACKENDS))
        with patch.object(runner, 'paper_jordan_sort_valid', return_value=[99]):
            self.assertEqual(runner.qualify_case(request, output), 2)
        rows = read_records(output)
        self.assertEqual(len(rows), 2); self.assertEqual(rows[1]['output'], [99])
        self.assertEqual(rows[1]['status'], 'ERROR')

    def test_rebuild_qualification_without_performance_acceptance(self):
        output = self.directory(); passed, specs = self.fixture(output)
        self.assertTrue(passed)
        report = self.validate_fixture(output, specs)
        self.assertTrue(report['all_selected_qualified'])
        self.assertEqual(report['public_executions'], 56)
        self.assertFalse(report['performance_eligible'])
        self.assertFalse(report['coverage_target_met'])

    def test_timeout_does_not_drop_selected_case_or_continue(self):
        output = self.directory(); passed, specs = self.fixture(output, 'n32-strict_flat-00-mirror')
        self.assertFalse(passed)
        rows = read_records(output)
        self.assertEqual([r['status'] for r in rows[:3]], ['PASS','TIMEOUT','NOT_RUN'])
        self.assertEqual(len(rows), 14)
        self.assertFalse(self.validate_fixture(output, specs)['all_selected_qualified'])

    def test_resealed_corruption_rejected(self):
        import shutil
        source = self.directory(); _, specs = self.fixture(source)
        for kind in ('bool-count','missing-mode','tree-config','selected','summary','environment','extra-directory'):
            with self.subTest(kind=kind):
                output = self.directory(); shutil.copytree(source, output)
                first = read_records(output)[0]['case']
                job = output/'jobs'/first
                if kind in ('bool-count','tree-config'):
                    path = job/'records/000002.json.gz'; row = json.loads(gzip.decompress(path.read_bytes()))
                    if kind == 'bool-count': row['processed_count'] = True
                    else: row['backend_identity'] = runner.identity('ordinary_list')
                    atomic_bytes(path, gzip.compress(canonical(row), mtime=0))
                elif kind == 'missing-mode': (job/'records/000003.json.gz').unlink()
                elif kind == 'selected':
                    doc = runner.read(output/'selected.json'); doc['cases'].pop(); atomic_json(output/'selected.json', doc)
                elif kind == 'summary':
                    doc = runner.read(output/'summary.json'); doc['all_selected_qualified'] = False; atomic_json(output/'summary.json', doc)
                elif kind == 'environment':
                    doc = runner.read(output/'environment.json'); del doc['hardware']; atomic_json(output/'environment.json', doc)
                else: (output/'extra').mkdir()
                runner.seal(output)
                with self.assertRaises(ValueError): self.validate_fixture(output, specs)

    def test_actual_termination_keeps_completed_checked_record(self):
        output = self.directory(); script = output.parent/'worker.py'
        script.write_text('''import sys,time
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1])/'experiments'))
import qualify_common_inputs as q
def blocked(*a,**kw): time.sleep(30)
q.paper_jordan_sort_valid=blocked  # Non-sorting timeout fixture only.
raise SystemExit(q.qualify_case(dict(case='timeout',values=[1,2,3],backends=list(q.BACKENDS)),Path(sys.argv[2])))
''')
        self.assertEqual(run_bounded([sys.executable,str(script),str(ROOT),str(output)],output,2),2)
        rows = read_records(output)
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]['mode'],'checked')
        failure = runner.read(output/'failure.json')
        self.assertEqual(failure['current']['action']['mode'],'minimal')

    def test_optimized_entries_rejected(self):
        for entry in ('common_input_protocol.py','qualify_common_inputs.py','validate_common_qualification.py'):
            result = subprocess.run([sys.executable,'-O',str(ROOT/'experiments'/entry),'--help'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('optimization level 0',result.stderr)


if __name__ == '__main__': unittest.main()
