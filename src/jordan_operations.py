"""Algorithm-facing operation helpers for the week 4 reference pipeline."""

from oracle import (
    lower_pairs,
    pair_to_interval,
    rank_map,
    upper_pairs,
)


def extract_pair_families(seq):
    """Return upper/lower pair families from a candidate sequence."""
    values = list(seq)

    return {
        "upper": upper_pairs(values),
        "lower": lower_pairs(values),
    }


def build_rank_intervals(seq, rank=None):
    """Build rank intervals for upper and lower pair families.

    If `rank` is not supplied, it is computed from the sequence.
    """
    values = list(seq)

    if rank is None:
        if len(values) != len(set(values)):
            raise ValueError(
                "rank cannot be inferred from a sequence with duplicate values"
            )
        rank = rank_map(values)

    pair_families = extract_pair_families(values)
    return {
        "upper": [pair_to_interval(pair, rank) for pair in pair_families["upper"]],
        "lower": [pair_to_interval(pair, rank) for pair in pair_families["lower"]],
    }


def build_operation_state(seq, oracle_result=None):
    """Build a compact operation-state snapshot for a candidate sequence."""
    values = list(seq)
    if oracle_result is None:
        from oracle import oracle

        oracle_result = oracle(values)

    state = {
        "n": len(values),
        "values": values,
        "oracle": oracle_result,
    }

    pair_families = extract_pair_families(values)
    state["upper_pairs"] = pair_families["upper"]
    state["lower_pairs"] = pair_families["lower"]

    if oracle_result["distinct_values"]:
        rank = rank_map(values)
        state["rank_map"] = rank
        state["upper_intervals"] = [
            pair_to_interval(pair, rank) for pair in state["upper_pairs"]
        ]
        state["lower_intervals"] = [
            pair_to_interval(pair, rank) for pair in state["lower_pairs"]
        ]
    else:
        state["rank_map"] = None
        state["upper_intervals"] = None
        state["lower_intervals"] = None

    return state


def operation_state_to_trace_fields(state):
    """Convert an operation state into compact trace entries."""
    fields = [
        {"step": "build_rank_map", "n": state["n"]},
        {
            "step": "extract_pair_families",
            "upper_pair_count": len(state["upper_pairs"]),
            "lower_pair_count": len(state["lower_pairs"]),
        },
    ]

    fields[0]["distinct_values"] = state["oracle"]["distinct_values"]

    if state["rank_map"] is not None:
        fields.append(
            {
                "step": "convert_pairs_to_rank_intervals",
                "upper_interval_count": len(state["upper_intervals"]),
                "lower_interval_count": len(state["lower_intervals"]),
            },
        )
    else:
        fields.append(
            {
                "step": "convert_pairs_to_rank_intervals",
                "upper_interval_count": None,
                "lower_interval_count": None,
                "skipped": True,
            },
        )

    return fields
