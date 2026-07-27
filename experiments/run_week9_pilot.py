"""Run the separate Week 9 sorting and recognition integration pilots."""

import argparse
from pathlib import Path

from run_week7_pilot import (
    DEFAULT_RUNS_DIR,
    FLAT_VALID,
    INCREMENTAL_VALID,
    INVALID_LOWER_CROSSING,
    INVALID_UPPER_CROSSING,
    MUTATION_BASED_INVALID,
    NESTED_VALID,
    PAPER_ALGORITHM_NAME,
    RANDOM_INVALID,
    PilotConfig,
    run_pilot,
    timestamp_run_id,
    validate_config,
    validate_no_overwrite,
)


WEEK9_SIZES = [8, 16, 32]
WEEK9_RANDOMIZED_CASES = 2
WEEK9_WARMUP_RUNS = 1
WEEK9_MEASURED_RUNS = 3
WEEK9_SEED = 20260727

SORTING_FAMILIES = [
    FLAT_VALID,
    NESTED_VALID,
    INCREMENTAL_VALID,
]
SORTING_ALGORITHMS = [
    "python_sort",
    "simplified_jordan_reference",
    PAPER_ALGORITHM_NAME,
]

RECOGNITION_FAMILIES = [
    FLAT_VALID,
    NESTED_VALID,
    INCREMENTAL_VALID,
    INVALID_UPPER_CROSSING,
    INVALID_LOWER_CROSSING,
    RANDOM_INVALID,
    MUTATION_BASED_INVALID,
]
RECOGNITION_ALGORITHMS = [
    "sort_plus_laminarity_check",
    "simplified_jordan_reference",
]


def build_week9_configs(run_id, run_dir, mode="both"):
    """Build frozen, isolated configs for the requested Week 9 pilot mode."""
    if mode not in {"sorting", "recognition", "both"}:
        raise ValueError("mode must be 'sorting', 'recognition', or 'both'")

    root = Path(run_dir)
    configs = {}
    if mode in {"sorting", "both"}:
        configs["sorting"] = _pilot_config(
            run_id=f"{run_id}_sorting",
            run_dir=root / "sorting",
            families=SORTING_FAMILIES,
            algorithms=SORTING_ALGORITHMS,
        )
    if mode in {"recognition", "both"}:
        configs["recognition"] = _pilot_config(
            run_id=f"{run_id}_recognition",
            run_dir=root / "recognition",
            families=RECOGNITION_FAMILIES,
            algorithms=RECOGNITION_ALGORITHMS,
        )
    return configs


def _pilot_config(run_id, run_dir, families, algorithms):
    run_dir = Path(run_dir)
    return PilotConfig(
        families=list(families),
        sizes=list(WEEK9_SIZES),
        algorithms=list(algorithms),
        randomized_cases=WEEK9_RANDOMIZED_CASES,
        warmup_runs=WEEK9_WARMUP_RUNS,
        measured_runs=WEEK9_MEASURED_RUNS,
        seed=WEEK9_SEED,
        algorithm_order_seed=WEEK9_SEED + 7919,
        case_order_seed=WEEK9_SEED + 1543,
        run_id=run_id,
        run_dir=run_dir,
        raw_csv=run_dir / "raw.csv",
        case_summary_csv=run_dir / "case_summary.csv",
        group_summary_csv=run_dir / "group_summary.csv",
        environment_json=run_dir / "environment.json",
        auto_report_md=run_dir / "auto_report.md",
        config_json=run_dir / "config.json",
        manifest_json=run_dir / "manifest.json",
    )


def run_week9_pilots(configs, overwrite=False):
    """Validate all outputs first, then run each requested isolated pilot."""
    if not configs:
        raise ValueError("at least one Week 9 pilot config is required")
    for config in configs.values():
        validate_config(config)
        validate_no_overwrite(config, overwrite=overwrite)

    results = {}
    for name, config in configs.items():
        raw_rows, case_rows, group_rows = run_pilot(config)
        results[name] = {
            "raw_rows": raw_rows,
            "case_rows": case_rows,
            "group_rows": group_rows,
        }
    return results


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["sorting", "recognition", "both"],
        default="both",
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_id = args.run_id or timestamp_run_id("week9_pilot")
    run_dir = args.run_dir or (DEFAULT_RUNS_DIR / run_id)
    configs = build_week9_configs(run_id, run_dir, mode=args.mode)
    results = run_week9_pilots(configs, overwrite=args.overwrite)

    for name, result in results.items():
        print(
            f"{name}: {len(result['raw_rows'])} raw rows, "
            f"{len(result['case_rows'])} case rows, "
            f"{len(result['group_rows'])} group rows"
        )


if __name__ == "__main__":
    main()
