"""Machine-independent protocol for the Week 11 sorting pilot."""

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


WEEK11_PROTOCOL_VERSION = "week11_pilot_v1"
PAPER_ALGORITHM_NAME = "simplified_jordan_paper_ordinary_list"


@dataclass(frozen=True)
class Week11ExperimentProtocol:
    """Store experiment choices that remain fixed across machines and runs."""

    protocol_version: str
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

    def repetitions_for_family(self, family):
        if family not in self.valid_families:
            raise ValueError(f"family is not part of the protocol: {family}")
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
        return len(self.valid_families) * len(self.sizes) * len(self.algorithms)


WEEK11_EXPERIMENT_PROTOCOL = Week11ExperimentProtocol(
    protocol_version=WEEK11_PROTOCOL_VERSION,
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
)


def validate_week11_experiment_protocol(
    protocol=WEEK11_EXPERIMENT_PROTOCOL,
):
    """Reject any change to the machine-independent Week 11 protocol."""
    if not isinstance(protocol, Week11ExperimentProtocol):
        raise TypeError("protocol must be a Week11ExperimentProtocol")
    if protocol != WEEK11_EXPERIMENT_PROTOCOL:
        raise ValueError("Week 11 protocol does not match the frozen contract")

    minimal_policy = PAPER_EXECUTION_POLICIES[protocol.paper_execution_mode]
    if (
        minimal_policy.record_trace
        or minimal_policy.count_operations
        or minimal_policy.validate_backend_commits
    ):
        raise RuntimeError("minimal mode no longer satisfies the timing protocol")

    checked_policy = PAPER_EXECUTION_POLICIES[protocol.audit_execution_mode]
    if not (
        checked_policy.record_trace
        and checked_policy.count_operations
        and checked_policy.validate_backend_commits
    ):
        raise RuntimeError("checked mode no longer satisfies the audit protocol")

    expected_counts = (35, 1050, 105, 45)
    actual_counts = (
        protocol.case_count,
        protocol.raw_row_count,
        protocol.case_summary_row_count,
        protocol.group_summary_row_count,
    )
    if actual_counts != expected_counts:
        raise RuntimeError("Week 11 protocol row counts changed")
    return protocol


def protocol_to_dict(protocol=WEEK11_EXPERIMENT_PROTOCOL):
    """Return the JSON-ready protocol without execution or machine fields."""
    validate_week11_experiment_protocol(protocol)
    result = asdict(protocol)
    for field_name in ("sizes", "valid_families", "algorithms"):
        result[field_name] = list(result[field_name])
    result.update(
        {
            "case_count": protocol.case_count,
            "raw_row_count": protocol.raw_row_count,
            "case_summary_row_count": protocol.case_summary_row_count,
            "group_summary_row_count": protocol.group_summary_row_count,
            "status": "frozen",
        }
    )
    return result


def main():
    print(json.dumps(protocol_to_dict(), indent=2))


if __name__ == "__main__":
    main()
