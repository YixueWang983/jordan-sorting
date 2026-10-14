import unittest

from probe_finger_cost_lemmas import (Fixture, forms, build_down, audit_down, exhaustive_splits,
                                    mixed_updates, observe_lemmas, TreeOperations, InternalNode, INTERIOR)


class FingerCostLemmaTests(unittest.TestCase):
    def test_red_roots_require_two_units_relative_to_raw_input_rank(self):
        f=Fixture(); red=(True,0,forms(1)[0],forms(1)[0])
        left,right=build_down(red,f),build_down(red,f,2)
        connector=InternalNode(f.backend.work,f.backend._node_id(),INTERIOR,True,0,0,10)
        rows=[]
        with observe_lemmas(rows),f.backend.work.observe('operations','two_red_roots'):
            result=TreeOperations(f.backend).join_down(left,right,connector)
        self.assertEqual(audit_down(result),[0,10,20,30])
        self.assertEqual(rows[0]['raw_ranks'],[0,0])
        self.assertEqual(rows[0]['normalized_ranks'],[1,1])
        self.assertEqual(rows[0]['result_rank'],2)

    def test_all_colored_shapes_up_to_ten_leaves_and_every_cut(self):
        count,rows=exhaustive_splits()
        self.assertEqual(count,2634)
        self.assertTrue(any(r['kind']=='split_down' and r['source_red'] for r in rows))
        self.assertTrue(any(r['kind']=='join' and r['accumulator']>r['sibling'] for r in rows if 'accumulator' in r))

    def test_mixed_histories_pay_insertion_potential_and_limit_root_rib_walks(self):
        histories,inserts,rows=mixed_updates()
        self.assertEqual(len(histories),12)
        self.assertTrue(all(h['model_and_structure_passed'] for h in histories))
        self.assertTrue(any(x['cascades']>=2 for x in inserts))
        self.assertTrue(any(x['kind']=='repair_short' and x['rib_calls'] for x in rows))
        self.assertTrue(any(x['kind']=='join' and abs(x['normalized_ranks'][0]-x['normalized_ranks'][1])>=3 for x in rows))


if __name__=='__main__': unittest.main()
