"""Check the eight-point walkthrough against the ordinary-list diagnostics and live groups."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from paper_jordan import (_run_paper_jordan_state_values, pair_encloses_point,
                          step1_select_predecessor_boundary, step2_select_successor_boundary,
                          step3a_increasing, step3b_increasing, step3c_increasing)
from paper_jordan_sort import paper_jordan_diagnostics_valid


def verify():
    values = [1, 2, 8, 7, 5, 4, 3, 6]
    report = paper_jordan_diagnostics_valid(values)
    events = [e for e in report["trace"] if e.get("iteration") == 8]
    assert [e["step"] for e in events] == [
        "step1_find_predecessor", "step1_select_boundary_pair",
        "step2_find_successor", "step2_select_boundary_pair",
        "step3a_insert_pair", "step3b_split_sibling_list", "step3c_insert_output_point",
    ]
    pred, a, succ, b, insert, split, output = events
    assert all(e["family"] == "upper" for e in events)
    assert all(e["orientation"] == "increasing" for e in (insert, split, output))
    assert all(e["adjusted_for_z1"] is False for e in (pred, a, succ, b, output))
    assert a["used_dummy_pair"] is False and b["used_dummy_pair"] is False
    assert pred["previous_point_id"] == succ["previous_point_id"] == 7
    assert pred["neighbor_point_id"] == a["neighbor_point_id"] == 2
    assert succ["neighbor_point_id"] == b["neighbor_point_id"] == 6
    assert a["selected_pair_id"] == insert["boundary_pair_id"] == 2
    assert b["selected_pair_id"] == split["boundary_pair_id"] == 6
    assert insert["pair_id"] == split["pair_id"] == output["pair_id"] == 8
    assert insert["insertion_mode"] == "boundary_insertion"
    assert split["performed"] is True and split["acquired_side"] == "left"
    assert (split["input_size"], split["left_size"], split["right_size"]) == (2, 1, 1)
    assert output["child_pair_id"] == 6 and output["insertion_side"] == "after"
    assert output["base_anchor_point_id"] == output["output_anchor_point_id"] == 5
    assert output["processed_count"] == 8 and report["invariants_valid"]

    # The trace records sizes and list IDs. Inspect actual ordered members and
    # parents between the same implementation steps to verify the panel labels.
    state = _run_paper_jordan_state_values(values, stop_after=7)
    root = state.upper_dummy_pair_id
    pairs = state.pairs
    get_list = state.sibling_backend.get_list

    def groups(owner):
        return {tuple(get_list(k).pair_ids) for k in pairs[owner].child_sibling_list_ids}

    def endpoints(pair):
        return (state.point_value(pairs[pair].first_point_id),
                state.point_value(pairs[pair].second_point_id))

    assert state.partial_order.to_list() == [1, 2, 3, 4, 5, 7, 8]
    assert (state.point_value(7), state.point_value(8)) == (3, 6)
    assert state.point_value(pred["neighbor_point_id"]) == 2
    assert state.point_value(succ["neighbor_point_id"]) == 4
    assert pairs[root].is_dummy and groups(root) == {(2,), (6, 4)}
    assert [endpoints(i) for i in (2, 4, 6)] == [(1, 2), (8, 7), (5, 4)]
    assert not pair_encloses_point(state, 2, 7) and not pair_encloses_point(state, 6, 7)
    left = step1_select_predecessor_boundary(state, 8)
    right = step2_select_successor_boundary(state, 8)
    step3a_increasing(state, 8, left)
    assert endpoints(8) == (3, 6) and pairs[8].parent_pair_id == insert["parent_pair_id"] == root
    assert tuple(get_list(insert["sibling_list_id"]).pair_ids) == (2, 8)
    assert tuple(get_list(split["input_list_id"]).pair_ids) == (6, 4)
    step3b_increasing(state, 8, 8, right)
    assert tuple(get_list(split["left_list_id"]).pair_ids) == (6,)
    assert tuple(get_list(split["right_list_id"]).pair_ids) == (4,)
    assert groups(8) == {(6,)} and groups(root) == {(2, 8), (4,)}
    assert pairs[6].parent_pair_id == 8 and pairs[4].parent_pair_id == root
    assert state.point_value(output["output_anchor_point_id"]) == max(endpoints(6)) == 5
    step3c_increasing(state, 8, 8)
    assert state.partial_order.to_list() == report["output"] == list(range(1, 9))


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without -O so the assertions execute.")
    verify()
    print("Verified all seven iteration-8 events, sibling groups, anchor and output.")
