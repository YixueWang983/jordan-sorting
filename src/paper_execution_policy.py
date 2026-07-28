"""Fixed execution-policy definitions for the paper Jordan algorithm."""

from dataclasses import dataclass
from types import MappingProxyType


CHECKED_MODE = "checked"
INSTRUMENTED_MODE = "instrumented"
TRACE_ONLY_MODE = "trace_only"
COUNTERS_ONLY_MODE = "counters_only"
MINIMAL_MODE = "minimal"


@dataclass(frozen=True)
class PaperExecutionPolicy:
    """Describe observation and global-validation behavior for one fixed mode."""

    name: str
    record_trace: bool
    count_operations: bool
    validate_backend_commits: bool

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("policy name must be a non-empty string")
        for field_name in (
            "record_trace",
            "count_operations",
            "validate_backend_commits",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a bool")


CHECKED_POLICY = PaperExecutionPolicy(
    name=CHECKED_MODE,
    record_trace=True,
    count_operations=True,
    validate_backend_commits=True,
)
INSTRUMENTED_POLICY = PaperExecutionPolicy(
    name=INSTRUMENTED_MODE,
    record_trace=True,
    count_operations=True,
    validate_backend_commits=False,
)
TRACE_ONLY_POLICY = PaperExecutionPolicy(
    name=TRACE_ONLY_MODE,
    record_trace=True,
    count_operations=False,
    validate_backend_commits=False,
)
COUNTERS_ONLY_POLICY = PaperExecutionPolicy(
    name=COUNTERS_ONLY_MODE,
    record_trace=False,
    count_operations=True,
    validate_backend_commits=False,
)
MINIMAL_POLICY = PaperExecutionPolicy(
    name=MINIMAL_MODE,
    record_trace=False,
    count_operations=False,
    validate_backend_commits=False,
)

PAPER_EXECUTION_POLICIES = MappingProxyType(
    {
        policy.name: policy
        for policy in (
            CHECKED_POLICY,
            INSTRUMENTED_POLICY,
            TRACE_ONLY_POLICY,
            COUNTERS_ONLY_POLICY,
            MINIMAL_POLICY,
        )
    }
)
PAPER_EXECUTION_MODE_NAMES = tuple(PAPER_EXECUTION_POLICIES)


def resolve_paper_execution_policy(execution_mode=CHECKED_MODE):
    """Return one fixed policy selected by its public mode name."""
    if not isinstance(execution_mode, str):
        raise TypeError("execution_mode must be a string")
    try:
        return PAPER_EXECUTION_POLICIES[execution_mode]
    except KeyError as exc:
        raise ValueError(f"unknown paper execution mode: {execution_mode}") from exc


def require_fixed_paper_execution_policy(policy):
    """Reject mutable, copied, or caller-defined policy objects."""
    if not isinstance(policy, PaperExecutionPolicy):
        raise TypeError("execution_policy must be a PaperExecutionPolicy")
    if PAPER_EXECUTION_POLICIES.get(policy.name) is not policy:
        raise ValueError("execution_policy must come from the fixed policy registry")
    return policy
