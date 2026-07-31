"""Run-level identity and environment binding for Week 11 evidence."""

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


DEFAULT_EXECUTION_ID = "week11_pilot_v1__mac16_13__run1"
EXECUTION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True)
class Week11ExecutionContext:
    """Describe one execution of a protocol on one source and machine."""

    execution_id: str
    output_dir: str
    machine_identity: Mapping[str, str]
    source_commit: str

    def __post_init__(self):
        object.__setattr__(
            self,
            "machine_identity",
            MappingProxyType(dict(self.machine_identity)),
        )


def output_dir_for_execution(execution_id):
    """Return the isolated repository-relative directory for one execution."""
    validate_execution_id(execution_id)
    return f"results/runs/{execution_id}"


def validate_execution_id(execution_id):
    if not isinstance(execution_id, str):
        raise TypeError("execution_id must be a string")
    if not EXECUTION_ID_PATTERN.fullmatch(execution_id):
        raise ValueError("execution_id contains unsupported characters")
    return execution_id


def validate_execution_context(context):
    """Validate run identity without imposing a particular machine model."""
    if not isinstance(context, Week11ExecutionContext):
        raise TypeError("context must be a Week11ExecutionContext")
    validate_execution_id(context.execution_id)
    if context.output_dir != output_dir_for_execution(context.execution_id):
        raise ValueError("execution output_dir does not match execution_id")
    if not context.machine_identity:
        raise ValueError("execution machine_identity must not be empty")
    if any(
        not isinstance(key, str)
        or not key
        or not isinstance(value, str)
        or not value
        for key, value in context.machine_identity.items()
    ):
        raise ValueError("execution machine_identity must contain strings")
    if len(context.source_commit) not in {40, 64}:
        raise ValueError("source_commit must be a Git commit SHA")
    try:
        int(context.source_commit, 16)
    except ValueError as exc:
        raise ValueError("source_commit must be hexadecimal") from exc
    return context


def execution_context_to_dict(context):
    """Return a JSON-ready execution record."""
    validate_execution_context(context)
    return {
        "execution_id": context.execution_id,
        "output_dir": context.output_dir,
        "machine_identity": dict(context.machine_identity),
        "source_commit": context.source_commit,
    }
