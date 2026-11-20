"""Check the lower-family walkthrough against iteration five of the sorting core."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from paper_jordan import _run_paper_jordan_state_values, pair_encloses_point
from paper_jordan_sort import paper_jordan_diagnostics_valid


def verify():
    values = [3, 5, 1, 2, 4]
    report = paper_jordan_diagnostics_valid(values)
    events = [event for event in report["trace"] if event.get("iteration") == 5]
    assert [e["step"] for e in events] == [
        "step1_find_predecessor", "step1_select_boundary_pair",
        "step2_find_successor", "step2_select_boundary_pair",
        "step3a_insert_pair", "step3b_split_sibling_list", "step3c_insert_output_point",
    ]
    pred, a, succ, b, insert, split, out = events
    assert all(e["family"] == "lower" for e in events)
    assert all(e["orientation"] == "increasing" for e in (insert, split, out))
    assert pred["previous_point_id"] == succ["previous_point_id"] == 4
    assert pred["neighbor_point_id"] == a["neighbor_point_id"] == 3
    assert pred["adjusted_for_z1"] is False and a["adjusted_for_z1"] is False
    assert succ["neighbor_point_id"] == b["neighbor_point_id"] == 2
    assert succ["adjusted_for_z1"] is True and b["adjusted_for_z1"] is True
    assert a["selected_pair_id"] == b["selected_pair_id"] == 3
    assert a["used_dummy_pair"] is False and b["used_dummy_pair"] is False
    assert insert["pair_id"] == split["pair_id"] == out["pair_id"] == 5
    assert insert["insertion_mode"] == "singleton_list"
    assert insert["parent_pair_id"] == insert["boundary_pair_id"] == split["boundary_pair_id"] == 3
    assert split["performed"] is False and split["reason"] == "boundary pair encloses previous point"
    assert out["child_pair_id"] is None and out["base_anchor_point_id"] == 4
    assert out["adjusted_for_z1"] is True and out["output_anchor_point_id"] == 1
    assert out["insertion_side"] == "after" and out["processed_count"] == 5

    # The trace gives the adjusted neighbor. Recover the skipped neighbor and
    # the incident pairs from the state immediately before the iteration.
    state = _run_paper_jordan_state_values(values, stop_after=4)
    prefix = state.partial_order.to_list()
    assert prefix == [1, 2, 3, 5]
    previous = state.point_value(4)
    z1 = state.point_value(1)
    new = state.point_value(5)
    assert (previous, z1, new) == (2, 3, 4)
    assert prefix[prefix.index(previous) - 1] == state.point_value(pred["neighbor_point_id"]) == 1
    assert prefix[prefix.index(previous) + 1] == z1
    assert prefix[prefix.index(z1) + 1] == state.point_value(succ["neighbor_point_id"]) == 5
    arcs = {p.pair_id: (p.family, state.point_value(p.first_point_id),
                        state.point_value(p.second_point_id))
            for p in state.pairs.values() if not p.is_dummy}
    assert arcs == {2: ("upper", 3, 5), 3: ("lower", 5, 1), 4: ("upper", 1, 2)}
    assert pair_encloses_point(state, 3, 4)
    assert previous < z1 < new
    wrong = prefix.copy()
    wrong.insert(wrong.index(previous) + 1, new)
    correct = prefix.copy()
    correct.insert(correct.index(z1) + 1, new)
    assert wrong == [1, 2, 4, 3, 5]
    assert correct == report["output"] == [1, 2, 3, 4, 5] and report["invariants_valid"]


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without -O to enable the trace assertions.")
    verify()
    print("Verified the skipped successor, singleton insertion, skipped split and corrected anchor.")
