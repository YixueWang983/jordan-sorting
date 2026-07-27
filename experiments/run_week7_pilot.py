"""Run the Week 7 pilot benchmark with case-level aggregation."""

import argparse
import csv
import gc
import hashlib
import json
import os
import platform
import random
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

from baselines import python_sort, sort_plus_laminarity_check  # noqa: E402
from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    INVALID_LOWER_CROSSING,
    INVALID_UPPER_CROSSING,
    MUTATION_BASED_INVALID,
    NESTED_VALID,
    RANDOM_INVALID,
    generate_sequence,
    make_case_id,
)
from instrumentation import instrumented_reference_run  # noqa: E402
from oracle import oracle  # noqa: E402
from paper_jordan import METRIC_NAMES as PAPER_METRIC_NAMES  # noqa: E402
from paper_jordan_sort import (  # noqa: E402
    paper_jordan_diagnostics_valid,
    paper_jordan_sort_valid,
)
from simplified_jordan import simplified_jordan_sort  # noqa: E402
from stats import structure_profile  # noqa: E402


DETERMINISTIC_FAMILIES = [
    FLAT_VALID,
    NESTED_VALID,
    INVALID_UPPER_CROSSING,
    INVALID_LOWER_CROSSING,
]

RANDOMIZED_FAMILIES = [
    INCREMENTAL_VALID,
    RANDOM_INVALID,
    MUTATION_BASED_INVALID,
]

DEFAULT_FAMILIES = DETERMINISTIC_FAMILIES + RANDOMIZED_FAMILIES
DEFAULT_SIZES = [64, 128, 256, 512, 1024]
DEFAULT_RANDOMIZED_CASES = 5
DEFAULT_WARMUP_RUNS = 5
DEFAULT_MEASURED_RUNS = 20
DEFAULT_SEED = 20260723
DEFAULT_ALGORITHM_NAMES = [
    "python_sort",
    "sort_plus_laminarity_check",
    "simplified_jordan_reference",
]
PAPER_ALGORITHM_NAME = "simplified_jordan_paper_ordinary_list"
DEFAULT_RUNS_DIR = PROJECT_ROOT / "results" / "runs"
DEFAULT_RAW_CSV = PROJECT_ROOT / "results" / "week7_pilot_raw.csv"
DEFAULT_CASE_SUMMARY_CSV = PROJECT_ROOT / "results" / "week7_pilot_case_summary.csv"
DEFAULT_GROUP_SUMMARY_CSV = PROJECT_ROOT / "results" / "week7_pilot_group_summary.csv"
DEFAULT_ENVIRONMENT_JSON = PROJECT_ROOT / "results" / "week7_environment.json"
DEFAULT_AUTO_REPORT_MD = PROJECT_ROOT / "docs" / "analysis" / "week7_pilot_auto_report.md"

ALGORITHMS = {
    "python_sort": python_sort,
    "sort_plus_laminarity_check": sort_plus_laminarity_check,
    "simplified_jordan_reference": simplified_jordan_sort,
    PAPER_ALGORITHM_NAME: paper_jordan_sort_valid,
}

NO_DECISION = object()
PAPER_METRIC_FIELDS = [f"paper_{name}" for name in PAPER_METRIC_NAMES]

RAW_FIELDS = [
    "case_id",
    "family",
    "n",
    "seed",
    "case_execution_position",
    "oracle_valid",
    "oracle_reason",
    "category",
    "max_depth",
    "parented_interval_ratio",
    "containment_pair_density",
    "total_crossing_pair_count",
    "algorithm",
    "run_index",
    "measured_round",
    "algorithm_position",
    "time_ns",
    "sorted_correct",
    "output_correct",
    "validity_correct",
    "reason_correct",
    "overall_correct",
    "error",
    "laminar_pair_checks",
    "upper_pair_checks",
    "lower_pair_checks",
    "crossings_found",
    "interval_validation_checks",
    "containment_checks",
    "parent_candidate_checks",
    "nodes_created",
    "nodes_visited",
    "trace_event_count",
    *PAPER_METRIC_FIELDS,
]

SUMMARY_FIELDS = [
    "family",
    "n",
    "case_id",
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
    "category",
    "max_depth",
    "parented_interval_ratio",
    "containment_pair_density",
    "total_crossing_pair_count",
    "median_containment_checks",
    "median_laminar_pair_checks",
    "median_trace_event_count",
]

GROUP_FIELDS = [
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
    "avg_containment_pair_density",
    "avg_max_depth",
    "avg_total_crossing_pair_count",
    "median_containment_checks",
    "median_laminar_pair_checks",
]


@dataclass(frozen=True)
class PilotConfig:
    families: list[str]
    sizes: list[int]
    algorithms: list[str]
    randomized_cases: int
    warmup_runs: int
    measured_runs: int
    seed: int
    algorithm_order_seed: int
    case_order_seed: int
    run_id: str
    run_dir: Path
    raw_csv: Path
    case_summary_csv: Path
    group_summary_csv: Path
    environment_json: Path
    auto_report_md: Path
    config_json: Path
    manifest_json: Path


def csv_value(value):
    if value is None:
        return ""
    return value


def timestamp_run_id(prefix="week8_formal_prep"):
    """Return a UTC timestamp run id that is safe for filenames."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}"


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def repetitions_for_family(family, randomized_cases):
    if family in RANDOMIZED_FAMILIES:
        return randomized_cases
    return 1


def seed_for_case(family, n, index, base_seed):
    if family in RANDOMIZED_FAMILIES:
        return base_seed + n * 1000 + index
    return None


def _git_output(args):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def git_commit_sha():
    return _git_output(["rev-parse", "HEAD"])


def git_dirty():
    return bool(_git_output(["status", "--short"]))


def cpu_model():
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return platform.processor()
    return platform.processor()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_config(config):
    unknown_families = sorted(set(config.families) - set(DEFAULT_FAMILIES))
    if unknown_families:
        raise ValueError(f"unknown families: {unknown_families}")

    unknown_algorithms = sorted(set(config.algorithms) - set(ALGORITHMS))
    if unknown_algorithms:
        raise ValueError(f"unknown algorithms: {unknown_algorithms}")
    if PAPER_ALGORITHM_NAME in config.algorithms:
        invalid_families = sorted(set(config.families) - {
            FLAT_VALID,
            NESTED_VALID,
            INCREMENTAL_VALID,
        })
        if invalid_families:
            raise ValueError(
                "paper ordinary-list algorithm requires valid-only families: "
                f"{invalid_families}"
            )

    if len(config.families) != len(set(config.families)):
        raise ValueError("families must not contain duplicates")
    if len(config.algorithms) != len(set(config.algorithms)):
        raise ValueError("algorithms must not contain duplicates")
    if not config.families:
        raise ValueError("at least one family is required")
    if not config.sizes:
        raise ValueError("at least one size is required")
    if any(n <= 0 for n in config.sizes):
        raise ValueError("sizes must be positive")
    if config.randomized_cases < 1:
        raise ValueError("randomized_cases must be positive")
    if config.warmup_runs < 0:
        raise ValueError("warmup_runs must be non-negative")
    if config.measured_runs < 1:
        raise ValueError("measured_runs must be positive")

    output_paths = [
        config.raw_csv,
        config.case_summary_csv,
        config.group_summary_csv,
        config.environment_json,
        config.auto_report_md,
        config.config_json,
        config.manifest_json,
    ]
    if len({path.resolve() for path in output_paths}) != len(output_paths):
        raise ValueError("output paths must be distinct")
    return config


def validate_no_overwrite(config, overwrite=False):
    """Reject existing output files unless overwrite is explicit."""
    if overwrite:
        return config

    output_paths = [
        config.raw_csv,
        config.case_summary_csv,
        config.group_summary_csv,
        config.environment_json,
        config.auto_report_md,
        config.config_json,
        config.manifest_json,
    ]
    existing = [path for path in output_paths if Path(path).exists()]
    if existing:
        raise ValueError(f"output files already exist: {[str(path) for path in existing]}")
    return config


def build_cases(config):
    cases = []
    for family in config.families:
        repetitions = repetitions_for_family(family, config.randomized_cases)
        for n in config.sizes:
            for index in range(1, repetitions + 1):
                case_seed = seed_for_case(family, n, index, config.seed)
                sequence = generate_sequence(family, n, seed=case_seed)
                oracle_result = oracle(sequence)
                profile = structure_profile(sequence, oracle_result=oracle_result)
                diagnostics = instrumented_reference_run(sequence)["metrics"]
                paper_diagnostics = {}
                if PAPER_ALGORITHM_NAME in config.algorithms:
                    paper_result = paper_jordan_diagnostics_valid(sequence)
                    if (
                        not paper_result["invariants_valid"]
                        or paper_result["output"] != oracle_result["sorted"]
                    ):
                        raise RuntimeError(
                            f"paper diagnostics failed for {family}, n={n}, "
                            f"seed={case_seed}"
                        )
                    paper_diagnostics = {
                        f"paper_{name}": paper_result["metrics"][name]
                        for name in PAPER_METRIC_NAMES
                    }
                cases.append(
                    {
                        "case_id": make_case_id(family, len(sequence), index),
                        "case_index": len(cases),
                        "family": family,
                        "n": len(sequence),
                        "seed": case_seed,
                        "sequence": sequence,
                        "oracle": oracle_result,
                        "profile": profile,
                        "diagnostics": diagnostics,
                        "paper_diagnostics": paper_diagnostics,
                    }
                )
    return cases


def _extract_sorted_output(algorithm_name, result):
    if algorithm_name in {"python_sort", PAPER_ALGORITHM_NAME}:
        return result
    if algorithm_name == "sort_plus_laminarity_check":
        return result["sorted"]
    if algorithm_name == "simplified_jordan_reference":
        return result["sorted"]
    raise ValueError(f"unknown algorithm: {algorithm_name}")


def _extract_validity_result(algorithm_name, result):
    if algorithm_name in {"sort_plus_laminarity_check", "simplified_jordan_reference"}:
        return result["valid"], result["reason"]
    return NO_DECISION, NO_DECISION


def _time_once(func, sequence):
    values = list(sequence)
    was_enabled = gc.isenabled()
    if was_enabled:
        gc.disable()
    try:
        start = time.perf_counter_ns()
        result = func(values)
        end = time.perf_counter_ns()
    finally:
        if was_enabled:
            gc.enable()
    return result, end - start


def run_timed_algorithm(
    algorithm_name,
    sequence,
    oracle_result,
    run_index,
    algorithm_position="",
):
    func = ALGORITHMS[algorithm_name]
    try:
        result, time_ns = _time_once(func, sequence)
        sorted_output = _extract_sorted_output(algorithm_name, result)
        validity_result, reason_result = _extract_validity_result(
            algorithm_name,
            result,
        )
        output_correct = sorted_output == oracle_result["sorted"]
        validity_correct = (
            ""
            if validity_result is NO_DECISION
            else validity_result == oracle_result["valid"]
        )
        reason_correct = (
            ""
            if reason_result is NO_DECISION
            else reason_result == oracle_result["reason"]
        )
        overall_correct = output_correct and (
            validity_correct in {"", True}
        ) and (reason_correct in {"", True})
        return {
            "run_index": run_index,
            "measured_round": run_index,
            "algorithm_position": algorithm_position,
            "time_ns": time_ns,
            "sorted_correct": output_correct,
            "output_correct": output_correct,
            "validity_correct": validity_correct,
            "reason_correct": reason_correct,
            "overall_correct": overall_correct,
            "error": "",
        }
    except Exception as exc:
        return {
            "run_index": run_index,
            "measured_round": run_index,
            "algorithm_position": algorithm_position,
            "time_ns": "",
            "sorted_correct": False,
            "output_correct": False,
            "validity_correct": False,
            "reason_correct": False,
            "overall_correct": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _metadata_fields(case, algorithm_name):
    profile = case["profile"]
    oracle_result = case["oracle"]
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "n": case["n"],
        "seed": csv_value(case["seed"]),
        "case_execution_position": case["case_execution_position"],
        "oracle_valid": oracle_result["valid"],
        "oracle_reason": csv_value(oracle_result["reason"]),
        "category": profile["category"],
        "max_depth": csv_value(profile["max_depth"]),
        "parented_interval_ratio": csv_value(profile["parented_interval_ratio"]),
        "containment_pair_density": csv_value(profile["containment_pair_density"]),
        "total_crossing_pair_count": csv_value(profile["total_crossing_pair_count"]),
        "algorithm": algorithm_name,
    }


def algorithm_order_for_round(algorithms, seed, case_index, measured_round):
    """Return a balanced per-round algorithm order for one case."""
    ordered = list(algorithms)
    random.Random(seed + case_index * 1009).shuffle(ordered)
    if not ordered:
        return ordered
    shift = (measured_round - 1) % len(ordered)
    return ordered[shift:] + ordered[:shift]


def make_raw_rows(config):
    rows = []
    cases = build_cases(config)
    random.Random(config.case_order_seed).shuffle(cases)
    for position, case in enumerate(cases, start=1):
        case["case_execution_position"] = position

    for case in cases:
        warmup_order = algorithm_order_for_round(
            config.algorithms,
            config.algorithm_order_seed,
            case["case_index"],
            measured_round=1,
        )
        for algorithm_name in warmup_order:
            for _ in range(config.warmup_runs):
                run_timed_algorithm(
                    algorithm_name,
                    case["sequence"],
                    case["oracle"],
                    run_index=0,
                )

        for run_index in range(1, config.measured_runs + 1):
            round_order = algorithm_order_for_round(
                config.algorithms,
                config.algorithm_order_seed,
                case["case_index"],
                measured_round=run_index,
            )
            for algorithm_position, algorithm_name in enumerate(round_order, start=1):
                row = {
                    **_metadata_fields(case, algorithm_name),
                    **run_timed_algorithm(
                        algorithm_name,
                        case["sequence"],
                        case["oracle"],
                        run_index=run_index,
                        algorithm_position=algorithm_position,
                    ),
                }
                if algorithm_name == "simplified_jordan_reference":
                    row.update(case["diagnostics"])
                if algorithm_name == PAPER_ALGORITHM_NAME:
                    row.update(case["paper_diagnostics"])
                rows.append({field: csv_value(row.get(field)) for field in RAW_FIELDS})
    return rows


def _median(values):
    return statistics.median(values) if values else ""


def _quartiles(values):
    if not values:
        return "", "", ""
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) == 1:
        return sorted_values[0], sorted_values[0], 0
    if len(sorted_values) % 2 == 0:
        lower = sorted_values[:midpoint]
        upper = sorted_values[midpoint:]
    else:
        lower = sorted_values[:midpoint]
        upper = sorted_values[midpoint + 1 :]
    q1 = statistics.median(lower) if lower else sorted_values[0]
    q3 = statistics.median(upper) if upper else sorted_values[-1]
    return q1, q3, q3 - q1


def _numeric(row, field):
    value = row.get(field)
    if value in {"", None}:
        return None
    return float(value)


def summarize_by_case(raw_rows):
    grouped = {}
    for row in raw_rows:
        grouped.setdefault((row["case_id"], row["algorithm"]), []).append(row)

    summaries = []
    for (case_id, algorithm), rows in sorted(grouped.items()):
        times = [int(row["time_ns"]) for row in rows if row["time_ns"] != ""]
        q1, q3, iqr = _quartiles(times)
        first = rows[0]
        error_count = sum(1 for row in rows if row["error"])
        metric_fields = {
            "median_containment_checks": _median(
                [
                    _numeric(row, "containment_checks")
                    for row in rows
                    if _numeric(row, "containment_checks") is not None
                ]
            ),
            "median_laminar_pair_checks": _median(
                [
                    _numeric(row, "laminar_pair_checks")
                    for row in rows
                    if _numeric(row, "laminar_pair_checks") is not None
                ]
            ),
            "median_trace_event_count": _median(
                [
                    _numeric(row, "trace_event_count")
                    for row in rows
                    if _numeric(row, "trace_event_count") is not None
                ]
            ),
        }
        summaries.append(
            {
                "family": first["family"],
                "n": first["n"],
                "case_id": case_id,
                "algorithm": algorithm,
                "measured_run_count": len(times),
                "median_time_ns": _median(times),
                "q1_time_ns": q1,
                "q3_time_ns": q3,
                "iqr_time_ns": iqr,
                "mean_time_ns": statistics.mean(times) if times else "",
                "stdev_time_ns": statistics.stdev(times) if len(times) > 1 else 0,
                "all_correct": all(_as_bool(row["overall_correct"]) for row in rows),
                "error_count": error_count,
                "category": first["category"],
                "max_depth": first["max_depth"],
                "parented_interval_ratio": first["parented_interval_ratio"],
                "containment_pair_density": first["containment_pair_density"],
                "total_crossing_pair_count": first["total_crossing_pair_count"],
                **metric_fields,
            }
        )
    return summaries


def summarize_by_group(case_rows):
    grouped = {}
    for row in case_rows:
        grouped.setdefault((row["family"], row["n"], row["algorithm"]), []).append(row)

    summaries = []
    for (family, n, algorithm), rows in sorted(grouped.items()):
        case_medians = [
            float(row["median_time_ns"])
            for row in rows
            if row["median_time_ns"] not in {"", None}
        ]
        q1, q3, iqr = _quartiles(case_medians)

        def avg(field):
            values = [_numeric(row, field) for row in rows if _numeric(row, field) is not None]
            return statistics.mean(values) if values else ""

        def med(field):
            values = [_numeric(row, field) for row in rows if _numeric(row, field) is not None]
            return _median(values)

        summaries.append(
            {
                "family": family,
                "n": n,
                "algorithm": algorithm,
                "case_count": len(rows),
                "median_case_time_ns": _median(case_medians),
                "q1_case_time_ns": q1,
                "q3_case_time_ns": q3,
                "iqr_case_time_ns": iqr,
                "mean_case_time_ns": statistics.mean(case_medians)
                if case_medians
                else "",
                "all_cases_correct": all(_as_bool(row["all_correct"]) for row in rows),
                "total_error_count": sum(int(row["error_count"]) for row in rows),
                "avg_containment_pair_density": avg("containment_pair_density"),
                "avg_max_depth": avg("max_depth"),
                "avg_total_crossing_pair_count": avg("total_crossing_pair_count"),
                "median_containment_checks": med("median_containment_checks"),
                "median_laminar_pair_checks": med("median_laminar_pair_checks"),
            }
        )
    return summaries


def write_csv(rows, output_csv, fields):
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


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
        "perf_counter_resolution": time.get_clock_info("perf_counter").resolution,
        "gc_initial_state": gc.isenabled(),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "config": {
            "families": config.families,
            "sizes": config.sizes,
            "algorithms": config.algorithms,
            "randomized_cases": config.randomized_cases,
            "warmup_runs": config.warmup_runs,
            "measured_runs": config.measured_runs,
            "seed": config.seed,
            "algorithm_order_seed": config.algorithm_order_seed,
            "case_order_seed": config.case_order_seed,
        },
    }
    config.environment_json.parent.mkdir(parents=True, exist_ok=True)
    config.environment_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def config_to_dict(config):
    return {
        "run_id": config.run_id,
        "families": config.families,
        "sizes": config.sizes,
        "algorithms": config.algorithms,
        "randomized_cases": config.randomized_cases,
        "warmup_runs": config.warmup_runs,
        "measured_runs": config.measured_runs,
        "seed": config.seed,
        "algorithm_order_seed": config.algorithm_order_seed,
        "case_order_seed": config.case_order_seed,
        "outputs": {
            "run_dir": str(config.run_dir),
            "raw_csv": str(config.raw_csv),
            "case_summary_csv": str(config.case_summary_csv),
            "group_summary_csv": str(config.group_summary_csv),
            "environment_json": str(config.environment_json),
            "auto_report_md": str(config.auto_report_md),
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


def write_manifest(config, raw_rows, case_rows, group_rows):
    files = {
        "raw_csv": config.raw_csv,
        "case_summary_csv": config.case_summary_csv,
        "group_summary_csv": config.group_summary_csv,
        "environment_json": config.environment_json,
        "config_json": config.config_json,
        "auto_report_md": config.auto_report_md,
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
            name: {
                "path": str(path),
                "sha256": file_sha256(path),
            }
            for name, path in files.items()
            if Path(path).exists()
        },
    }
    config.manifest_json.parent.mkdir(parents=True, exist_ok=True)
    config.manifest_json.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def write_auto_report(config, group_rows):
    config.auto_report_md.parent.mkdir(parents=True, exist_ok=True)
    algorithms = ", ".join(sorted({row["algorithm"] for row in group_rows}))
    families = ", ".join(config.families)
    config.auto_report_md.write_text(
        "\n".join(
            [
                "# Benchmark Auto Report",
                "",
                "This pilot is a controlled engineering observation, not a final performance claim.",
                "",
                "## Configuration",
                "",
                f"- Run id: {config.run_id}",
                f"- Families: {families}",
                f"- Sizes: {config.sizes}",
                f"- Algorithms: {algorithms}",
                f"- Warm-up runs: {config.warmup_runs}",
                f"- Measured runs: {config.measured_runs}",
                "",
                "## Initial Observations",
                "",
                "- The pilot records correctness, timing, structural metrics, and selected operation counters together.",
                "- The pilot suggests that future analysis should compare runtime against containment density and max depth at the case-summary level.",
                "- The pilot times configured plain algorithm entry points; complete diagnostics are collected once per case outside the timed region.",
                "- Paper ordinary-list timing still includes trace recording and correctness-first backend commit validation.",
                "",
                "## Boundaries",
                "",
                "- This pilot does not prove linear complexity.",
                "- This pilot is not representative of all Jordan sequences.",
                "- This pilot does not implement level-linked search trees or heterogeneous finger trees.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_pilot(config):
    validate_config(config)
    raw_rows = make_raw_rows(config)
    case_rows = summarize_by_case(raw_rows)
    group_rows = summarize_by_group(case_rows)

    write_config(config)
    write_csv(raw_rows, config.raw_csv, RAW_FIELDS)
    write_csv(case_rows, config.case_summary_csv, SUMMARY_FIELDS)
    write_csv(group_rows, config.group_summary_csv, GROUP_FIELDS)
    write_environment(config)
    write_auto_report(config, group_rows)
    write_manifest(config, raw_rows, case_rows, group_rows)

    return raw_rows, case_rows, group_rows


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--families", nargs="*", default=DEFAULT_FAMILIES)
    parser.add_argument("--sizes", nargs="*", type=int, default=DEFAULT_SIZES)
    parser.add_argument("--algorithms", nargs="*", default=DEFAULT_ALGORITHM_NAMES)
    parser.add_argument(
        "--randomized-cases", type=int, default=DEFAULT_RANDOMIZED_CASES
    )
    parser.add_argument("--warmup-runs", type=int, default=DEFAULT_WARMUP_RUNS)
    parser.add_argument("--measured-runs", type=int, default=DEFAULT_MEASURED_RUNS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--algorithm-order-seed", type=int, default=None)
    parser.add_argument("--case-order-seed", type=int, default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--raw-csv", type=Path, default=None)
    parser.add_argument(
        "--case-summary-csv", type=Path, default=None
    )
    parser.add_argument(
        "--group-summary-csv", type=Path, default=None
    )
    parser.add_argument(
        "--environment-json", type=Path, default=None
    )
    parser.add_argument(
        "--auto-report-md", type=Path, default=None
    )
    return parser.parse_args()


def build_config_from_args(args):
    run_id = args.run_id or timestamp_run_id()
    run_dir = args.run_dir or (DEFAULT_RUNS_DIR / run_id)

    explicit_paths = [
        args.raw_csv,
        args.case_summary_csv,
        args.group_summary_csv,
        args.environment_json,
        args.auto_report_md,
    ]
    config = PilotConfig(
        families=args.families,
        sizes=args.sizes,
        algorithms=args.algorithms,
        randomized_cases=args.randomized_cases,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        seed=args.seed,
        algorithm_order_seed=(
            args.algorithm_order_seed
            if args.algorithm_order_seed is not None
            else args.seed + 7919
        ),
        case_order_seed=(
            args.case_order_seed
            if args.case_order_seed is not None
            else args.seed + 1543
        ),
        run_id=run_id,
        run_dir=run_dir,
        raw_csv=args.raw_csv or (run_dir / "raw.csv"),
        case_summary_csv=args.case_summary_csv or (run_dir / "case_summary.csv"),
        group_summary_csv=args.group_summary_csv or (run_dir / "group_summary.csv"),
        environment_json=args.environment_json or (run_dir / "environment.json"),
        auto_report_md=args.auto_report_md or (run_dir / "auto_report.md"),
        config_json=run_dir / "config.json",
        manifest_json=run_dir / "manifest.json",
    )
    validate_config(config)
    validate_no_overwrite(config, overwrite=args.overwrite)
    return config


def main():
    args = parse_args()
    config = build_config_from_args(args)
    raw_rows, case_rows, group_rows = run_pilot(config)
    print(
        "wrote "
        f"{len(raw_rows)} raw rows, {len(case_rows)} case rows, "
        f"{len(group_rows)} group rows"
    )


if __name__ == "__main__":
    main()
