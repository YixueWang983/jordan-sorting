"""Run the Week 10 paper timing-contamination experiment."""

import argparse
import csv
import gc
import hashlib
import json
import os
import platform
import random
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    NESTED_VALID,
    generate_sequence,
    make_case_id,
)
from oracle import oracle  # noqa: E402
from paper_execution_policy import (  # noqa: E402
    MINIMAL_MODE,
    PAPER_EXECUTION_MODE_NAMES,
    PAPER_EXECUTION_POLICIES,
)
from paper_jordan_sort import (  # noqa: E402
    paper_jordan_diagnostics_valid,
    paper_jordan_sort_valid,
)
from run_week7_pilot import (  # noqa: E402
    cpu_model,
    file_sha256,
    git_commit_sha,
    git_dirty,
    timestamp_run_id,
)
from stats import structure_profile  # noqa: E402


WEEK10_FAMILIES = [FLAT_VALID, NESTED_VALID, INCREMENTAL_VALID]
WEEK10_SIZES = [32, 64, 128, 256]
WEEK10_RANDOMIZED_CASES = 3
WEEK10_WARMUP_RUNS = 3
WEEK10_MEASURED_RUNS = 15
WEEK10_SEED = 20260723

SMOKE_SIZES = [8, 16, 32]
SMOKE_RANDOMIZED_CASES = 1
SMOKE_WARMUP_RUNS = 1
SMOKE_MEASURED_RUNS = 3

DEFAULT_RUNS_DIR = PROJECT_ROOT / "results" / "runs"
EXECUTION_MODES = list(PAPER_EXECUTION_MODE_NAMES)

STRUCTURAL_FIELDS = [
    "category",
    "upper_interval_count",
    "lower_interval_count",
    "total_interval_count",
    "upper_root_count",
    "lower_root_count",
    "nesting_count",
    "nesting_density",
    "max_depth",
]

RAW_FIELDS = [
    "run_id",
    "case_id",
    "case_index",
    "family",
    "n",
    "seed",
    "sequence_sha256",
    "case_execution_position",
    *STRUCTURAL_FIELDS,
    "execution_mode",
    "record_trace",
    "count_operations",
    "validate_backend_commits",
    "run_index",
    "measured_round",
    "mode_position",
    "time_ns",
    "oracle_valid",
    "output_correct",
    "audit_passed",
    "error",
]

CASE_SUMMARY_FIELDS = [
    "case_id",
    "family",
    "n",
    "execution_mode",
    "measured_run_count",
    "median_time_ns",
    "q1_time_ns",
    "q3_time_ns",
    "iqr_time_ns",
    "mean_time_ns",
    "stdev_time_ns",
    "median_over_minimal_ratio",
    "all_correct",
    "error_count",
]

GROUP_SUMMARY_FIELDS = [
    "family",
    "n",
    "execution_mode",
    "case_count",
    "median_case_time_ns",
    "median_over_minimal_ratio",
    "all_cases_correct",
    "total_error_count",
]


@dataclass(frozen=True)
class ContaminationConfig:
    families: list[str]
    sizes: list[int]
    execution_modes: list[str]
    randomized_cases: int
    warmup_runs: int
    measured_runs: int
    seed: int
    mode_order_seed: int
    case_order_seed: int
    run_id: str
    run_dir: Path
    raw_csv: Path
    case_summary_csv: Path
    group_summary_csv: Path
    environment_json: Path
    config_json: Path
    manifest_json: Path


def build_week10_config(run_id, run_dir, smoke=True):
    """Build the frozen smoke or full Week 10 contamination configuration."""
    root = Path(run_dir)
    return ContaminationConfig(
        families=list(WEEK10_FAMILIES),
        sizes=list(SMOKE_SIZES if smoke else WEEK10_SIZES),
        execution_modes=list(EXECUTION_MODES),
        randomized_cases=(
            SMOKE_RANDOMIZED_CASES if smoke else WEEK10_RANDOMIZED_CASES
        ),
        warmup_runs=SMOKE_WARMUP_RUNS if smoke else WEEK10_WARMUP_RUNS,
        measured_runs=SMOKE_MEASURED_RUNS if smoke else WEEK10_MEASURED_RUNS,
        seed=WEEK10_SEED,
        mode_order_seed=WEEK10_SEED + 7919,
        case_order_seed=WEEK10_SEED + 1543,
        run_id=run_id,
        run_dir=root,
        raw_csv=root / "raw.csv",
        case_summary_csv=root / "case_summary.csv",
        group_summary_csv=root / "group_summary.csv",
        environment_json=root / "environment.json",
        config_json=root / "config.json",
        manifest_json=root / "manifest.json",
    )


def validate_config(config):
    """Validate the fixed Week 10 runner contract."""
    if config.families != WEEK10_FAMILIES:
        raise ValueError("Week 10 families must match the frozen valid families")
    if config.execution_modes != EXECUTION_MODES:
        raise ValueError("Week 10 execution modes must match the fixed registry")
    if not config.sizes or any(
        isinstance(n, bool) or not isinstance(n, int) or n < 1
        for n in config.sizes
    ):
        raise ValueError("sizes must be positive integers")
    if config.randomized_cases < 1:
        raise ValueError("randomized_cases must be positive")
    if config.warmup_runs < 0:
        raise ValueError("warmup_runs must be non-negative")
    if config.measured_runs < 1:
        raise ValueError("measured_runs must be positive")
    if not isinstance(config.run_id, str) or not config.run_id:
        raise ValueError("run_id must be a non-empty string")

    outputs = _output_paths(config)
    if len({path.resolve() for path in outputs}) != len(outputs):
        raise ValueError("output paths must be distinct")
    if any(path.parent.resolve() != config.run_dir.resolve() for path in outputs):
        raise ValueError("all outputs must be direct children of run_dir")
    return config


def validate_no_overwrite(config, overwrite=False):
    """Reject an existing output file unless overwrite is explicit."""
    if overwrite:
        return config
    existing = [path for path in _output_paths(config) if path.exists()]
    if existing:
        raise ValueError(
            f"output files already exist: {[str(path) for path in existing]}"
        )
    return config


def _output_paths(config):
    return [
        config.raw_csv,
        config.case_summary_csv,
        config.group_summary_csv,
        config.environment_json,
        config.config_json,
        config.manifest_json,
    ]


def repetitions_for_family(family, randomized_cases):
    return randomized_cases if family == INCREMENTAL_VALID else 1


def seed_for_case(family, n, index, base_seed):
    if family == INCREMENTAL_VALID:
        return base_seed + n * 1000 + index
    return None


def expected_case_count(config):
    return sum(
        len(config.sizes)
        * repetitions_for_family(family, config.randomized_cases)
        for family in config.families
    )


def build_cases(config):
    """Generate, certify, profile, and completely audit every timed case."""
    cases = []
    for family in config.families:
        repetitions = repetitions_for_family(family, config.randomized_cases)
        for n in config.sizes:
            for case_index in range(1, repetitions + 1):
                case_seed = seed_for_case(family, n, case_index, config.seed)
                sequence = generate_sequence(family, n, seed=case_seed)
                oracle_result = oracle(sequence)
                if not oracle_result["valid"]:
                    raise RuntimeError(
                        "Week 10 paper timing requires an oracle-certified "
                        f"valid input: family={family}, n={n}, "
                        f"reason={oracle_result['reason']}"
                    )

                profile = structure_profile(
                    sequence,
                    oracle_result=oracle_result,
                )
                diagnostics = paper_jordan_diagnostics_valid(sequence)
                audit_passed = (
                    diagnostics["invariants_valid"]
                    and diagnostics["output"] == oracle_result["sorted"]
                )
                if not audit_passed:
                    raise RuntimeError(
                        "checked paper diagnostics failed before timing: "
                        f"family={family}, n={n}, seed={case_seed}"
                    )

                cases.append(
                    {
                        "case_id": make_case_id(
                            family,
                            len(sequence),
                            case_index,
                        ),
                        "case_index": len(cases),
                        "family": family,
                        "n": len(sequence),
                        "seed": case_seed,
                        "sequence_sha256": _sequence_sha256(sequence),
                        "sequence": sequence,
                        "oracle": oracle_result,
                        "profile": profile,
                        "audit_passed": audit_passed,
                    }
                )
    return cases


def mode_order_for_round(execution_modes, seed, case_index, measured_round):
    """Return a deterministic cyclically balanced mode order."""
    ordered = list(execution_modes)
    random.Random(seed + case_index * 1009).shuffle(ordered)
    shift = (measured_round - 1) % len(ordered)
    return ordered[shift:] + ordered[:shift]


def _time_once_mode(execution_mode, sequence):
    """Time only the valid-input public paper sorter for one fixed mode."""
    values = list(sequence)
    was_enabled = gc.isenabled()
    if was_enabled:
        gc.disable()
    try:
        start = time.perf_counter_ns()
        result = paper_jordan_sort_valid(
            values,
            execution_mode=execution_mode,
        )
        end = time.perf_counter_ns()
    finally:
        if was_enabled:
            gc.enable()
    return result, end - start


def run_timed_mode(
    execution_mode,
    sequence,
    oracle_result,
    run_index,
    mode_position="",
):
    """Run one pre-certified mode timing without oracle or diagnostics."""
    try:
        output, time_ns = _time_once_mode(execution_mode, sequence)
        return {
            "run_index": run_index,
            "measured_round": run_index,
            "mode_position": mode_position,
            "time_ns": time_ns,
            "output_correct": output == oracle_result["sorted"],
            "error": "",
        }
    except Exception as exc:
        return {
            "run_index": run_index,
            "measured_round": run_index,
            "mode_position": mode_position,
            "time_ns": "",
            "output_correct": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def make_raw_rows(config):
    """Create raw rows after all case certification and audits finish."""
    cases = build_cases(config)
    random.Random(config.case_order_seed).shuffle(cases)
    for position, case in enumerate(cases, start=1):
        case["case_execution_position"] = position

    rows = []
    for case in cases:
        warmup_order = mode_order_for_round(
            config.execution_modes,
            config.mode_order_seed,
            case["case_index"],
            1,
        )
        for execution_mode in warmup_order:
            for _ in range(config.warmup_runs):
                result = run_timed_mode(
                    execution_mode,
                    case["sequence"],
                    case["oracle"],
                    run_index=0,
                )
                if result["error"] or not result["output_correct"]:
                    raise RuntimeError(
                        "Week 10 warm-up failed for "
                        f"{case['case_id']}, mode={execution_mode}: "
                        f"{result['error']}"
                    )

        for run_index in range(1, config.measured_runs + 1):
            round_order = mode_order_for_round(
                config.execution_modes,
                config.mode_order_seed,
                case["case_index"],
                run_index,
            )
            for mode_position, execution_mode in enumerate(
                round_order,
                start=1,
            ):
                policy = PAPER_EXECUTION_POLICIES[execution_mode]
                row = {
                    "run_id": config.run_id,
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
                    "execution_mode": execution_mode,
                    "record_trace": policy.record_trace,
                    "count_operations": policy.count_operations,
                    "validate_backend_commits": (
                        policy.validate_backend_commits
                    ),
                    "oracle_valid": case["oracle"]["valid"],
                    "audit_passed": case["audit_passed"],
                    **run_timed_mode(
                        execution_mode,
                        case["sequence"],
                        case["oracle"],
                        run_index=run_index,
                        mode_position=mode_position,
                    ),
                }
                rows.append(
                    {
                        field: _csv_value(row.get(field))
                        for field in RAW_FIELDS
                    }
                )
    return rows


def _csv_value(value):
    return "" if value is None else value


def _sequence_sha256(sequence):
    payload = json.dumps(
        list(sequence),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
    """Aggregate measured timings by case and execution mode."""
    grouped = {}
    for row in raw_rows:
        grouped.setdefault(
            (row["case_id"], row["execution_mode"]),
            [],
        ).append(row)

    summaries = []
    for (case_id, execution_mode), rows in sorted(grouped.items()):
        times = [
            int(row["time_ns"])
            for row in rows
            if row["time_ns"] not in {"", None}
        ]
        q1, q3, iqr = _quartiles(times)
        first = rows[0]
        summaries.append(
            {
                "case_id": case_id,
                "family": first["family"],
                "n": first["n"],
                "execution_mode": execution_mode,
                "measured_run_count": len(times),
                "median_time_ns": statistics.median(times) if times else "",
                "q1_time_ns": q1,
                "q3_time_ns": q3,
                "iqr_time_ns": iqr,
                "mean_time_ns": statistics.mean(times) if times else "",
                "stdev_time_ns": (
                    statistics.stdev(times) if len(times) > 1 else 0
                ),
                "median_over_minimal_ratio": "",
                "all_correct": all(
                    _as_bool(row["oracle_valid"])
                    and _as_bool(row["output_correct"])
                    and _as_bool(row["audit_passed"])
                    and not row["error"]
                    for row in rows
                ),
                "error_count": sum(1 for row in rows if row["error"]),
            }
        )

    minimal_medians = {
        row["case_id"]: row["median_time_ns"]
        for row in summaries
        if row["execution_mode"] == MINIMAL_MODE
    }
    for row in summaries:
        baseline = minimal_medians.get(row["case_id"], "")
        if baseline not in {"", 0} and row["median_time_ns"] != "":
            row["median_over_minimal_ratio"] = (
                row["median_time_ns"] / baseline
            )
    return summaries


def summarize_by_group(case_rows):
    """Aggregate case medians by family, size, and execution mode."""
    grouped = {}
    for row in case_rows:
        grouped.setdefault(
            (row["family"], row["n"], row["execution_mode"]),
            [],
        ).append(row)

    summaries = []
    for (family, n, execution_mode), rows in sorted(grouped.items()):
        medians = [
            float(row["median_time_ns"])
            for row in rows
            if row["median_time_ns"] not in {"", None}
        ]
        summaries.append(
            {
                "family": family,
                "n": n,
                "execution_mode": execution_mode,
                "case_count": len(rows),
                "median_case_time_ns": (
                    statistics.median(medians) if medians else ""
                ),
                "median_over_minimal_ratio": "",
                "all_cases_correct": all(
                    _as_bool(row["all_correct"]) for row in rows
                ),
                "total_error_count": sum(
                    int(row["error_count"]) for row in rows
                ),
            }
        )

    minimal_medians = {
        (row["family"], row["n"]): row["median_case_time_ns"]
        for row in summaries
        if row["execution_mode"] == MINIMAL_MODE
    }
    for row in summaries:
        baseline = minimal_medians.get((row["family"], row["n"]), "")
        if baseline not in {"", 0} and row["median_case_time_ns"] != "":
            row["median_over_minimal_ratio"] = (
                row["median_case_time_ns"] / baseline
            )
    return summaries


def write_csv(rows, output_path, fields):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def config_to_dict(config):
    return {
        "run_id": config.run_id,
        "families": config.families,
        "sizes": config.sizes,
        "execution_modes": config.execution_modes,
        "randomized_cases": config.randomized_cases,
        "warmup_runs": config.warmup_runs,
        "measured_runs": config.measured_runs,
        "seed": config.seed,
        "mode_order_seed": config.mode_order_seed,
        "case_order_seed": config.case_order_seed,
        "outputs": {
            "raw_csv": str(config.raw_csv),
            "case_summary_csv": str(config.case_summary_csv),
            "group_summary_csv": str(config.group_summary_csv),
            "environment_json": str(config.environment_json),
            "config_json": str(config.config_json),
            "manifest_json": str(config.manifest_json),
        },
    }


def write_config(config):
    config.config_json.parent.mkdir(parents=True, exist_ok=True)
    config.config_json.write_text(
        json.dumps(config_to_dict(config), indent=2) + "\n",
        encoding="utf-8",
    )


def write_environment(config):
    data = {
        "run_id": config.run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_commit_sha(),
        "git_dirty": git_dirty(),
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_model": cpu_model(),
        "logical_cpu_count": os.cpu_count(),
        "perf_counter_resolution": time.get_clock_info(
            "perf_counter"
        ).resolution,
        "gc_initial_state": gc.isenabled(),
        "config": config_to_dict(config),
    }
    config.environment_json.parent.mkdir(parents=True, exist_ok=True)
    config.environment_json.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def write_manifest(config, raw_rows, case_rows, group_rows):
    files = {
        "raw_csv": config.raw_csv,
        "case_summary_csv": config.case_summary_csv,
        "group_summary_csv": config.group_summary_csv,
        "environment_json": config.environment_json,
        "config_json": config.config_json,
    }
    data = {
        "run_id": config.run_id,
        "git_commit_sha": git_commit_sha(),
        "git_dirty": git_dirty(),
        "row_counts": {
            "raw": len(raw_rows),
            "case_summary": len(case_rows),
            "group_summary": len(group_rows),
        },
        "files": {
            label: {
                "path": str(path),
                "sha256": file_sha256(path),
            }
            for label, path in files.items()
        },
    }
    config.manifest_json.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def run_contamination_experiment(config, overwrite=False):
    """Run one isolated Week 10 smoke or full contamination experiment."""
    validate_config(config)
    validate_no_overwrite(config, overwrite=overwrite)
    raw_rows = make_raw_rows(config)
    case_rows = summarize_by_case(raw_rows)
    group_rows = summarize_by_group(case_rows)

    write_config(config)
    write_csv(raw_rows, config.raw_csv, RAW_FIELDS)
    write_csv(case_rows, config.case_summary_csv, CASE_SUMMARY_FIELDS)
    write_csv(group_rows, config.group_summary_csv, GROUP_SUMMARY_FIELDS)
    write_environment(config)
    write_manifest(config, raw_rows, case_rows, group_rows)
    return raw_rows, case_rows, group_rows


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--full", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    smoke = not args.full
    prefix = "week10_contamination_smoke" if smoke else "week10_contamination"
    run_id = args.run_id or timestamp_run_id(prefix)
    run_dir = args.run_dir or (DEFAULT_RUNS_DIR / run_id)
    config = build_week10_config(run_id, run_dir, smoke=smoke)
    raw_rows, case_rows, group_rows = run_contamination_experiment(
        config,
        overwrite=args.overwrite,
    )
    print(
        f"wrote {len(raw_rows)} raw rows, "
        f"{len(case_rows)} case rows, "
        f"{len(group_rows)} group rows"
    )


if __name__ == "__main__":
    main()
