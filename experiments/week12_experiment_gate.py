"""Frozen, unexecuted Week 12 valid-input sorting experiment gate."""

import hashlib
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


WEEK12_PROTOCOL_VERSION = "week12_formal_sorting_v1"
WEEK12_GATE_STATUS = "frozen_not_executed"
PAPER_ALGORITHM_NAME = "simplified_jordan_paper_ordinary_list"


@dataclass(frozen=True)
class Week12ExperimentGate:
    """Store the machine-independent Week 12 formal sorting choices."""

    protocol_version: str
    status: str
    source_pilot_execution_id: str
    source_pilot_commit: str
    source_pilot_manifest_path: str
    source_pilot_manifest_sha256: str
    scope: str
    recognition_separate: bool
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
            raise ValueError(f"family is not part of the gate: {family}")
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

    @property
    def case_audit_row_count(self):
        return self.case_count


WEEK12_EXPERIMENT_GATE = Week12ExperimentGate(
    protocol_version=WEEK12_PROTOCOL_VERSION,
    status=WEEK12_GATE_STATUS,
    source_pilot_execution_id="week11_pilot_v1__run003",
    source_pilot_commit="01f6480fe179dcbe0f99486be86384b61dd4121f",
    source_pilot_manifest_path=(
        "results/runs/week11_pilot_v1__run003/manifest.json"
    ),
    source_pilot_manifest_sha256=(
        "ef6a9d17df644eab8c3284d04dc356ce4b68b4efdfc0da7eecb5a9c7136c5141"
    ),
    scope="oracle_certified_valid_input_sorting",
    recognition_separate=True,
    sizes=(32, 64, 128, 256, 512),
    valid_families=(
        FLAT_VALID,
        NESTED_VALID,
        INCREMENTAL_VALID,
    ),
    randomized_cases=10,
    warmup_runs=5,
    measured_runs=20,
    algorithms=(
        "python_sort",
        "simplified_jordan_reference",
        PAPER_ALGORITHM_NAME,
    ),
    paper_execution_mode=MINIMAL_MODE,
    audit_execution_mode=CHECKED_MODE,
    seed=20261201,
    algorithm_order_seed=20261202,
    case_order_seed=20261203,
)


def validate_week12_experiment_gate(gate=WEEK12_EXPERIMENT_GATE):
    """Reject any drift from the frozen, unexecuted Week 12 gate."""
    if not isinstance(gate, Week12ExperimentGate):
        raise TypeError("gate must be a Week12ExperimentGate")
    if gate != WEEK12_EXPERIMENT_GATE:
        raise ValueError("Week 12 gate does not match the frozen contract")
    if gate.status != "frozen_not_executed":
        raise RuntimeError("Week 12 gate must remain unexecuted")
    if gate.scope != "oracle_certified_valid_input_sorting":
        raise RuntimeError("Week 12 sorting scope changed")
    if gate.recognition_separate is not True:
        raise RuntimeError("recognition must remain separate")
    manifest_path = PROJECT_ROOT / gate.source_pilot_manifest_path
    if not manifest_path.is_file():
        raise RuntimeError("Week 11 source-pilot manifest is missing")
    manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if manifest_sha256 != gate.source_pilot_manifest_sha256:
        raise RuntimeError("Week 11 source-pilot manifest hash changed")
    minimal_policy = PAPER_EXECUTION_POLICIES[gate.paper_execution_mode]
    if (
        minimal_policy.record_trace
        or minimal_policy.count_operations
        or minimal_policy.validate_backend_commits
    ):
        raise RuntimeError("Week 12 paper timing mode is not minimal")
    checked_policy = PAPER_EXECUTION_POLICIES[gate.audit_execution_mode]
    if not (
        checked_policy.record_trace
        and checked_policy.count_operations
        and checked_policy.validate_backend_commits
    ):
        raise RuntimeError("Week 12 audit mode is not checked")
    expected_counts = (60, 3600, 180, 45, 60)
    actual_counts = (
        gate.case_count,
        gate.raw_row_count,
        gate.case_summary_row_count,
        gate.group_summary_row_count,
        gate.case_audit_row_count,
    )
    if actual_counts != expected_counts:
        raise RuntimeError("Week 12 gate row counts changed")
    return gate


def gate_to_dict(gate=WEEK12_EXPERIMENT_GATE):
    validate_week12_experiment_gate(gate)
    result = asdict(gate)
    for field_name in ("sizes", "valid_families", "algorithms"):
        result[field_name] = list(result[field_name])
    result.update(
        {
            "case_count": gate.case_count,
            "raw_row_count": gate.raw_row_count,
            "case_summary_row_count": gate.case_summary_row_count,
            "group_summary_row_count": gate.group_summary_row_count,
            "case_audit_row_count": gate.case_audit_row_count,
        }
    )
    return result


def main():
    print(json.dumps(gate_to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
