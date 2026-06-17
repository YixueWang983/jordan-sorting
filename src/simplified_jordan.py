"""Reference skeleton for simplified Jordan sorting."""

from family_tree import (
    LOWER,
    UPPER,
    build_family_trees,
    family_tree_to_dict,
)
from oracle import oracle
from stats import structure_profile


IMPLEMENTATION = "reference_skeleton"
IMPLEMENTATION_STAGE = "week2_interface_skeleton"
BACKEND_REFERENCE = {
    "name": "ordinary_list",
    "uses_oracle_sorted_output": True,
    "linear_time_claim": False,
}


def _build_result(valid, sorted_result, reason, oracle_result, families, stats, trace):
    """Build a standardized reference skeleton result dict."""

    return {
        "valid": valid,
        "sorted": sorted_result,
        "reason": reason,
        "oracle": oracle_result,
        "families": families,
        "stats": stats,
        "trace": trace,
        "implementation": IMPLEMENTATION,
        "implementation_stage": IMPLEMENTATION_STAGE,
        "backend": BACKEND_REFERENCE,
    }


def simplified_jordan_sort(seq):
    """Return a reference-skeleton result for a candidate sequence.

    Return value (stable contract):
    {
        "valid": bool,
        "sorted": list,
        "reason": str | None,
        "oracle": dict,
        "families": dict | None,
        "stats": dict,
        "trace": list,
        "implementation": "reference_skeleton",
        "implementation_stage": "week2_interface_skeleton",
        "backend": {
            "name": "ordinary_list",
            "uses_oracle_sorted_output": True,
            "linear_time_claim": False,
        },
    }

    This is *not* the full simplified Jordan-sorting algorithm.
    It relies on ``oracle_result["sorted"]`` as the output list and
    focuses on a testable interface + structural outputs.
    """
    values = list(seq)
    oracle_result = oracle(values)

    trace = [
        {"step": "copy_input", "n": len(values)},
        {
            "step": "oracle",
            "valid": oracle_result["valid"],
            "reason": oracle_result["reason"],
        },
    ]

    if not oracle_result["valid"]:
        stats = structure_profile(values, oracle_result=oracle_result)
        trace.append(
            {
                "step": "structure_profile",
                "category": stats["category"],
            }
        )
        trace.append(
            {
                "step": "reject_invalid_input",
                "reason": oracle_result["reason"],
            }
        )
        return _build_result(
            False,
            oracle_result["sorted"],
            oracle_result["reason"],
            oracle_result,
            None,
            stats,
            trace,
        )

    families = build_family_trees(values, oracle_result=oracle_result)
    trace.append(
        {
            "step": "build_family_trees",
            "upper_nodes": len(families[UPPER].nodes),
            "lower_nodes": len(families[LOWER].nodes),
        }
    )

    stats = structure_profile(
        values,
        oracle_result=oracle_result,
        family_trees=families,
    )
    trace.append(
        {
            "step": "structure_profile",
            "category": stats["category"],
        }
    )
    trace.append({"step": "prepare_reference_backend", "backend": "ordinary_list"})
    trace.append({"step": "extract_rank_order", "backend": "oracle_sorted"})
    trace.append({"step": "return_reference_sorted_output"})

    return _build_result(
        True,
        oracle_result["sorted"],
        None,
        oracle_result,
        {
            UPPER: family_tree_to_dict(families[UPPER]),
            LOWER: family_tree_to_dict(families[LOWER]),
        },
        stats,
        trace,
    )
