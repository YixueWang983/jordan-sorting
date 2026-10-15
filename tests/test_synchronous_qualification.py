"""Legacy predicates, fresh audits, isolation and v2 scheduling regressions."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'experiments')]
from dataclasses import replace
import itertools
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import paper_jordan as core
from paper_jordan_validation import run_synchronous_qualification, require_independent
from heterogeneous_finger_backend import HeterogeneousFingerBackend as Tree, InternalNode
from matched_backend_fixture import backend_spec
from paper_execution_policy import CHECKED_POLICY
from oracle import oracle


def view(state, snapshots):
    return (snapshots, state.partial_order.to_list(), dict(state.pair_by_end_index),
            dict(state.metrics), list(state.trace), dict(state.stage_results), dict(state.backend_work))


class SynchronousQualificationTests(unittest.TestCase):
    values = [1,2,3,4,6,7,0,5]

    def state(self, values=None, name='heterogeneous_finger'):
        return core._run_paper_jordan_state_values(list(values or range(1,17)), backend=backend_spec(name))

    def test_reverse_deletion_matches_legacy_predictions_all_orders_through_seven(self):
        for n in range(3,8):
            state = SimpleNamespace(upper_dummy_pair_id=-1, lower_dummy_pair_id=-2,
                                    pair_by_end_index={i:i for i in range(2,n+1)})
            for order in itertools.permutations(range(1,n+1)):
                facts = core._historical_neighbors(order)
                for i in range(4,n+1):
                    for side in (True,False):
                        self.assertEqual(core._expected_boundary_selection(state,i,order,side),
                                         core._expected_boundary_selection(state,i,order,side,history=facts))
                    prefix = [p for p in order if p <= i]; j = prefix.index(i)
                    self.assertEqual(facts[i][2:], (prefix[j-1] if j else None,
                                     prefix[j+1] if j+1<len(prefix) else None))

    def test_new_old_prefix_views_and_metrics_equal_for_legal_small_inputs(self):
        cases = [list(p) for n in range(3,7) for p in itertools.permutations(range(n)) if oracle(p)['valid']]
        cases += [self.values, [-x for x in self.values], [10,1,9,8,5,4,3,6]]
        for name in ('ordinary_list','heterogeneous_finger'):
            for values in cases:
                old = []
                def reference(s):
                    snapshots = core.validate_paper_jordan_state_reference(s, return_snapshots=True)
                    old.append(view(s,snapshots))
                core._run_paper_jordan_state_values(values, backend=backend_spec(name), invariant_callback=reference)
                new = []
                state, report = run_synchronous_qualification(values, backend=backend_spec(name),
                    prefix_callback=lambda s,v:new.append(view(s,v)))
                self.assertEqual(old,new)
                self.assertEqual(state.partial_order.to_list(),sorted(values))
                self.assertEqual(report['prefix_comparisons'],len(values)-2)
                self.assertEqual(report['initialized_instances'],3)

    def test_each_call_audits_again_after_direct_physical_corruption(self):
        for field in ('rank','span','owner','reverse'):
            for validate in (core.validate_paper_jordan_state, core._validate_state_local,
                             core.validate_paper_jordan_state_reference):
                with self.subTest(field=field,check=validate.__name__):
                    state=self.state(); validate(state)
                    b=state.sibling_backend; header=next(iter(b._lists.values()))
                    if field=='rank': header.root.rank+=1
                    elif field=='span': header.root.span+=1
                    elif field=='owner': header.owner=b._pairs[2]
                    else: header.left_finger.left=header.left_finger
                    with self.assertRaises(RuntimeError): validate(state)

    def test_old_stage_and_trace_mutations_are_not_hidden_by_a_cache(self):
        for kind in ('stage','trace'):
            for validate in (core.validate_paper_jordan_state,core._validate_state_local,
                             core.validate_paper_jordan_state_reference):
                state=self.state(); validate(state)
                if kind=='trace': state.trace[2]['neighbor_point_id']=99
                else:
                    result=state.stage_results[4]['step3c_insert_output_point']
                    state.stage_results[4]['step3c_insert_output_point']=replace(result,output_anchor_point_id=99)
                with self.assertRaises(RuntimeError): validate(state)

    def test_single_call_bundle_runs_one_audit_and_does_not_store_results(self):
        state=self.state(); b=state.sibling_backend; audit=Tree._audit; calls=[]
        def observed(instance,*a,**k): calls.append(instance); return audit(instance,*a,**k)
        with patch.object(Tree,'_audit',observed):
            one=b.validated_snapshots(); two=b.validated_snapshots()
        self.assertEqual(one,two); self.assertEqual(calls,[b,b])
        self.assertFalse(any('cache' in k or 'validated' in k for k in vars(b)))

    def test_isolation_and_no_ordinary_backend_fallback(self):
        from sibling_list_backend import OrdinarySiblingListBackend
        created=[]; init=Tree.__init__
        def construct(b,*a,**kw): init(b,*a,**kw); created.append(b)
        with patch.object(Tree,'__init__',construct), patch.object(OrdinarySiblingListBackend,'__init__',side_effect=AssertionError('fallback')):
            state,report=run_synchronous_qualification(self.values,backend=backend_spec('heterogeneous_finger'))
        self.assertEqual(len(created),3)
        self.assertTrue(all(b.execution_policy is CHECKED_POLICY and not b.detailed_work for b in created))
        for a,b in itertools.combinations(created,2):
            for field in ('_pairs','_lists','_nodes'):
                self.assertIsNot(getattr(a,field),getattr(b,field))
                self.assertFalse({id(x) for x in getattr(a,field).values()} & {id(x) for x in getattr(b,field).values()})
        first=self.state(); second=self.state(); second.sibling_backend._nodes=first.sibling_backend._nodes
        with self.assertRaisesRegex(RuntimeError,'registry alias'): require_independent(first,second)

    def test_peer_corruption_rejected_before_success_callback(self):
        step=core._step3c; seen=[]
        def corrupt(state,*a,**kw):
            result=step(state,*a,**kw)
            if state.sibling_backend not in seen: seen.append(state.sibling_backend)
            if len(seen)==2:
                next(iter(state.sibling_backend._lists.values())).root.span+=1
            return result
        prefixes=[]
        with patch.object(core,'_step3c',corrupt), self.assertRaises(RuntimeError):
            run_synchronous_qualification(list(range(1,9)),backend=backend_spec('heterogeneous_finger'),
                prefix_callback=lambda s,v:prefixes.append(s.processed_count))
        self.assertEqual(prefixes,[3])

    def test_pending_and_adopt_failure_cannot_reach_output(self):
        for broken in (lambda *a,**kw:None, lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('adopt failed'))):
            with patch.object(Tree,'adopt_split',broken), self.assertRaises(RuntimeError):
                run_synchronous_qualification(self.values,backend=backend_spec('heterogeneous_finger'))

    def test_final_fresh_replay_runs_and_is_checked(self):
        init=Tree.__init__; instances=[]
        def fail_third(b,*a,**kw):
            init(b,*a,**kw); instances.append(b)
            if len(instances)==3: raise RuntimeError('fresh replay construction failed')
        with patch.object(Tree,'__init__',fail_third), self.assertRaisesRegex(RuntimeError,'fresh replay'):
            run_synchronous_qualification(self.values,backend=backend_spec('heterogeneous_finger'))
        self.assertEqual(len(instances),3)

    def test_final_comparison_reaudits_callback_mutation(self):
        def corrupt_last(state,views):
            if state.processed_count==len(self.values):
                next(iter(state.sibling_backend._lists.values())).root.span+=1
        with self.assertRaises(RuntimeError):
            run_synchronous_qualification(self.values,backend=backend_spec('heterogeneous_finger'),prefix_callback=corrupt_last)

    def test_flat_audit_schedule_and_history_work_are_separately_counted(self):
        values=list(range(1,17)); t=len(values)-2; audit=Tree._audit; calls=[]; old_work={}
        def observed(b,*a,**kw): calls.append(1); return audit(b,*a,**kw)
        with patch.object(Tree,'_audit',observed):
            core._run_paper_jordan_state_values(values,backend=backend_spec('heterogeneous_finger'),
                invariant_callback=lambda s:core.validate_paper_jordan_state_reference(s,history_work=old_work))
            self.assertEqual(len(calls),t*(t+1)//2+4*t)
            calls.clear()
            state,report=run_synchronous_qualification(values,backend=backend_spec('heterogeneous_finger'))
        self.assertEqual(len(calls),5*t+2)
        self.assertEqual(report['history_work']['linked_points'],2*sum(range(3,len(values)+1))+2*len(values))
        self.assertNotIn('reference_filter_visits',report['history_work'])
        self.assertEqual(old_work['reference_filter_visits'],sum(3*k*(k-3) for k in range(3,len(values)+1)))


if __name__=='__main__': unittest.main()
