"""Experiment-only operation counters for the reference pipeline."""

from dataclasses import asdict, dataclass

from family_tree import LOWER, UPPER, build_family_trees, family_tree_to_dict
from jordan_operations import build_operation_state, operation_state_to_trace_fields
from oracle import oracle
from simplified_jordan import BACKEND_REFERENCE, IMPLEMENTATION, IMPLEMENTATION_STAGE
from stats import structure_profile


@dataclass
class OperationMetrics:
    """Deterministic counters for diagnostic cost analysis."""

    laminar_pair_checks: int = 0
    upper_pair_checks: int = 0
    lower_pair_checks: int = 0
    crossings_found: int = 0
    interval_validation_checks: int = 0
    containment_checks: int = 0
    parent_candidate_checks: int = 0
    nodes_created: int = 0
    nodes_visited: int = 0
    trace_event_count: int = 0

    def to_dict(self):
        """Return a serializable copy of the counters."""
        return asdict(self)


def _build_result(valid, sorted_result, reason, oracle_result, families, stats, trace):
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
        "backend": dict(BACKEND_REFERENCE),
    }


def instrumented_reference_run(seq):
    """Run the reference pipeline with operation counters.

    This is an experiment-only wrapper. It intentionally does not change the
    public return contract of ``simplified_jordan_sort``.
    """
    values = list(seq)
    metrics = OperationMetrics()
    oracle_result = oracle(values, metrics=metrics)

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
        metrics.trace_event_count = len(trace)
        return {
            "result": _build_result(
                False,
                oracle_result["sorted"],
                oracle_result["reason"],
                oracle_result,
                None,
                stats,
                trace,
            ),
            "metrics": metrics.to_dict(),
        }

    operation_state = build_operation_state(values, oracle_result=oracle_result)
    trace.extend(operation_state_to_trace_fields(operation_state))

    families = build_family_trees(values, oracle_result=oracle_result, metrics=metrics)
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

    metrics.trace_event_count = len(trace)
    return {
        "result": _build_result(
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
        ),
        "metrics": metrics.to_dict(),
    }

