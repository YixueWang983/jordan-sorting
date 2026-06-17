"""Reference skeleton for simplified Jordan sorting."""

from family_tree import (
    LOWER,
    UPPER,
    build_family_trees,
    family_tree_to_dict,
)
from oracle import oracle
from stats import structure_profile


def simplified_jordan_sort(seq):
    """Return a stable, testable reference skeleton result for a candidate sequence."""
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
        return {
            "valid": False,
            "sorted": oracle_result["sorted"],
            "reason": oracle_result["reason"],
            "oracle": oracle_result,
            "families": None,
            "stats": stats,
            "trace": trace,
            "implementation": "reference_skeleton",
        }

    families = build_family_trees(values, oracle_result=oracle_result)
    trace.append(
        {
            "step": "build_family_trees",
            "upper_nodes": len(families[UPPER].nodes),
            "lower_nodes": len(families[LOWER].nodes),
        }
    )

    stats = structure_profile(values, oracle_result=oracle_result)
    trace.append(
        {
            "step": "structure_profile",
            "category": stats["category"],
        }
    )
    trace.append({"step": "return_oracle_sorted_output"})

    return {
        "valid": True,
        "sorted": oracle_result["sorted"],
        "reason": None,
        "oracle": oracle_result,
        "families": {
            UPPER: family_tree_to_dict(families[UPPER]),
            LOWER: family_tree_to_dict(families[LOWER]),
        },
        "stats": stats,
        "trace": trace,
        "implementation": "reference_skeleton",
    }
