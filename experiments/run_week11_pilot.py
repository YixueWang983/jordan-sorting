"""Build and preflight executions of the frozen Week 11 protocol."""

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import random
import re
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from baselines import python_sort  # noqa: E402
from generators import (  # noqa: E402
    INCREMENTAL_VALID,
    generate_sequence,
    make_case_id,
)
from oracle import oracle  # noqa: E402
from paper_execution_policy import CHECKED_MODE, MINIMAL_MODE  # noqa: E402
from paper_jordan import METRIC_NAMES as PAPER_METRIC_NAMES  # noqa: E402
from paper_jordan_sort import (  # noqa: E402
    paper_jordan_diagnostics_valid,
    paper_jordan_sort_valid,
)
from simplified_jordan import simplified_jordan_sort  # noqa: E402
from stats import structure_profile  # noqa: E402
from week11_execution_context import (  # noqa: E402
    BENCHMARK_ENVIRONMENT_FIELDS,
    Week11ExecutionContext,
    execution_context_to_dict,
    output_dir_for_execution,
    validate_execution_context,
    validate_execution_id,
)
from week11_experiment_protocol import (  # noqa: E402
    PAPER_ALGORITHM_NAME,
    WEEK11_EXPERIMENT_PROTOCOL,
    protocol_to_dict,
    validate_week11_experiment_protocol,
)


EVIDENCE_FILENAMES = (
    "raw.csv",
    "case_summary.csv",
    "group_summary.csv",
    "case_audit.csv",
    "config.json",
    "environment.json",
    "manifest.json",
    "validation_report.json",
)
POWER_STATUS_FIELDS = (
    "source",
    "status",
    "on_ac_power",
    "battery_state",
    "battery_percent",
    "low_power_mode",
)
LOAD_STATUS_FIELDS = (
    "logical_cpu_count",
    "one_minute_load",
    "five_minute_load",
    "fifteen_minute_load",
    "one_minute_load_per_cpu",
    "five_minute_load_per_cpu",
    "one_five_delta_per_cpu",
    "max_allowed_load_per_cpu",
    "max_allowed_delta_per_cpu",
    "low",
    "stable",
)
MIN_TIMING_DISK_BYTES = 1 << 30
MAX_TIMING_LOAD_PER_CPU = 0.25
MAX_TIMING_LOAD_DELTA_PER_CPU = 0.10

STRUCTURAL_FIELDS = (
    "category",
    "upper_interval_count",
    "lower_interval_count",
    "total_interval_count",
    "upper_root_count",
    "lower_root_count",
    "upper_nesting_count",
    "lower_nesting_count",
    "nesting_count",
    "nesting_density",
    "parented_interval_ratio",
    "upper_max_depth",
    "lower_max_depth",
    "max_depth",
    "upper_containment_pair_count",
    "lower_containment_pair_count",
    "containment_pair_count",
    "containment_pair_density",
    "upper_crossing_pair_count",
    "lower_crossing_pair_count",
    "total_crossing_pair_count",
)
PAPER_AUDIT_FIELDS = tuple(
    f"paper_{metric_name}" for metric_name in PAPER_METRIC_NAMES
)
RAW_FIELDS = (
    "protocol_version",
    "execution_id",
    "case_id",
    "case_index",
    "family",
    "n",
    "seed",
    "sequence_sha256",
    "case_execution_position",
    *STRUCTURAL_FIELDS,
    "algorithm",
    "paper_execution_mode",
    "audit_execution_mode",
    "run_index",
    "measured_round",
    "algorithm_position",
    "time_ns",
    "oracle_valid",
    "oracle_reason",
    "output_correct",
    "audit_passed",
    "error",
)
CASE_SUMMARY_FIELDS = (
    "case_id",
    "family",
    "n",
    "algorithm",
    "measured_run_count",
    "median_time_ns",
    "q1_time_ns",
    "q3_time_ns",
    "iqr_time_ns",
    "mean_time_ns",
    "stdev_time_ns",
    "all_correct",
    "error_count",
)
GROUP_SUMMARY_FIELDS = (
    "family",
    "n",
    "algorithm",
    "case_count",
    "median_case_time_ns",
    "q1_case_time_ns",
    "q3_case_time_ns",
    "iqr_case_time_ns",
    "mean_case_time_ns",
    "all_cases_correct",
    "total_error_count",
)
CASE_AUDIT_FIELDS = (
    "protocol_version",
    "execution_id",
    "case_id",
    "case_index",
    "family",
    "n",
    "seed",
    "sequence_sha256",
    "oracle_valid",
    "oracle_reason",
    *STRUCTURAL_FIELDS,
    "audit_execution_mode",
    "audit_passed",
    "diagnostic_output_sha256",
    "diagnostic_processed_count",
    "diagnostic_trace_event_count",
    *PAPER_AUDIT_FIELDS,
)


@dataclass(frozen=True)
class Week11ExecutionConfig:
    """Hold an in-memory execution contract derived from the protocol."""

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
            raise ValueError(f"family is not part of this execution: {family}")
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


def build_execution_config(protocol=WEEK11_EXPERIMENT_PROTOCOL):
    """Derive the executable contract without copying protocol values."""
    validate_week11_experiment_protocol(protocol)
    return Week11ExecutionConfig(
        protocol_version=protocol.protocol_version,
        sizes=tuple(protocol.sizes),
        valid_families=tuple(protocol.valid_families),
        randomized_cases=protocol.randomized_cases,
        warmup_runs=protocol.warmup_runs,
        measured_runs=protocol.measured_runs,
        algorithms=tuple(protocol.algorithms),
        paper_execution_mode=protocol.paper_execution_mode,
        audit_execution_mode=protocol.audit_execution_mode,
        seed=protocol.seed,
        algorithm_order_seed=protocol.algorithm_order_seed,
        case_order_seed=protocol.case_order_seed,
    )


def validate_execution_config(config):
    """Validate a frozen-derived or deliberately reduced test configuration."""
    if not isinstance(config, Week11ExecutionConfig):
        raise TypeError("config must be a Week11ExecutionConfig")
    if not config.protocol_version:
        raise ValueError("protocol_version must be non-empty")
    if config.protocol_version != WEEK11_EXPERIMENT_PROTOCOL.protocol_version:
        raise ValueError("protocol_version does not match the frozen protocol")
    if not config.sizes or len(set(config.sizes)) != len(config.sizes):
        raise ValueError("sizes must be non-empty and unique")
    if any(
        isinstance(n, bool) or not isinstance(n, int) or n < 1
        for n in config.sizes
    ):
        raise ValueError("sizes must be positive integers")
    if (
        not config.valid_families
        or len(set(config.valid_families)) != len(config.valid_families)
        or not set(config.valid_families).issubset(
            WEEK11_EXPERIMENT_PROTOCOL.valid_families
        )
    ):
        raise ValueError("valid families must be a unique frozen subset")
    if config.algorithms != WEEK11_EXPERIMENT_PROTOCOL.algorithms:
        raise ValueError("algorithms must match the frozen Week 11 order")
    if set(config.algorithms) != set(ALGORITHMS):
        raise RuntimeError("algorithm registry does not match the protocol")
    if config.paper_execution_mode != MINIMAL_MODE:
        raise ValueError("paper timing mode must be minimal")
    if config.audit_execution_mode != CHECKED_MODE:
        raise ValueError("audit execution mode must be checked")
    if (
        isinstance(config.randomized_cases, bool)
        or not isinstance(config.randomized_cases, int)
        or config.randomized_cases < 1
    ):
        raise ValueError("randomized_cases must be a positive integer")
    if (
        isinstance(config.warmup_runs, bool)
        or not isinstance(config.warmup_runs, int)
        or config.warmup_runs < 0
    ):
        raise ValueError("warmup_runs must be a non-negative integer")
    if (
        isinstance(config.measured_runs, bool)
        or not isinstance(config.measured_runs, int)
        or config.measured_runs < 1
    ):
        raise ValueError("measured_runs must be a positive integer")
    for field_name in ("seed", "algorithm_order_seed", "case_order_seed"):
        value = getattr(config, field_name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
    return config


def seed_for_case(family, n, case_number, base_seed):
    """Return the established deterministic seed for one generated case."""
    if family == INCREMENTAL_VALID:
        return base_seed + n * 1000 + case_number
    return None


def _sequence_sha256(sequence):
    payload = json.dumps(
        list(sequence),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _csv_value(value):
    return "" if value is None else value


def _python_sort_algorithm(values, paper_execution_mode):
    del paper_execution_mode
    return python_sort(values)


def _reference_algorithm(values, paper_execution_mode):
    del paper_execution_mode
    return simplified_jordan_sort(values)


def _paper_algorithm(values, paper_execution_mode):
    return paper_jordan_sort_valid(
        values,
        execution_mode=paper_execution_mode,
    )


ALGORITHMS = {
    "python_sort": _python_sort_algorithm,
    "simplified_jordan_reference": _reference_algorithm,
    PAPER_ALGORITHM_NAME: _paper_algorithm,
}


def _extract_sorted_output(algorithm_name, result):
    if algorithm_name == "simplified_jordan_reference":
        return result["sorted"]
    if algorithm_name in {"python_sort", PAPER_ALGORITHM_NAME}:
        return result
    raise ValueError(f"unknown algorithm: {algorithm_name}")


def _case_audit_row(config, execution_id, case, diagnostics):
    profile = case["profile"]
    oracle_result = case["oracle"]
    row = {
        "protocol_version": config.protocol_version,
        "execution_id": execution_id,
        "case_id": case["case_id"],
        "case_index": case["case_index"],
        "family": case["family"],
        "n": case["n"],
        "seed": _csv_value(case["seed"]),
        "sequence_sha256": case["sequence_sha256"],
        "oracle_valid": oracle_result["valid"],
        "oracle_reason": _csv_value(oracle_result["reason"]),
        **{field: _csv_value(profile[field]) for field in STRUCTURAL_FIELDS},
        "audit_execution_mode": config.audit_execution_mode,
        "audit_passed": case["audit_passed"],
        "diagnostic_output_sha256": _sequence_sha256(
            diagnostics["output"]
        ),
        "diagnostic_processed_count": diagnostics["processed_count"],
        "diagnostic_trace_event_count": len(diagnostics["trace"]),
        **{
            f"paper_{name}": diagnostics["metrics"][name]
            for name in PAPER_METRIC_NAMES
        },
    }
    return {field: _csv_value(row.get(field)) for field in CASE_AUDIT_FIELDS}


def build_cases_and_audits(config, execution_id):
    """Certify and audit every exact case before any timing may begin."""
    validate_execution_config(config)
    validate_execution_id(execution_id)
    cases = []
    audit_rows = []
    sequence_hashes_by_group = {}
    for family in config.valid_families:
        repetitions = config.repetitions_for_family(family)
        for n in config.sizes:
            for case_number in range(1, repetitions + 1):
                case_seed = seed_for_case(
                    family,
                    n,
                    case_number,
                    config.seed,
                )
                sequence = generate_sequence(family, n, seed=case_seed)
                if len(sequence) != n:
                    raise RuntimeError(
                        "Week 11 generator returned the wrong length: "
                        f"family={family}, expected={n}, actual={len(sequence)}"
                    )
                oracle_result = oracle(sequence)
                if not oracle_result["valid"]:
                    raise RuntimeError(
                        "Week 11 sorting requires an oracle-certified valid "
                        f"input: family={family}, n={n}, "
                        f"reason={oracle_result['reason']}"
                    )

                sequence_sha256 = _sequence_sha256(sequence)
                group_key = (family, n)
                group_hashes = sequence_hashes_by_group.setdefault(
                    group_key,
                    set(),
                )
                if sequence_sha256 in group_hashes:
                    raise RuntimeError(
                        "Week 11 generator returned a duplicate case: "
                        f"family={family}, n={n}, seed={case_seed}"
                    )
                group_hashes.add(sequence_sha256)

                profile = structure_profile(
                    sequence,
                    oracle_result=oracle_result,
                )
                diagnostics = paper_jordan_diagnostics_valid(sequence)
                audit_passed = (
                    diagnostics["invariants_valid"]
                    and diagnostics["output"] == oracle_result["sorted"]
                    and diagnostics["processed_count"] == len(sequence)
                )
                if not audit_passed:
                    raise RuntimeError(
                        "checked paper diagnostics failed before timing: "
                        f"family={family}, n={n}, seed={case_seed}"
                    )

                case = {
                    "case_id": make_case_id(family, len(sequence), case_number),
                    "case_index": len(cases) + 1,
                    "family": family,
                    "n": len(sequence),
                    "seed": case_seed,
                    "sequence_sha256": sequence_sha256,
                    "sequence": sequence,
                    "oracle": oracle_result,
                    "profile": profile,
                    "audit_passed": audit_passed,
                }
                cases.append(case)
                audit_rows.append(
                    _case_audit_row(config, execution_id, case, diagnostics)
                )

    if len(cases) != config.case_count:
        raise RuntimeError(
            f"expected {config.case_count} cases, generated {len(cases)}"
        )
    return cases, audit_rows


def algorithm_order_for_round(
    algorithms,
    seed,
    case_index,
    measured_round,
):
    """Return a deterministic cyclically balanced algorithm order."""
    ordered = list(algorithms)
    random.Random(seed + case_index * 1009).shuffle(ordered)
    shift = (measured_round - 1) % len(ordered)
    return ordered[shift:] + ordered[:shift]


def order_cases(cases, case_order_seed):
    """Return deterministically shuffled case copies with fixed positions."""
    ordered = [dict(case) for case in cases]
    random.Random(case_order_seed).shuffle(ordered)
    for position, case in enumerate(ordered, start=1):
        case["case_execution_position"] = position
    return ordered


def _time_once_algorithm(
    algorithm_name,
    sequence,
    paper_execution_mode,
):
    """Time only one algorithm call on an isolated input list."""
    try:
        algorithm = ALGORITHMS[algorithm_name]
    except KeyError as exc:
        raise ValueError(f"unknown algorithm: {algorithm_name}") from exc

    values = list(sequence)
    was_enabled = gc.isenabled()
    if was_enabled:
        gc.disable()
    try:
        start = time.perf_counter_ns()
        result = algorithm(values, paper_execution_mode)
        end = time.perf_counter_ns()
    finally:
        if gc.isenabled() != was_enabled:
            if was_enabled:
                gc.enable()
            else:
                gc.disable()
    return result, end - start


def run_timed_algorithm(
    algorithm_name,
    sequence,
    oracle_result,
    paper_execution_mode,
    run_index,
    algorithm_position="",
):
    """Run one timing after certification, returning a fail-recording result."""
    try:
        result, time_ns = _time_once_algorithm(
            algorithm_name,
            sequence,
            paper_execution_mode,
        )
        output = _extract_sorted_output(algorithm_name, result)
        return {
            "run_index": run_index,
            "measured_round": run_index,
            "algorithm_position": algorithm_position,
            "time_ns": time_ns,
            "output_correct": output == oracle_result["sorted"],
            "error": "",
        }
    except Exception as exc:
        return {
            "run_index": run_index,
            "measured_round": run_index,
            "algorithm_position": algorithm_position,
            "time_ns": "",
            "output_correct": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _raw_metadata(config, execution_id, case, algorithm_name):
    return {
        "protocol_version": config.protocol_version,
        "execution_id": execution_id,
        "case_id": case["case_id"],
        "case_index": case["case_index"],
        "family": case["family"],
        "n": case["n"],
        "seed": _csv_value(case["seed"]),
        "sequence_sha256": case["sequence_sha256"],
        "case_execution_position": case["case_execution_position"],
        **{
            field: _csv_value(case["profile"][field])
            for field in STRUCTURAL_FIELDS
        },
        "algorithm": algorithm_name,
        "paper_execution_mode": config.paper_execution_mode,
        "audit_execution_mode": config.audit_execution_mode,
        "oracle_valid": case["oracle"]["valid"],
        "oracle_reason": _csv_value(case["oracle"]["reason"]),
        "audit_passed": case["audit_passed"],
    }


def make_raw_rows(
    config,
    certified_cases,
    execution_id,
):
    """Warm up and time only after all case certifications have completed."""
    validate_execution_config(config)
    validate_execution_id(execution_id)
    if len(certified_cases) != config.case_count:
        raise ValueError("certified case count does not match the configuration")

    rows = []
    for case in order_cases(certified_cases, config.case_order_seed):
        warmup_order = algorithm_order_for_round(
            config.algorithms,
            config.algorithm_order_seed,
            case["case_index"],
            measured_round=1,
        )
        for algorithm_name in warmup_order:
            for _ in range(config.warmup_runs):
                result = run_timed_algorithm(
                    algorithm_name,
                    case["sequence"],
                    case["oracle"],
                    config.paper_execution_mode,
                    run_index=0,
                )
                if result["error"] or not result["output_correct"]:
                    raise RuntimeError(
                        "Week 11 warm-up failed for "
                        f"{case['case_id']}, algorithm={algorithm_name}: "
                        f"{result['error']}"
                    )

        for run_index in range(1, config.measured_runs + 1):
            round_order = algorithm_order_for_round(
                config.algorithms,
                config.algorithm_order_seed,
                case["case_index"],
                measured_round=run_index,
            )
            for algorithm_position, algorithm_name in enumerate(
                round_order,
                start=1,
            ):
                row = {
                    **_raw_metadata(
                        config,
                        execution_id,
                        case,
                        algorithm_name,
                    ),
                    **run_timed_algorithm(
                        algorithm_name,
                        case["sequence"],
                        case["oracle"],
                        config.paper_execution_mode,
                        run_index=run_index,
                        algorithm_position=algorithm_position,
                    ),
                }
                rows.append(
                    {
                        field: _csv_value(row.get(field))
                        for field in RAW_FIELDS
                    }
                )
    return rows


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _quartiles(values):
    if not values:
        return "", "", ""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0], ordered[0], 0
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 0:
        lower = ordered[:midpoint]
        upper = ordered[midpoint:]
    else:
        lower = ordered[:midpoint]
        upper = ordered[midpoint + 1 :]
    q1 = statistics.median(lower) if lower else ordered[0]
    q3 = statistics.median(upper) if upper else ordered[-1]
    return q1, q3, q3 - q1


def summarize_by_case(raw_rows):
    """Aggregate measured timings by case and algorithm."""
    grouped = {}
    for row in raw_rows:
        grouped.setdefault((row["case_id"], row["algorithm"]), []).append(row)

    summaries = []
    for (case_id, algorithm_name), rows in sorted(grouped.items()):
        times = [
            int(row["time_ns"])
            for row in rows
            if row["time_ns"] not in {"", None}
        ]
        q1, q3, iqr = _quartiles(times)
        first = rows[0]
        summary = {
            "case_id": case_id,
            "family": first["family"],
            "n": first["n"],
            "algorithm": algorithm_name,
            "measured_run_count": len(times),
            "median_time_ns": statistics.median(times) if times else "",
            "q1_time_ns": q1,
            "q3_time_ns": q3,
            "iqr_time_ns": iqr,
            "mean_time_ns": statistics.mean(times) if times else "",
            "stdev_time_ns": statistics.stdev(times) if len(times) > 1 else 0,
            "all_correct": all(
                _as_bool(row["oracle_valid"])
                and _as_bool(row["output_correct"])
                and _as_bool(row["audit_passed"])
                and not row["error"]
                for row in rows
            ),
            "error_count": sum(1 for row in rows if row["error"]),
        }
        summaries.append(
            {
                field: _csv_value(summary.get(field))
                for field in CASE_SUMMARY_FIELDS
            }
        )
    return summaries


def summarize_by_group(case_rows):
    """Aggregate case medians by family, size, and algorithm."""
    grouped = {}
    for row in case_rows:
        grouped.setdefault(
            (row["family"], row["n"], row["algorithm"]),
            [],
        ).append(row)

    summaries = []
    for (family, n, algorithm_name), rows in sorted(grouped.items()):
        medians = [
            float(row["median_time_ns"])
            for row in rows
            if row["median_time_ns"] not in {"", None}
        ]
        q1, q3, iqr = _quartiles(medians)
        summary = {
            "family": family,
            "n": n,
            "algorithm": algorithm_name,
            "case_count": len(rows),
            "median_case_time_ns": (
                statistics.median(medians) if medians else ""
            ),
            "q1_case_time_ns": q1,
            "q3_case_time_ns": q3,
            "iqr_case_time_ns": iqr,
            "mean_case_time_ns": (
                statistics.mean(medians) if medians else ""
            ),
            "all_cases_correct": all(
                _as_bool(row["all_correct"]) for row in rows
            ),
            "total_error_count": sum(int(row["error_count"]) for row in rows),
        }
        summaries.append(
            {
                field: _csv_value(summary.get(field))
                for field in GROUP_SUMMARY_FIELDS
            }
        )
    return summaries


def run_pilot_in_memory(config, execution_id):
    """Execute a supplied contract without writing any evidence files."""
    validate_execution_config(config)
    validate_execution_id(execution_id)
    cases, audit_rows = build_cases_and_audits(config, execution_id)
    raw_rows = make_raw_rows(config, cases, execution_id)
    case_rows = summarize_by_case(raw_rows)
    group_rows = summarize_by_group(case_rows)

    expected_counts = (
        config.raw_row_count,
        config.case_summary_row_count,
        config.group_summary_row_count,
        config.case_count,
    )
    actual_counts = (
        len(raw_rows),
        len(case_rows),
        len(group_rows),
        len(audit_rows),
    )
    if actual_counts != expected_counts:
        raise RuntimeError(
            f"Week 11 row counts changed: expected={expected_counts}, "
            f"actual={actual_counts}"
        )
    return {
        "raw_rows": raw_rows,
        "case_summary_rows": case_rows,
        "group_summary_rows": group_rows,
        "case_audit_rows": audit_rows,
    }


@dataclass(frozen=True)
class Week11PilotPaths:
    """Hold the fixed output contract for one Week 11 execution."""

    run_dir: Path
    raw_csv: Path
    case_summary_csv: Path
    group_summary_csv: Path
    case_audit_csv: Path
    config_json: Path
    environment_json: Path
    manifest_json: Path
    validation_report_json: Path

    @property
    def evidence_paths(self):
        return tuple(getattr(self, field_name) for field_name in (
            "raw_csv",
            "case_summary_csv",
            "group_summary_csv",
            "case_audit_csv",
            "config_json",
            "environment_json",
            "manifest_json",
            "validation_report_json",
        ))


def build_pilot_paths(
    project_root=PROJECT_ROOT,
    *,
    execution_id,
):
    """Resolve one execution-specific output directory under a project root."""
    validate_execution_id(execution_id)
    root = Path(project_root)
    run_dir = root / output_dir_for_execution(execution_id)
    paths = Week11PilotPaths(
        run_dir=run_dir,
        raw_csv=run_dir / "raw.csv",
        case_summary_csv=run_dir / "case_summary.csv",
        group_summary_csv=run_dir / "group_summary.csv",
        case_audit_csv=run_dir / "case_audit.csv",
        config_json=run_dir / "config.json",
        environment_json=run_dir / "environment.json",
        manifest_json=run_dir / "manifest.json",
        validation_report_json=run_dir / "validation_report.json",
    )
    if tuple(path.name for path in paths.evidence_paths) != EVIDENCE_FILENAMES:
        raise RuntimeError("Week 11 evidence filenames changed")
    if any(path.parent != run_dir for path in paths.evidence_paths):
        raise RuntimeError("Week 11 evidence must be direct children of run_dir")
    return paths


def require_unused_output(paths):
    """Reject any pre-existing formal run directory or evidence file."""
    existing = [path for path in paths.evidence_paths if path.exists()]
    if paths.run_dir.exists() or existing:
        raise RuntimeError(
            "Week 11 execution output is already in use: "
            f"run_dir={paths.run_dir}, existing={existing}"
        )
    return paths


def _git_output(project_root, *args):
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _remote_main_sha(project_root):
    """Query the real remote main ref without trusting a tracking ref."""
    output = _git_output(
        project_root,
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/heads/main",
    )
    lines = [line.split() for line in output.splitlines() if line.strip()]
    if len(lines) != 1 or len(lines[0]) != 2:
        raise RuntimeError("could not resolve exactly one remote main ref")
    sha, ref_name = lines[0]
    if ref_name != "refs/heads/main" or len(sha) not in {40, 64}:
        raise RuntimeError("origin main returned an invalid ref record")
    try:
        int(sha, 16)
    except ValueError as exc:
        raise RuntimeError("origin main returned a non-hex commit SHA") from exc
    return sha


def git_snapshot(project_root=PROJECT_ROOT):
    """Return the clean/pushed source state required by the formal runner."""
    root = Path(project_root)
    status = _git_output(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    head = _git_output(root, "rev-parse", "HEAD")
    origin_main = _remote_main_sha(root)
    return {
        "head": head,
        "origin_main": origin_main,
        "origin_main_source": "git_ls_remote",
        "git_clean": status == "",
        "head_pushed": head == origin_main,
    }


def require_clean_pushed_git(snapshot):
    """Reject a dirty or unpushed source state."""
    if snapshot.get("git_clean") is not True:
        raise RuntimeError("Week 11 preflight requires a clean worktree")
    if snapshot.get("head_pushed") is not True:
        raise RuntimeError("Week 11 preflight requires HEAD == origin/main")
    return snapshot


def build_config_record(
    protocol=WEEK11_EXPERIMENT_PROTOCOL,
):
    """Build machine-independent config.json content from the protocol."""
    return protocol_to_dict(protocol)


def _capture_command(command):
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {"success": False, "output": "unavailable"}
    return {
        "success": True,
        "output": completed.stdout.strip() or "unavailable",
    }


def _processor_class():
    """Capture an anonymous processor class without device identifiers."""
    system = platform.system()
    if system == "Linux":
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            cpuinfo = ""
        cpu_fields = {}
        for line in cpuinfo.splitlines():
            key, separator, value = line.partition(":")
            normalized_key = key.strip().lower()
            candidate = value.strip()
            if separator and candidate and normalized_key not in cpu_fields:
                cpu_fields[normalized_key] = candidate
        for field in ("model name", "hardware", "processor"):
            if field in cpu_fields:
                return cpu_fields[field]
    if system != "Darwin":
        return platform.processor() or platform.machine() or "unavailable"
    captured = _capture_command(
        ["system_profiler", "SPHardwareDataType", "-json"]
    )
    if not captured["success"]:
        return "unavailable"
    try:
        payload = json.loads(captured["output"])
        hardware = payload["SPHardwareDataType"][0]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return "unavailable"
    return hardware.get("chip_type", "unavailable")


def _physical_memory_gb():
    if platform.system() == "Darwin":
        captured = _capture_command(["sysctl", "-n", "hw.memsize"])
        if not captured["success"]:
            raise RuntimeError("could not capture physical memory")
        try:
            memory_bytes = int(captured["output"])
        except (TypeError, ValueError) as exc:
            raise RuntimeError("physical memory is not an integer") from exc
    else:
        try:
            memory_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf(
                "SC_PHYS_PAGES"
            )
        except (AttributeError, OSError, TypeError, ValueError) as exc:
            raise RuntimeError("could not capture physical memory") from exc
    if memory_bytes <= 0:
        raise RuntimeError("physical memory must be positive")
    return round(memory_bytes / (1024**3), 2)


def capture_benchmark_environment():
    """Capture anonymous performance-relevant environment metadata."""
    is_macos = platform.system() == "Darwin"
    build = (
        _capture_command(["sw_vers", "-buildVersion"])
        if is_macos
        else {"success": True, "output": platform.version()}
    )
    os_name = "macOS" if is_macos else platform.system()
    return {
        "processor_class": _processor_class(),
        "architecture": platform.machine(),
        "memory_gb": _physical_memory_gb(),
        "logical_cpu_count": os.cpu_count(),
        "os_name": os_name,
        "os_version": platform.mac_ver()[0] or platform.release(),
        "os_build": build["output"],
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }


def _unavailable_power_status(source):
    return {
        "source": source,
        "status": "unavailable",
        "on_ac_power": None,
        "battery_state": "unknown",
        "battery_percent": None,
        "low_power_mode": None,
    }


def _linux_power_status(power_supply_root=Path("/sys/class/power_supply")):
    """Read anonymous Linux power state from sysfs when available."""
    root = Path(power_supply_root)
    if not root.is_dir():
        return _unavailable_power_status("linux_sysfs")
    try:
        supplies = sorted(root.iterdir())
    except OSError:
        return _unavailable_power_status("linux_sysfs")

    batteries = []
    battery_percentages = []
    line_power = []
    type_read_error = False
    capacity_read_error = False
    for supply in supplies:
        try:
            supply_type = (supply / "type").read_text(
                encoding="utf-8"
            ).strip()
        except OSError:
            type_read_error = True
            continue
        if supply_type == "Battery":
            try:
                batteries.append(
                    (supply / "status").read_text(
                        encoding="utf-8"
                    ).strip().lower()
                )
            except OSError:
                batteries.append("unknown")
            try:
                capacity = int(
                    (supply / "capacity").read_text(
                        encoding="utf-8"
                    ).strip()
                )
                if not 0 <= capacity <= 100:
                    raise ValueError("battery capacity is out of range")
                battery_percentages.append(capacity)
            except (OSError, ValueError):
                capacity_read_error = True
        elif supply_type in {"Mains", "USB", "USB_C"}:
            try:
                line_power.append(
                    (supply / "online").read_text(
                        encoding="utf-8"
                    ).strip()
                    == "1"
                )
            except OSError:
                continue

    if type_read_error or capacity_read_error:
        return _unavailable_power_status("linux_sysfs")

    if not batteries:
        return {
            "source": "linux_sysfs",
            "status": "not_applicable",
            "on_ac_power": None,
            "battery_state": "not_applicable",
            "battery_percent": None,
            "low_power_mode": None,
        }

    if "discharging" in batteries:
        battery_state = "discharging"
    elif "charging" in batteries:
        battery_state = "charging"
    elif batteries and all(state == "full" for state in batteries):
        battery_state = "full"
    else:
        battery_state = "unknown"
    on_ac_power = (
        any(line_power)
        if line_power
        else battery_state in {"charging", "full"}
    )
    return {
        "source": "linux_sysfs",
        "status": "available",
        "on_ac_power": on_ac_power,
        "battery_state": battery_state,
        "battery_percent": min(battery_percentages),
        "low_power_mode": None,
    }


def _pmset_active_profile(battery_output):
    match = re.search(
        r"(?im)^now drawing from ['\"]([^'\"]+)['\"]\s*$",
        battery_output,
    )
    return match.group(1).strip() if match is not None else None


def _pmset_profile_section(settings_output, profile_name):
    """Return only the named top-level pmset custom profile section."""
    if not isinstance(profile_name, str) or not profile_name:
        return None
    target = profile_name.casefold()
    active = False
    section_lines = []
    found = False
    for line in settings_output.splitlines():
        stripped = line.strip()
        is_header = (
            bool(stripped)
            and not line[:1].isspace()
            and stripped.endswith(":")
        )
        if is_header:
            active = stripped[:-1].strip().casefold() == target
            found = found or active
            continue
        if active:
            section_lines.append(line)
    return "\n".join(section_lines) if found else None


def _pmset_low_power_mode(settings_output, profile_name):
    section = _pmset_profile_section(settings_output, profile_name)
    if section is None:
        return None
    values = {}
    for key, raw_value in re.findall(
        r"(?im)^\s*(lowpowermode|powermode)\s+(-?\d+)\s*$",
        section,
    ):
        values.setdefault(key.casefold(), set()).add(int(raw_value))
    if "powermode" in values:
        if len(values["powermode"]) != 1:
            return None
        return {0: False, 1: True, 2: False}.get(
            next(iter(values["powermode"]))
        )
    if "lowpowermode" in values:
        if len(values["lowpowermode"]) != 1:
            return None
        return {0: False, 1: True}.get(
            next(iter(values["lowpowermode"]))
        )
    return None


def _pmset_battery_reading(battery_output):
    match = re.search(r"(\d{1,3})%;\s*([^;]+);", battery_output)
    if match is None:
        return None
    battery_percent = int(match.group(1))
    if not 0 <= battery_percent <= 100:
        return None
    raw_state = match.group(2).strip().casefold()
    battery_state = {
        "charging": "charging",
        "charged": "full",
        "full": "full",
        "discharging": "discharging",
    }.get(raw_state, "unknown")
    return battery_percent, battery_state


def capture_power_status():
    """Capture a cross-platform, device-anonymous power status."""
    system = platform.system()
    if system == "Darwin":
        battery = _capture_command(["pmset", "-g", "batt"])
        if not battery["success"]:
            return _unavailable_power_status("pmset")
        active_profile = _pmset_active_profile(battery["output"])
        battery_reading = _pmset_battery_reading(battery["output"])
        if active_profile is None or battery_reading is None:
            return _unavailable_power_status("pmset")
        battery_percent, battery_state = battery_reading
        settings = _capture_command(["pmset", "-g", "custom"])
        low_power_mode = None
        if settings["success"]:
            low_power_mode = _pmset_low_power_mode(
                settings["output"],
                active_profile,
            )
        return {
            "source": "pmset",
            "status": "available",
            "on_ac_power": active_profile.casefold() == "ac power",
            "battery_state": battery_state,
            "battery_percent": battery_percent,
            "low_power_mode": low_power_mode,
        }
    if system == "Linux":
        return _linux_power_status()
    return _unavailable_power_status(system.lower() or "unknown")


def validate_power_status(power_status):
    """Validate power metadata without imposing the Day 5 readiness rule."""
    if not isinstance(power_status, dict):
        raise TypeError("power_status must be a dictionary")
    if set(power_status) != set(POWER_STATUS_FIELDS):
        raise ValueError("power_status fields changed")
    if (
        not isinstance(power_status["source"], str)
        or not power_status["source"]
    ):
        raise ValueError("power_status source is invalid")
    status = power_status["status"]
    if status not in {"available", "not_applicable", "unavailable"}:
        raise ValueError("power_status status is invalid")
    on_ac_power = power_status["on_ac_power"]
    if on_ac_power is not None and not isinstance(on_ac_power, bool):
        raise ValueError("power_status on_ac_power is invalid")
    battery_state = power_status["battery_state"]
    if battery_state not in {
        "charging",
        "discharging",
        "full",
        "not_applicable",
        "unknown",
    }:
        raise ValueError("power_status battery_state is invalid")
    battery_percent = power_status["battery_percent"]
    if battery_percent is not None and (
        not isinstance(battery_percent, int)
        or isinstance(battery_percent, bool)
        or not 0 <= battery_percent <= 100
    ):
        raise ValueError("power_status battery_percent is invalid")
    low_power_mode = power_status["low_power_mode"]
    if low_power_mode is not None and not isinstance(low_power_mode, bool):
        raise ValueError("power_status low_power_mode is invalid")
    if status == "available":
        if (
            not isinstance(on_ac_power, bool)
            or battery_state
            not in {"charging", "discharging", "full", "unknown"}
            or not isinstance(battery_percent, int)
        ):
            raise ValueError("available power_status is inconsistent")
    elif status == "not_applicable":
        if (
            on_ac_power is not None
            or battery_state != "not_applicable"
            or battery_percent is not None
            or low_power_mode is not None
        ):
            raise ValueError("not-applicable power_status is inconsistent")
    elif (
        on_ac_power is not None
        or battery_state != "unknown"
        or battery_percent is not None
        or low_power_mode is not None
    ):
        raise ValueError("unavailable power_status is inconsistent")
    return power_status


def capture_load_status(logical_cpu_count=None):
    """Capture normalized load values for the Day 5 timing-readiness gate."""
    cpu_count = (
        logical_cpu_count
        if logical_cpu_count is not None
        else os.cpu_count()
    )
    if (
        not isinstance(cpu_count, int)
        or isinstance(cpu_count, bool)
        or cpu_count <= 0
    ):
        raise RuntimeError("logical CPU count is unavailable or invalid")
    try:
        raw_loads = os.getloadavg()
    except (AttributeError, OSError) as exc:
        raise RuntimeError("system load averages are unavailable") from exc
    if len(raw_loads) != 3:
        raise RuntimeError("system load average shape changed")
    loads = tuple(float(value) for value in raw_loads)
    if any(not math.isfinite(value) or value < 0 for value in loads):
        raise RuntimeError("system load averages are invalid")

    one_minute, five_minute, fifteen_minute = loads
    one_per_cpu = one_minute / cpu_count
    five_per_cpu = five_minute / cpu_count
    delta_per_cpu = abs(one_minute - five_minute) / cpu_count
    return {
        "logical_cpu_count": cpu_count,
        "one_minute_load": one_minute,
        "five_minute_load": five_minute,
        "fifteen_minute_load": fifteen_minute,
        "one_minute_load_per_cpu": one_per_cpu,
        "five_minute_load_per_cpu": five_per_cpu,
        "one_five_delta_per_cpu": delta_per_cpu,
        "max_allowed_load_per_cpu": MAX_TIMING_LOAD_PER_CPU,
        "max_allowed_delta_per_cpu": MAX_TIMING_LOAD_DELTA_PER_CPU,
        "low": (
            max(one_per_cpu, five_per_cpu)
            <= MAX_TIMING_LOAD_PER_CPU
        ),
        "stable": delta_per_cpu <= MAX_TIMING_LOAD_DELTA_PER_CPU,
    }


def validate_load_status(load_status):
    """Reject malformed or internally inconsistent load measurements."""
    if not isinstance(load_status, dict):
        raise TypeError("load_status must be a dictionary")
    if set(load_status) != set(LOAD_STATUS_FIELDS):
        raise ValueError("load_status fields changed")
    cpu_count = load_status["logical_cpu_count"]
    if (
        not isinstance(cpu_count, int)
        or isinstance(cpu_count, bool)
        or cpu_count <= 0
    ):
        raise ValueError("load_status logical CPU count is invalid")
    numeric_fields = (
        "one_minute_load",
        "five_minute_load",
        "fifteen_minute_load",
        "one_minute_load_per_cpu",
        "five_minute_load_per_cpu",
        "one_five_delta_per_cpu",
        "max_allowed_load_per_cpu",
        "max_allowed_delta_per_cpu",
    )
    for field_name in numeric_fields:
        value = load_status[field_name]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"load_status {field_name} is invalid")
    if load_status["max_allowed_load_per_cpu"] != MAX_TIMING_LOAD_PER_CPU:
        raise ValueError("load_status load threshold changed")
    if (
        load_status["max_allowed_delta_per_cpu"]
        != MAX_TIMING_LOAD_DELTA_PER_CPU
    ):
        raise ValueError("load_status stability threshold changed")

    one_per_cpu = load_status["one_minute_load"] / cpu_count
    five_per_cpu = load_status["five_minute_load"] / cpu_count
    delta_per_cpu = abs(
        load_status["one_minute_load"] - load_status["five_minute_load"]
    ) / cpu_count
    expected_numeric = {
        "one_minute_load_per_cpu": one_per_cpu,
        "five_minute_load_per_cpu": five_per_cpu,
        "one_five_delta_per_cpu": delta_per_cpu,
    }
    for field_name, expected in expected_numeric.items():
        if not math.isclose(
            load_status[field_name],
            expected,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError(f"load_status {field_name} is inconsistent")
    expected_low = max(one_per_cpu, five_per_cpu) <= MAX_TIMING_LOAD_PER_CPU
    expected_stable = delta_per_cpu <= MAX_TIMING_LOAD_DELTA_PER_CPU
    if load_status["low"] is not expected_low:
        raise ValueError("load_status low flag is inconsistent")
    if load_status["stable"] is not expected_stable:
        raise ValueError("load_status stable flag is inconsistent")
    return load_status


def require_timing_ready_environment(environment_record, load_status):
    """Enforce the fail-closed Day 5 power, load, and disk gates."""
    power_status = validate_power_status(environment_record.get("power_status"))
    validated_load = validate_load_status(load_status)
    available_disk = environment_record.get("available_disk_bytes")
    if (
        not isinstance(available_disk, int)
        or isinstance(available_disk, bool)
        or available_disk < 0
    ):
        raise RuntimeError("available disk measurement is invalid")

    discharging_exception = (
        power_status["battery_state"] == "discharging"
        and power_status["battery_percent"] >= 50
        and power_status["low_power_mode"] is False
    ) if power_status["status"] == "available" else False
    power_ready = power_status["status"] == "not_applicable" or (
        power_status["status"] == "available"
        and power_status["on_ac_power"] is True
        and (
            power_status["battery_state"] in {"charging", "full"}
            or discharging_exception
        )
    )
    disk_ready = available_disk >= MIN_TIMING_DISK_BYTES
    failures = []
    if not power_ready:
        failures.append(
            "power must be battery-free, charging/full on AC, or high-charge "
            "discharging on AC with low-power mode disabled"
        )
    if validated_load["low"] is not True:
        failures.append("system load is above the normalized timing threshold")
    if validated_load["stable"] is not True:
        failures.append(
            "system load is not stable across 1- and 5-minute averages"
        )
    if not disk_ready:
        failures.append("at least 1 GiB of free disk space is required")
    if failures:
        raise RuntimeError(
            "Week 11 timing preflight failed: " + "; ".join(failures)
        )
    return {
        "ready": True,
        "power_ready": True,
        "load_low": True,
        "load_stable": True,
        "disk_ready": True,
        "minimum_disk_bytes": MIN_TIMING_DISK_BYTES,
        "available_disk_bytes": available_disk,
        "load_status": validated_load,
    }


def build_environment_record(
    git_state,
    *,
    execution_id,
    protocol=WEEK11_EXPERIMENT_PROTOCOL,
    project_root=PROJECT_ROOT,
    benchmark_environment=None,
):
    """Build the environment.json contract before any future timing."""
    validate_week11_experiment_protocol(protocol)
    validate_execution_id(execution_id)
    require_clean_pushed_git(git_state)
    environment = benchmark_environment or capture_benchmark_environment()
    context = Week11ExecutionContext(
        execution_id=execution_id,
        output_dir=output_dir_for_execution(execution_id),
        benchmark_environment=environment,
        source_commit=git_state["head"],
    )
    validate_execution_context(context)
    power_status = validate_power_status(capture_power_status())
    load = _capture_command(["uptime"])
    return {
        **execution_context_to_dict(context),
        "protocol_version": protocol.protocol_version,
        "captured_before_timing": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_dirty": False,
        "head_matches_origin_main": True,
        "available_disk_bytes": shutil.disk_usage(project_root).free,
        "perf_counter_resolution": time.get_clock_info(
            "perf_counter"
        ).resolution,
        "power_status": power_status,
        "load_command_success": load["success"],
        "load_snapshot": load["output"],
        "paper_execution_mode": protocol.paper_execution_mode,
        "audit_execution_mode": protocol.audit_execution_mode,
    }


def _write_json_exclusive(path, payload):
    """Create one JSON evidence file without permitting replacement."""
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not verify JSON evidence: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON evidence must contain an object: {path}")
    return value


def initialize_evidence_directory(
    paths,
    config_record,
    environment_record,
    protocol=WEEK11_EXPERIMENT_PROTOCOL,
):
    """Atomically reserve a run directory and prewrite timing evidence."""
    validate_week11_experiment_protocol(protocol)
    require_unused_output(paths)
    if config_record != protocol_to_dict(protocol):
        raise ValueError("config does not match the frozen protocol")
    if environment_record.get("protocol_version") != protocol.protocol_version:
        raise ValueError("environment protocol_version does not match config")
    duplicated_environment_fields = sorted(
        set(BENCHMARK_ENVIRONMENT_FIELDS).intersection(environment_record)
    )
    if duplicated_environment_fields:
        raise ValueError(
            "environment must keep benchmark metadata only in "
            f"benchmark_environment: {duplicated_environment_fields}"
        )
    if (
        environment_record.get("paper_execution_mode")
        != protocol.paper_execution_mode
    ):
        raise ValueError("environment paper execution mode does not match protocol")
    if (
        environment_record.get("audit_execution_mode")
        != protocol.audit_execution_mode
    ):
        raise ValueError("environment audit execution mode does not match protocol")
    execution_id = environment_record.get("execution_id")
    benchmark_environment = environment_record.get("benchmark_environment")
    source_commit = environment_record.get("source_commit")
    context = Week11ExecutionContext(
        execution_id=execution_id,
        output_dir=environment_record.get("output_dir"),
        benchmark_environment=benchmark_environment,
        source_commit=source_commit,
    )
    validate_execution_context(context)
    if paths.run_dir.name != execution_id:
        raise ValueError("evidence path does not match execution_id")
    if environment_record.get("captured_before_timing") is not True:
        raise ValueError("environment must be captured before timing")
    power_status = validate_power_status(environment_record.get("power_status"))
    if power_status["status"] == "unavailable":
        raise ValueError("power_status must be available or not_applicable")
    try:
        paths.run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RuntimeError("Week 11 execution output is already in use") from exc

    # Deliberately leave partial evidence in place if a later write fails.
    _write_json_exclusive(paths.config_json, config_record)
    _write_json_exclusive(paths.environment_json, environment_record)

    if _read_json_object(paths.config_json) != config_record:
        raise RuntimeError("config.json verification failed")
    if _read_json_object(paths.environment_json) != environment_record:
        raise RuntimeError("environment.json verification failed")
    return {
        "status": "evidence_initialized_before_timing",
        "run_dir": str(paths.run_dir),
        "config_json": str(paths.config_json),
        "environment_json": str(paths.environment_json),
    }


def initialize_formal_evidence(
    project_root=PROJECT_ROOT,
    *,
    execution_id,
    protocol=WEEK11_EXPERIMENT_PROTOCOL,
):
    """Perform the mandatory evidence prewrite for a future formal run."""
    validate_week11_experiment_protocol(protocol)
    validate_execution_id(execution_id)
    root = Path(project_root)
    paths = require_unused_output(
        build_pilot_paths(root, execution_id=execution_id)
    )
    benchmark_environment = capture_benchmark_environment()
    source = require_clean_pushed_git(git_snapshot(root))
    config = build_config_record(protocol)
    environment = build_environment_record(
        source,
        execution_id=execution_id,
        protocol=protocol,
        project_root=root,
        benchmark_environment=benchmark_environment,
    )
    return initialize_evidence_directory(
        paths,
        config,
        environment,
        protocol,
    )


def run_preflight(
    project_root=PROJECT_ROOT,
    *,
    execution_id,
    protocol=WEEK11_EXPERIMENT_PROTOCOL,
):
    """Validate protocol and execution readiness without creating output."""
    validate_week11_experiment_protocol(protocol)
    validate_execution_id(execution_id)
    root = Path(project_root)
    paths = require_unused_output(
        build_pilot_paths(root, execution_id=execution_id)
    )
    benchmark_environment = capture_benchmark_environment()
    source = require_clean_pushed_git(git_snapshot(root))
    config = build_config_record(protocol)
    environment = build_environment_record(
        source,
        execution_id=execution_id,
        protocol=protocol,
        project_root=root,
        benchmark_environment=benchmark_environment,
    )
    load_status = capture_load_status(
        benchmark_environment["logical_cpu_count"]
    )
    timing_readiness = require_timing_ready_environment(
        environment,
        load_status,
    )
    return {
        "status": "ready_not_executed",
        "protocol_valid": True,
        "protocol_version": protocol.protocol_version,
        "execution_context_valid": True,
        "execution_id": execution_id,
        "benchmark_environment_recorded": True,
        "git_clean": source["git_clean"],
        "head_pushed": source["head_pushed"],
        "head": source["head"],
        "origin_main": source["origin_main"],
        "output_dir": str(paths.run_dir),
        "output_directory_unused": True,
        "case_count": protocol.case_count,
        "expected_raw_rows": protocol.raw_row_count,
        "expected_case_summary_rows": protocol.case_summary_row_count,
        "expected_group_summary_rows": protocol.group_summary_row_count,
        "paper_execution_mode": protocol.paper_execution_mode,
        "audit_execution_mode": protocol.audit_execution_mode,
        "config_contract_ready": config["status"] == "frozen",
        "environment_contract_ready": (
            environment["captured_before_timing"] is True
            and environment["available_disk_bytes"] >= 0
            and environment["power_status"]["status"]
            in {"available", "not_applicable"}
            and "load_command_success" in environment
        ),
        "timing_readiness": timing_readiness,
        "formal_execution_enabled": False,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate the frozen framework without creating evidence",
    )
    parser.add_argument(
        "--execution-id",
        required=True,
        help="identify one run without changing the frozen protocol",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.preflight_only:
        raise RuntimeError(
            "formal Week 11 execution is disabled until the Day 5 preflight"
        )
    print(
        json.dumps(
            run_preflight(execution_id=args.execution_id),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
