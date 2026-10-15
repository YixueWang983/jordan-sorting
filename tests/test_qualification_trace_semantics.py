"""Actual small traces corrupted on copies; no physical-tree proof by archive."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments')]
import copy,gzip,json,tempfile,unittest
from unittest.mock import patch
from committed_records import read_records,atomic_bytes,canonical
import qualify_common_inputs_v2 as runner
import validate_common_qualification_v2 as checker
from validate_finger_middle_splits import values_for
from common_input_protocol import digest
from qualification_trace_semantics import check_trace


class TraceSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.output=Path(cls.temp.name)/'run'
        cls.request=dict(case='small-split',values=values_for(32,3,False),backends=list(runner.BACKENDS))
        if runner.qualify_case(cls.request,cls.output)!=0:raise RuntimeError('small flow failed')
        cls.rows=read_records(cls.output)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def mutate(self,kind):
        row=copy.deepcopy(self.rows[2]);events=row['final']['trace'];metrics=row['final']['metrics']
        performed=next(e for e in events if e.get('performed') is True)
        skipped=next(e for e in events if e.get('performed') is False)
        if kind=='zero-source':performed.update(input_size=0,left_size=0,right_size=0,left_list_id=None,right_list_id=None)
        elif kind=='nonempty-no-ids':performed.update(input_size=2,left_size=1,right_size=1,left_list_id=None,right_list_id=None)
        elif kind=='skip-nonzero':skipped.update(input_size=1,left_size=1,right_size=0)
        elif kind=='skip-id':skipped['input_list_id']=1
        elif kind=='empty-has-id':performed.update(left_size=0,right_size=performed['input_size'],left_list_id=999)
        elif kind=='alias-output':performed.update(input_size=2,left_size=1,right_size=1,left_list_id=999,right_list_id=999)
        elif kind=='non-split-empty':events[:]=[e if e.get('step')=='step3b_split_sibling_list' else {} for e in events]
        elif kind=='swap-steps':events[2],events[4]=events[4],events[2]
        elif kind=='missing-field':del events[6]['parent_pair_id']
        elif kind=='wrong-counter':metrics['predecessor_accesses']+=1
        elif kind=='bool-id':performed['input_list_id']=True
        elif kind=='wrong-initialization':events[0]['point_ids'].reverse()
        elif kind=='wrong-owner':performed['input_list_id']=events[2+7*(performed['iteration']-4)+4]['sibling_list_id']
        return row

    def test_actual_trace_and_derived_coverage(self):
        for row in (self.rows[0],self.rows[2]):
            report=check_trace(self.request['values'],row['final']['trace'],row['final']['metrics'],row['backend'])
            self.assertTrue(any(s['smaller_side']==3 for s in report['splits']))
            self.assertFalse(report['physical_tree_proof'])

    @staticmethod
    def replace_list_id(events, start, old, new):
        # Rename all later references too: an unrelated stale-reference error
        # must not be what rejects a reused ID.
        fields=('sibling_list_id','input_list_id','left_list_id','right_list_id')
        for event in events[start:]:
            for key in fields:
                if event.get(key)==old:event[key]=new

    def reject_lifecycle_mutation(self, mutate, message):
        for index in (0,2):
            with self.subTest(backend=self.rows[index]['backend']):
                rows=copy.deepcopy(self.rows);mutate(rows[index]['final']['trace'])
                with patch.object(checker,'read_records',return_value=rows),self.assertRaisesRegex(ValueError,message):
                    checker.validate_job(self.output,self.request,digest(self.request['values']),passing=True)

    def test_split_outputs_cannot_reuse_source_id(self):
        for side in ('left','right'):
            def mutate(events):
                at=next(j for j,e in enumerate(events) if e.get('performed') is True)
                self.replace_list_id(events,at,events[at][side+'_list_id'],events[at]['input_list_id'])
            with self.subTest(side=side):
                self.reject_lifecycle_mutation(mutate,'split output reuses an allocated list ID')

    def test_singleton_cannot_reuse_retired_id(self):
        def mutate(events):
            at=next(j for j,e in enumerate(events) if e.get('performed') is True)
            retired=events[at]['input_list_id']
            later=next(j for j in range(at+1,len(events)) if events[j].get('insertion_mode')=='singleton_list')
            self.replace_list_id(events,later,events[later]['sibling_list_id'],retired)
        self.reject_lifecycle_mutation(mutate,'singleton reuses an allocated list ID')

    def test_later_split_cannot_reuse_previously_retired_id(self):
        def mutate(events):
            first,later=[j for j,e in enumerate(events) if e.get('performed') is True]
            old=events[later]['left_list_id'] or events[later]['right_list_id']
            self.replace_list_id(events,later,old,events[first]['input_list_id'])
        self.reject_lifecycle_mutation(mutate,'split output reuses an allocated list ID')

    def test_boundary_insertion_keeps_live_id_without_requiring_monotone_ids(self):
        for row in self.rows[::2]:
            trace=copy.deepcopy(row['final']['trace'])
            fields=('upper_list_id','lower_list_id','sibling_list_id','input_list_id','left_list_id','right_list_id')
            allocated={e[k] for e in trace for k in fields if e.get(k) is not None}
            rename={old:1000-old for old in allocated}
            for event in trace:
                for key in fields:
                    if event.get(key) is not None:event[key]=rename[event[key]]
            insertions=[e['sibling_list_id'] for e in trace if e.get('insertion_mode')=='boundary_insertion']
            self.assertGreater(len(insertions),len(set(insertions)))
            check_trace(self.request['values'],trace,row['final']['metrics'],row['backend'])

    def test_all_review_counterexamples_rejected_by_validate_job(self):
        kinds=('zero-source','nonempty-no-ids','skip-nonzero','skip-id','empty-has-id','alias-output',
               'non-split-empty','swap-steps','missing-field','wrong-counter','bool-id','wrong-initialization','wrong-owner')
        for kind in kinds:
            with self.subTest(kind=kind):
                rows=copy.deepcopy(self.rows);rows[2]=self.mutate(kind)
                with patch.object(checker,'read_records',return_value=rows),self.assertRaises(ValueError):
                    checker.validate_job(self.output,self.request,digest(self.request['values']),passing=True)

    def test_historical_revision_bound_to_git_not_current_checkout(self):
        old=ROOT/'docs/validation/common_qualification_v2_20261015/qualification/environment.json'
        env=json.loads(old.read_text())
        checker.validate_environment(env,historical=True)
        with self.assertRaises(ValueError):checker.validate_environment(env)
        for kind in ('hash','path','head'):
            bad=copy.deepcopy(env)
            if kind=='hash':bad['source_sha256']['src/paper_jordan.py']='0'*64
            elif kind=='path':bad['source_sha256']['../secret.py']='0'*64
            else:bad['head']='0'*40
            with self.subTest(kind=kind),self.assertRaises(ValueError):checker.validate_environment(bad,historical=True)


if __name__=='__main__':unittest.main()
