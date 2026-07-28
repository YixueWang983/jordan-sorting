"""Frozen Week 11 paper-sorting integration-pilot gate."""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    NESTED_VALID,
)
from paper_execution_policy import (  # noqa: E402
    CHECKED_MODE,
    MINIMAL_MODE,
    PAPER_EXECUTION_POLICIES,
)


PAPER_ALGORITHM_NAME = "simplified_jordan_paper_ordinary_list"
WEEK11_RUN_ID = "week11_paper_sorting_pilot_v1"
WEEK11_OUTPUT_DIR = f"results/runs/{WEEK11_RUN_ID}"


@dataclass(frozen=True)
class Week11ExperimentGate:
    """Store the frozen, not-yet-executed Week 11 pilot configuration."""

    run_id: str
    output_dir: str
    sizes: tuple[int, ...]
    valid_families: tuple[str, ...]
    randomized_cases: int
    warmup_runs: int
    measured_runs: int
    algorithms: tuple[str, ...]
    paper_execution_mode: str
    audit_execution_mode: str
    seed: int
    algorithm_order_seed: int
    case_order_seed: int
    estimated_runtime_upper_minutes: int

    def repetitions_for_family(self, family):
        if family not in self.valid_families:
            raise ValueError(f"family is not part of the Week 11 gate: {family}")
        return self.randomized_cases if family == INCREMENTAL_VALID else 1

    @property
    def case_count(self):
        return len(self.sizes) * sum(
            self.repetitions_for_family(family)
            for family in self.valid_families
        )

    @property
    def raw_row_count(self):
        return self.case_count * len(self.algorithms) * self.measured_runs

    @property
    def case_summary_row_count(self):
        return self.case_count * len(self.algorithms)

    @property
    def group_summary_row_count(self):
        return (
            len(self.valid_families)
            * len(self.sizes)
            * len(self.algorithms)
        )


WEEK11_EXPERIMENT_GATE = Week11ExperimentGate(
    run_id=WEEK11_RUN_ID,
    output_dir=WEEK11_OUTPUT_DIR,
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
)


def validate_week11_experiment_gate(gate=WEEK11_EXPERIMENT_GATE):
    """Reject drift from the frozen Week 11 integration-pilot contract."""
    if not isinstance(gate, Week11ExperimentGate):
        raise TypeError("gate must be a Week11ExperimentGate")
    if gate.run_id != WEEK11_RUN_ID:
        raise ValueError("Week 11 run_id does not match the frozen value")
    if gate.output_dir != WEEK11_OUTPUT_DIR:
        raise ValueError("Week 11 output_dir does not match the frozen value")
    if gate.sizes != (32, 64, 128, 256, 512):
        raise ValueError("Week 11 sizes do not match the frozen values")
    if gate.valid_families != (
        FLAT_VALID,
        NESTED_VALID,
        INCREMENTAL_VALID,
    ):
        raise ValueError("Week 11 valid families do not match the frozen values")
    if gate.randomized_cases != 5:
        raise ValueError("Week 11 randomized case count must be 5")
    if gate.warmup_runs != 3 or gate.measured_runs != 10:
        raise ValueError("Week 11 timing repetition counts do not match")
    if gate.algorithms != (
        "python_sort",
        "simplified_jordan_reference",
        PAPER_ALGORITHM_NAME,
    ):
        raise ValueError("Week 11 algorithms do not match the frozen values")
    if gate.paper_execution_mode != MINIMAL_MODE:
        raise ValueError("Week 11 paper timing mode must be minimal")
    if gate.audit_execution_mode != CHECKED_MODE:
        raise ValueError("Week 11 untimed audit mode must be checked")
    if (
        gate.seed,
        gate.algorithm_order_seed,
        gate.case_order_seed,
    ) != (20260723, 20268642, 20262266):
        raise ValueError("Week 11 seeds do not match the frozen values")
    if gate.estimated_runtime_upper_minutes != 15:
        raise ValueError("Week 11 runtime budget does not match the frozen value")

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

    if gate.case_count != 35:
        raise RuntimeError("Week 11 expected case count changed")
    if gate.raw_row_count != 1050:
        raise RuntimeError("Week 11 expected raw row count changed")
    if gate.case_summary_row_count != 105:
        raise RuntimeError("Week 11 expected case-summary row count changed")
    if gate.group_summary_row_count != 45:
        raise RuntimeError("Week 11 expected group-summary row count changed")
    return gate


def gate_to_dict(gate=WEEK11_EXPERIMENT_GATE):
    """Return a JSON-ready gate record with derived row counts."""
    validate_week11_experiment_gate(gate)
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


def main():
    print(json.dumps(gate_to_dict(), indent=2))


if __name__ == "__main__":
    main()
