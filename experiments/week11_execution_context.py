"""Run-level identity and environment binding for Week 11 evidence."""

import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


EXECUTION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BENCHMARK_ENVIRONMENT_FIELDS = (
    "processor_class",
    "architecture",
    "memory_gb",
    "logical_cpu_count",
    "os_name",
    "os_version",
    "os_build",
    "python_implementation",
    "python_version",
)


@dataclass(frozen=True)
class Week11ExecutionContext:
    """Describe one execution of a protocol and its benchmark environment."""

    execution_id: str
    output_dir: str
    benchmark_environment: Mapping[str, object]
    source_commit: str

    def __post_init__(self):
        object.__setattr__(
            self,
            "benchmark_environment",
            MappingProxyType(dict(self.benchmark_environment)),
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
    environment = context.benchmark_environment
    if set(environment) != set(BENCHMARK_ENVIRONMENT_FIELDS):
        raise ValueError("execution benchmark_environment fields changed")
    for field in BENCHMARK_ENVIRONMENT_FIELDS:
        value = environment[field]
        if field in {"memory_gb", "logical_cpu_count"}:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError(f"benchmark environment {field} is invalid")
        elif not isinstance(value, str) or not value:
            raise ValueError(f"benchmark environment {field} is invalid")
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
        "benchmark_environment": dict(context.benchmark_environment),
        "source_commit": context.source_commit,
    }
