"""Frozen Week 11 v2 paper-sorting pilot gate for the M4 machine."""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from generators import FLAT_VALID, INCREMENTAL_VALID, NESTED_VALID
from paper_execution_policy import (
    CHECKED_MODE,
    MINIMAL_MODE,
    PAPER_EXECUTION_POLICIES,
)
from week11_experiment_gate import (
    PAPER_ALGORITHM_NAME,
    Week11ExperimentGate,
)


WEEK11_GATE_VERSION_V2 = "v2"
WEEK11_RUN_ID_V2 = "week11_paper_sorting_pilot_v2_m4"
WEEK11_OUTPUT_DIR_V2 = f"results/runs/{WEEK11_RUN_ID_V2}"
WEEK11_MACHINE_IDENTITY_ID_V2 = "week11_v2_m4_mac16_13"
WEEK11_MACHINE_BASELINE_PATH_V2 = (
    "docs/analysis/week11_machine_baseline_v2_m4.json"
)
WEEK11_MACHINE_BASELINE_SHA256_V2 = (
    "d59a3d265985d781d3368366ac1553635b5fbfca20f6a03e6df4efef43fe7f69"
)
WEEK11_MACHINE_PREFLIGHT_PATH_V2 = (
    "docs/analysis/week11_machine_preflight_v2_m4.md"
)


@dataclass(frozen=True)
class Week11ExperimentGateV2(Week11ExperimentGate):
    """Bind the unchanged pilot design to one versioned machine baseline."""

    gate_version: str
    machine_baseline_path: str
    machine_baseline_sha256: str
    machine_identity_id: str
    machine_preflight_path: str


WEEK11_EXPERIMENT_GATE_V2 = Week11ExperimentGateV2(
    run_id=WEEK11_RUN_ID_V2,
    output_dir=WEEK11_OUTPUT_DIR_V2,
    sizes=(32, 64, 128, 256, 512),
    valid_families=(
        FLAT_VALID,
        NESTED_VALID,
        INCREMENTAL_VALID,
    ),
    randomized_cases=5,
    warmup_runs=3,
    measured_runs=10,
    algorithms=(
        "python_sort",
        "simplified_jordan_reference",
        PAPER_ALGORITHM_NAME,
    ),
    paper_execution_mode=MINIMAL_MODE,
    audit_execution_mode=CHECKED_MODE,
    seed=20260723,
    algorithm_order_seed=20268642,
    case_order_seed=20262266,
    estimated_runtime_upper_minutes=15,
    gate_version=WEEK11_GATE_VERSION_V2,
    machine_baseline_path=WEEK11_MACHINE_BASELINE_PATH_V2,
    machine_baseline_sha256=WEEK11_MACHINE_BASELINE_SHA256_V2,
    machine_identity_id=WEEK11_MACHINE_IDENTITY_ID_V2,
    machine_preflight_path=WEEK11_MACHINE_PREFLIGHT_PATH_V2,
)


def validate_week11_experiment_gate_v2(gate=WEEK11_EXPERIMENT_GATE_V2):
    """Reject any drift from the frozen Week 11 v2 M4 contract."""
    if not isinstance(gate, Week11ExperimentGateV2):
        raise TypeError("gate must be a Week11ExperimentGateV2")
    if gate != WEEK11_EXPERIMENT_GATE_V2:
        raise ValueError("Week 11 v2 gate does not match the frozen contract")

    minimal_policy = PAPER_EXECUTION_POLICIES[gate.paper_execution_mode]
    if (
        minimal_policy.record_trace
        or minimal_policy.count_operations
        or minimal_policy.validate_backend_commits
    ):
        raise RuntimeError("minimal mode no longer satisfies the timing gate")

    checked_policy = PAPER_EXECUTION_POLICIES[gate.audit_execution_mode]
    if not (
        checked_policy.record_trace
        and checked_policy.count_operations
        and checked_policy.validate_backend_commits
    ):
        raise RuntimeError("checked mode no longer satisfies the audit gate")

    expected_counts = (35, 1050, 105, 45)
    actual_counts = (
        gate.case_count,
        gate.raw_row_count,
        gate.case_summary_row_count,
        gate.group_summary_row_count,
    )
    if actual_counts != expected_counts:
        raise RuntimeError("Week 11 v2 derived row counts changed")
    return gate


def gate_to_dict_v2(gate=WEEK11_EXPERIMENT_GATE_V2):
    """Return the JSON-ready v2 gate and its derived row counts."""
    validate_week11_experiment_gate_v2(gate)
    result = asdict(gate)
    for field_name in ("sizes", "valid_families", "algorithms"):
        result[field_name] = list(result[field_name])
    result.update(
        {
            "case_count": gate.case_count,
            "raw_row_count": gate.raw_row_count,
            "case_summary_row_count": gate.case_summary_row_count,
            "group_summary_row_count": gate.group_summary_row_count,
            "status": "frozen_not_executed",
        }
    )
    return result


# The dedicated runner imports these active-gate aliases from the v2 module.
WEEK11_EXPERIMENT_GATE = WEEK11_EXPERIMENT_GATE_V2
gate_to_dict = gate_to_dict_v2
validate_week11_experiment_gate = validate_week11_experiment_gate_v2


def main():
    print(json.dumps(gate_to_dict_v2(), indent=2))


if __name__ == "__main__":
    main()
