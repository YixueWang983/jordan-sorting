"""Review regressions: real worker timeout persistence and two proof examples."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'experiments')]
from committed_records import read_records,run_bounded
from finger_refinement_model import check_run,decode_tree,next_plan
from heterogeneous_finger_split import TreeOperations
from paper_execution_policy import MINIMAL_POLICY
from oracle import oracle
from test_finger_refinement import TREE_OFF
from test_heterogeneous_finger_backend import Fixture
from sibling_list_backend import RIGHT


class TimeoutPersistenceTests(unittest.TestCase):
    def exercise(self,mode):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        base=Path(temporary.name);output=base/'archive';worker=base/'worker.py'
        worker.write_text('''import sys,time,json
from pathlib import Path
sys.path[:0]=[str(Path(sys.argv[1])/'experiments'),str(Path(sys.argv[1])/'tests'),str(Path(sys.argv[1])/'src')]
import validate_finger_refinement as runner
from committed_records import atomic_json
mode=sys.argv[2];output=Path(sys.argv[3])
runner.cases=lambda:iter([('first',[1,2,3]),('second',[1,2,3,4])])
def fake_run(values,backend,policy):
    # Explicit non-sorting fixture: exercise original run()/record control flow.
    if len(values)==4:
        if mode=='exception':raise RuntimeError('deliberate second-case failure')
        if mode=='partial':(output/'records'/'unfinished.partial').write_bytes(b'incomplete')
        if mode=='late_summary':atomic_json(output/'summary.json',{'accepted':True})
        if mode in ('timeout','partial','late_summary'):time.sleep(30)
    return None,{'prefixes':len(values)-2,'iterations':len(values)-3}
runner.check_run=fake_run
try:runner.run(output)
except Exception:raise SystemExit(3)
''')
        code=run_bounded([sys.executable,str(worker),str(ROOT),mode,str(output)],output,2)
        return code,output

    def test_normal_exit_closes_each_of_two_records(self):
        code,out=self.exercise('normal')
        self.assertEqual(code,0)
        self.assertEqual([r['case'] for r in read_records(out)],['first','second'])
        self.assertTrue(json.loads((out/'summary.json').read_text())['accepted'])

    def test_python_exception_preserves_first_record_and_current_case(self):
        code,out=self.exercise('exception')
        self.assertEqual(code,2)
        self.assertEqual([r['case'] for r in read_records(out)],['first'])
        failure=json.loads((out/'failure.json').read_text())
        self.assertEqual(failure['current']['case'],'second')
        self.assertEqual(failure['committed_records'],1)
        self.assertFalse(failure['accepted'])

    def test_real_process_timeout_preserves_first_complete_gzip(self):
        code,out=self.exercise('timeout')
        self.assertEqual(code,2)
        self.assertEqual([r['case'] for r in read_records(out)],['first'])
        failure=json.loads((out/'failure.json').read_text())
        self.assertEqual(failure['status'],'RESOURCE_TIMEOUT')
        self.assertEqual(failure['current']['case'],'second')
        self.assertEqual(failure['committed_records'],1)
        self.assertFalse((out/'summary.json').exists())

    def test_interrupted_partial_record_is_not_counted_or_needed_for_recovery(self):
        code,out=self.exercise('partial')
        self.assertEqual(code,2)
        self.assertEqual(len(read_records(out)),1)
        self.assertTrue((out/'records'/'unfinished.partial').exists())
        self.assertEqual(json.loads((out/'failure.json').read_text())['committed_records'],1)

    def test_timeout_overrides_summary_written_before_worker_exit(self):
        code,out=self.exercise('late_summary')
        self.assertEqual(code,2)
        self.assertFalse(json.loads((out/'summary.json').read_text())['accepted'])
        self.assertEqual(len(read_records(out)),1)


class ProofScopeRegressions(unittest.TestCase):
    def test_new_endpoint_inside_finite_owner_but_outside_its_direct_children(self):
        values=[10,1,9,8,5,4,3,6]
        self.assertTrue(oracle(values)['valid'])
        plan=next_plan(values,7)
        self.assertEqual(plan['owner'],2)
        self.assertEqual(plan['source'],(6,4))
        self.assertEqual(plan['acquired'],(6,))
        self.assertTrue(1<values[-1]<10)
        for backend in ('ordinary_list',TREE_OFF):
            check_run(values,backend,MINIMAL_POLICY)

    def test_located_component_can_be_strictly_on_one_side_without_equal_key(self):
        f=Fixture();b=f.backend
        a,c=f.pair(4,5),f.pair(8,9)
        lid=b.make_list(a.pair_id,-1);b.insert_boundary(c.pair_id,a.pair_id,RIGHT)
        header=b._lists[lid];ops=TreeOperations(b)
        side,top,size=ops.locate_component(header,6)
        self.assertEqual((side,top.key,size),(RIGHT,8,1))
        left,right=ops.split(header,6)
        self.assertEqual([leaf.key for leaf in decode_tree(left)[1]],[4])
        self.assertEqual([leaf.key for leaf in decode_tree(right)[1]],[8])


if __name__=='__main__':unittest.main()
