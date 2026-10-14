import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import matched_backend_fixture as runner
from validate_matched_backend_fixture import validate
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree
import paper_jordan as core
from partial_sorted_list import SortedOrderList


class MatchedBackendFixtureTests(unittest.TestCase):
    values=[1,2,3,4,6,7,0,5]

    def directory(self):
        temporary=tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        return Path(temporary.name)/'fixture'

    def seal(self,path):
        names=('config.json','environment.json','raw.jsonl','summary.json')
        (path/'manifest.json').write_bytes(runner.canonical({n:hashlib.sha256((path/n).read_bytes()).hexdigest() for n in names}))

    def rewrite(self,path,name,update):
        value=json.loads((path/name).read_text()); update(value)
        (path/name).write_bytes(runner.canonical(value)); self.seal(path)

    def test_actual_two_backend_fixture_and_independent_summary_rebuild(self):
        path=self.directory()
        self.assertTrue(runner.run([self.values,[-x for x in self.values]],path))
        report=validate(path)
        self.assertTrue(report['completed_successfully'])
        self.assertFalse(report['performance_eligible'])
        self.assertEqual(report['rows'],18)
        rows=[json.loads(line) for line in (path/'raw.jsonl').read_text().splitlines()]
        samples=[r for r in rows if r['kind']=='sample']
        self.assertEqual(len(samples),8)
        self.assertTrue(all(r['synthetic_ticks']==1 for r in samples))

    def test_initializer_and_output_recovery_are_between_clock_boundaries(self):
        active=False; events=[]
        def clock():
            nonlocal active
            active=not active; events.append('start' if active else 'stop'); return len(events)
        initialize=core._initialize_paper_jordan_state_values
        recover=SortedOrderList.to_list
        def init(*a,**kw):
            self.assertTrue(active); events.append('init'); return initialize(*a,**kw)
        def output(state):
            self.assertTrue(active); events.append('recover'); return recover(state)
        with patch.object(core,'_initialize_paper_jordan_state_values',init),patch.object(SortedOrderList,'to_list',output):
            result=runner.trial(self.values,'heterogeneous_finger',sorted(self.values),clock)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(events,['start','init','recover','stop'])
        self.assertFalse(active)

    def test_each_trial_constructs_fresh_unobserved_tree(self):
        original=Tree.__init__; instances=[]
        def construct(b,*a,**kw):
            original(b,*a,**kw); instances.append(b)
        with patch.object(Tree,'__init__',construct):
            for _ in range(3):
                self.assertEqual(runner.trial(self.values,'heterogeneous_finger',sorted(self.values),runner.FixtureClock())['status'],'PASS')
        self.assertEqual(len(instances),3)
        self.assertTrue(all(not b.detailed_work and b.work.buckets is None for b in instances))
        self.assertEqual(len({id(b._nodes) for b in instances}),3)

    def test_wrong_output_is_retained_and_stops_remaining_schedule(self):
        path=self.directory()
        with patch.object(runner,'paper_jordan_sort_valid',return_value=[99]):
            self.assertFalse(runner.run([self.values],path))
        report=validate(path); self.assertFalse(report['completed_successfully'])
        rows=[json.loads(line) for line in (path/'raw.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows),4)
        self.assertEqual(rows[-1]['output'],[99])
        self.assertEqual(rows[-1]['error']['type'],'OutputMismatch')

    def test_exception_is_retained_and_clock_closes(self):
        path=self.directory()
        with patch.object(runner,'paper_jordan_sort_valid',side_effect=RuntimeError('injected')):
            self.assertFalse(runner.run([self.values],path))
        self.assertFalse(validate(path)['completed_successfully'])
        row=json.loads((path/'raw.jsonl').read_text().splitlines()[-1])
        self.assertEqual(row['synthetic_ticks'],1)
        self.assertEqual(row['error'],{'type':'RuntimeError','message':'injected'})

    def test_illegal_input_remains_in_evidence(self):
        path=self.directory(); values=[0,1,0]
        self.assertFalse(runner.run([values],path))
        self.assertFalse(validate(path)['completed_successfully'])
        self.assertEqual(json.loads((path/'summary.json').read_text())['rows'],1)
        self.assertEqual(json.loads((path/'config.json').read_text())['inputs'][0]['values'],values)

    def test_disabled_stage_and_existing_directory_cannot_run(self):
        path=self.directory()
        for stage in ('pilot','formal'):
            with self.assertRaisesRegex(RuntimeError,'disabled'):runner.run([self.values],path,stage)
        self.assertFalse(path.exists())
        runner.run([self.values],path)
        with self.assertRaises(FileExistsError): runner.run([self.values],path)

    def test_validator_rejects_resealed_backend_mode_and_source_changes(self):
        for file,update in (
            ('config.json',lambda x:x['protocol'].update(tree_detailed_work=True)),
            ('config.json',lambda x:x['protocol'].update(tree_detailed_work=0)),
            ('config.json',lambda x:x['protocol'].update(execution_mode='checked')),
            ('config.json',lambda x:x['protocol'].update(stage='formal')),
            ('config.json',lambda x:x['backends']['heterogeneous_finger'][3][0].__setitem__(1,True)),
            ('environment.json',lambda x:x.update(source_sha256={})),
            ('summary.json',lambda x:x['summary']['heterogeneous_finger'].update(samples=100)),
        ):
            with self.subTest(file=file):
                path=self.directory();runner.run([self.values],path)
                self.rewrite(path,file,update)
                with self.assertRaises(ValueError):validate(path)

    def test_validator_rejects_duplicate_or_missing_or_incorrect_rows(self):
        for kind in ('duplicate','missing','output','boolean_output','identity','timing'):
            with self.subTest(kind=kind):
                path=self.directory();runner.run([self.values],path)
                rows=[json.loads(x) for x in (path/'raw.jsonl').read_text().splitlines()]
                if kind=='duplicate':rows[-1]=rows[-2]
                elif kind=='missing':rows.pop()
                elif kind=='output':rows[-1]['output']=[99]
                elif kind=='boolean_output':rows[-1]['output'][0]=False
                elif kind=='identity':rows[-1]['backend_identity']=None
                else: rows[-1]['synthetic_ticks']=100000
                (path/'raw.jsonl').write_bytes(b'\n'.join(runner.canonical(r) for r in rows)+b'\n');self.seal(path)
                with self.assertRaises(ValueError):validate(path)

    def test_manifest_detects_unsealed_change(self):
        path=self.directory();runner.run([self.values],path)
        with (path/'raw.jsonl').open('a') as stream:stream.write('\n')
        with self.assertRaisesRegex(ValueError,'hash'):validate(path)


if __name__=='__main__': unittest.main()
