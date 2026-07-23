"""Run the Week 7 pilot benchmark with case-level aggregation."""

import argparse
import csv
import gc
import json
import platform
import random
import statistics
import sys
import time
from dataclasses import dataclass
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
DEFAULT_RAW_CSV = PROJECT_ROOT / "results" / "week7_pilot_raw.csv"
DEFAULT_CASE_SUMMARY_CSV = PROJECT_ROOT / "results" / "week7_pilot_case_summary.csv"
DEFAULT_GROUP_SUMMARY_CSV = PROJECT_ROOT / "results" / "week7_pilot_group_summary.csv"
DEFAULT_ENVIRONMENT_JSON = PROJECT_ROOT / "results" / "week7_environment.json"
DEFAULT_INTERPRETATION_MD = (
    PROJECT_ROOT / "docs" / "analysis" / "week7_pilot_interpretation.md"
)

ALGORITHMS = {
    "python_sort": python_sort,
    "sort_plus_laminarity_check": sort_plus_laminarity_check,
    "simplified_jordan_reference": instrumented_reference_run,
}

RAW_FIELDS = [
    "case_id",
    "family",
    "n",
    "seed",
    "oracle_valid",
    "oracle_reason",
    "category",
    "max_depth",
    "parented_interval_ratio",
    "containment_pair_density",
    "total_crossing_pair_count",
    "algorithm",
    "run_index",
    "time_ns",
    "sorted_correct",
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
    randomized_cases: int
    warmup_runs: int
    measured_runs: int
    seed: int
    raw_csv: Path
    case_summary_csv: Path
    group_summary_csv: Path
    environment_json: Path
    interpretation_md: Path


def csv_value(value):
    if value is None:
        return ""
    return value


def repetitions_for_family(family, randomized_cases):
    if family in RANDOMIZED_FAMILIES:
        return randomized_cases
    return 1


def seed_for_case(family, n, index, base_seed):
    if family in RANDOMIZED_FAMILIES:
        return base_seed + n * 1000 + index
    return None


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
                cases.append(
                    {
                        "case_id": make_case_id(family, len(sequence), index),
                        "family": family,
                        "n": len(sequence),
                        "seed": case_seed,
                        "sequence": sequence,
                        "oracle": oracle_result,
                        "profile": profile,
                    }
                )
    return cases


def _extract_sorted_output(algorithm_name, result):
    if algorithm_name == "python_sort":
        return result
    if algorithm_name == "sort_plus_laminarity_check":
        return result["sorted"]
    if algorithm_name == "simplified_jordan_reference":
        return result["result"]["sorted"]
    raise ValueError(f"unknown algorithm: {algorithm_name}")


def _extract_metrics(algorithm_name, result):
    if algorithm_name == "simplified_jordan_reference":
        return result["metrics"]
    return {}


def _time_once(func, sequence):
    was_enabled = gc.isenabled()
    if was_enabled:
        gc.disable()
    try:
        start = time.perf_counter_ns()
        result = func(list(sequence))
        end = time.perf_counter_ns()
    finally:
        if was_enabled:
            gc.enable()
    return result, end - start


def run_timed_algorithm(algorithm_name, sequence, oracle_sorted, run_index):
    func = ALGORITHMS[algorithm_name]
    try:
        result, time_ns = _time_once(func, sequence)
        sorted_output = _extract_sorted_output(algorithm_name, result)
        metrics = _extract_metrics(algorithm_name, result)
        return {
            "run_index": run_index,
            "time_ns": time_ns,
            "sorted_correct": sorted_output == oracle_sorted,
            "error": "",
            **metrics,
        }
    except Exception as exc:
        return {
            "run_index": run_index,
            "time_ns": "",
            "sorted_correct": False,
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
        "oracle_valid": oracle_result["valid"],
        "oracle_reason": csv_value(oracle_result["reason"]),
        "category": profile["category"],
        "max_depth": csv_value(profile["max_depth"]),
        "parented_interval_ratio": csv_value(profile["parented_interval_ratio"]),
        "containment_pair_density": csv_value(profile["containment_pair_density"]),
        "total_crossing_pair_count": csv_value(profile["total_crossing_pair_count"]),
        "algorithm": algorithm_name,
    }


def make_raw_rows(config):
    rng = random.Random(config.seed)
    rows = []
    cases = build_cases(config)

    for case in cases:
        algorithms = list(ALGORITHMS)
        rng.shuffle(algorithms)
        for algorithm_name in algorithms:
            for _ in range(config.warmup_runs):
                run_timed_algorithm(
                    algorithm_name,
                    case["sequence"],
                    case["oracle"]["sorted"],
                    run_index=0,
                )

            for run_index in range(1, config.measured_runs + 1):
                row = {
                    **_metadata_fields(case, algorithm_name),
                    **run_timed_algorithm(
                        algorithm_name,
                        case["sequence"],
                        case["oracle"]["sorted"],
                        run_index=run_index,
                    ),
                }
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
                "all_correct": all(row["sorted_correct"] == "True" for row in rows),
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
        case_medians = [float(row["median_time_ns"]) for row in rows]
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
                "mean_case_time_ns": statistics.mean(case_medians),
                "all_cases_correct": all(row["all_correct"] is True for row in rows),
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
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "config": {
            "families": config.families,
            "sizes": config.sizes,
            "randomized_cases": config.randomized_cases,
            "warmup_runs": config.warmup_runs,
            "measured_runs": config.measured_runs,
            "seed": config.seed,
            "algorithms": list(ALGORITHMS),
        },
    }
    config.environment_json.parent.mkdir(parents=True, exist_ok=True)
    config.environment_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_interpretation(config, group_rows):
    config.interpretation_md.parent.mkdir(parents=True, exist_ok=True)
    algorithms = ", ".join(sorted({row["algorithm"] for row in group_rows}))
    families = ", ".join(config.families)
    config.interpretation_md.write_text(
        "\n".join(
            [
                "# Week 7 Pilot Interpretation",
                "",
                "This pilot is a controlled engineering observation, not a final performance claim.",
                "",
                "## Configuration",
                "",
                f"- Families: {families}",
                f"- Sizes: {config.sizes}",
                f"- Algorithms: {algorithms}",
                f"- Warm-up runs: {config.warmup_runs}",
                f"- Measured runs: {config.measured_runs}",
                "",
                "## Initial Observations",
                "",
                "- The pilot records correctness, timing, structural metrics, and operation counters together.",
                "- The pilot suggests that future analysis should compare runtime against containment density and max depth at the case-summary level.",
                "- The pilot keeps `simplified_jordan_reference` as a reference pipeline using oracle-sorted output.",
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
    raw_rows = make_raw_rows(config)
    case_rows = summarize_by_case(raw_rows)
    group_rows = summarize_by_group(case_rows)

    write_csv(raw_rows, config.raw_csv, RAW_FIELDS)
    write_csv(case_rows, config.case_summary_csv, SUMMARY_FIELDS)
    write_csv(group_rows, config.group_summary_csv, GROUP_FIELDS)
    write_environment(config)
    write_interpretation(config, group_rows)

    return raw_rows, case_rows, group_rows


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--families", nargs="*", default=DEFAULT_FAMILIES)
    parser.add_argument("--sizes", nargs="*", type=int, default=DEFAULT_SIZES)
    parser.add_argument(
        "--randomized-cases", type=int, default=DEFAULT_RANDOMIZED_CASES
    )
    parser.add_argument("--warmup-runs", type=int, default=DEFAULT_WARMUP_RUNS)
    parser.add_argument("--measured-runs", type=int, default=DEFAULT_MEASURED_RUNS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--raw-csv", type=Path, default=DEFAULT_RAW_CSV)
    parser.add_argument(
        "--case-summary-csv", type=Path, default=DEFAULT_CASE_SUMMARY_CSV
    )
    parser.add_argument(
        "--group-summary-csv", type=Path, default=DEFAULT_GROUP_SUMMARY_CSV
    )
    parser.add_argument(
        "--environment-json", type=Path, default=DEFAULT_ENVIRONMENT_JSON
    )
    parser.add_argument(
        "--interpretation-md", type=Path, default=DEFAULT_INTERPRETATION_MD
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = PilotConfig(
        families=args.families,
        sizes=args.sizes,
        randomized_cases=args.randomized_cases,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        seed=args.seed,
        raw_csv=args.raw_csv,
        case_summary_csv=args.case_summary_csv,
        group_summary_csv=args.group_summary_csv,
        environment_json=args.environment_json,
        interpretation_md=args.interpretation_md,
    )
    raw_rows, case_rows, group_rows = run_pilot(config)
    print(
        "wrote "
        f"{len(raw_rows)} raw rows, {len(case_rows)} case rows, "
        f"{len(group_rows)} group rows"
    )


if __name__ == "__main__":
    main()

