"""运行 Week 1 的小规模 baseline 实验。"""

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from baselines import (  # noqa: E402
    merge_sort,
    python_sort,
    quick_sort,
    sort_plus_laminarity_check,
    time_function,
)
from generators import (  # noqa: E402
    FLAT_VALID,
    INCREMENTAL_VALID,
    INVALID_LOWER_CROSSING,
    INVALID_UPPER_CROSSING,
    MUTATION_BASED_INVALID,
    NESTED_VALID,
    RANDOM_INVALID,
    generate_dataset,
    load_test_case,
)


CSV_FIELDS = [
    "case_id",
    "family",
    "n",
    "seed",
    "oracle_valid",
    "oracle_reason",
    "distinct_values",
    "upper_ok",
    "lower_ok",
    "algorithm",
    "run_index",
    "time_ns",
    "sorted_correct",
    "error",
]


ALGORITHMS = {
    "python_sort": python_sort,
    "merge_sort": merge_sort,
    "quick_sort": quick_sort,
    "sort_plus_laminarity_check": sort_plus_laminarity_check,
}


VALID_FAMILIES = {
    FLAT_VALID,
    NESTED_VALID,
    INCREMENTAL_VALID,
}


INVALID_FAMILIES = {
    INVALID_UPPER_CROSSING,
    INVALID_LOWER_CROSSING,
    RANDOM_INVALID,
    MUTATION_BASED_INVALID,
}


@dataclass(frozen=True)
class ExperimentConfig:
    """保存一次实验运行需要的配置。"""

    name: str
    sizes: list[int]
    families: list[str]
    algorithms: list[str]
    cases_per_size: int
    timing_runs: int
    cases_dir: Path
    output_csv: Path
    seed: int = 20260610


SMOKE_CONFIG = ExperimentConfig(
    name="smoke",
    sizes=[8],
    families=[FLAT_VALID],
    algorithms=["python_sort"],
    cases_per_size=1,
    timing_runs=1,
    cases_dir=PROJECT_ROOT / "results" / "week1_smoke_cases",
    output_csv=PROJECT_ROOT / "results" / "week1_baseline_smoke_results.csv",
)


FULL_CONFIG = ExperimentConfig(
    name="full",
    sizes=[8, 16, 32, 64, 128, 256, 512],
    families=[
        FLAT_VALID,
        NESTED_VALID,
        INCREMENTAL_VALID,
        INVALID_UPPER_CROSSING,
        INVALID_LOWER_CROSSING,
        RANDOM_INVALID,
        MUTATION_BASED_INVALID,
    ],
    algorithms=[
        "python_sort",
        "merge_sort",
        "quick_sort",
        "sort_plus_laminarity_check",
    ],
    cases_per_size=3,
    timing_runs=5,
    cases_dir=PROJECT_ROOT / "results" / "week1_baseline_cases",
    output_csv=PROJECT_ROOT / "results" / "week1_baseline_results.csv",
)


def csv_value(value):
    """把 Python 值转换成更适合 CSV 的简单值。"""
    if value is None:
        return ""
    return value


def generate_case_paths(config):
    """用已有 JSON pipeline 生成实验 case，并返回所有 case 文件路径。"""
    paths = []
    for family in config.families:
        paths.extend(
            generate_dataset(
                family=family,
                sizes=config.sizes,
                repetitions=config.cases_per_size,
                output_dir=config.cases_dir,
                seed=config.seed,
            )
        )
    return paths


def extract_sorted_output(algorithm_name, result):
    """从不同 baseline 的返回值中取出排序结果。"""
    if algorithm_name == "sort_plus_laminarity_check":
        return result["sorted"]
    return result


def run_algorithm_once(algorithm_name, sequence, oracle_sorted):
    """运行一次 baseline，并返回 timing、correctness 和 error 信息。"""
    try:
        timed = time_function(ALGORITHMS[algorithm_name], sequence)
        sorted_output = extract_sorted_output(algorithm_name, timed["result"])
        return {
            "time_ns": timed["time_ns"],
            "sorted_correct": sorted_output == oracle_sorted,
            "error": "",
        }
    except Exception as exc:
        return {
            "time_ns": "",
            "sorted_correct": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def make_result_rows(config):
    """生成 case、运行 baseline，并返回 raw CSV rows。"""
    rows = []
    case_paths = generate_case_paths(config)

    for case_path in case_paths:
        case = load_test_case(case_path)
        oracle_result = case["oracle"]
        sequence = case["sequence"]
        oracle_sorted = oracle_result["sorted"]

        for algorithm_name in config.algorithms:
            for run_index in range(1, config.timing_runs + 1):
                run_result = run_algorithm_once(
                    algorithm_name=algorithm_name,
                    sequence=sequence,
                    oracle_sorted=oracle_sorted,
                )

                rows.append(
                    {
                        "case_id": case["id"],
                        "family": case["family"],
                        "n": case["n"],
                        "seed": csv_value(case["seed"]),
                        "oracle_valid": oracle_result["valid"],
                        "oracle_reason": csv_value(oracle_result["reason"]),
                        "distinct_values": oracle_result["distinct_values"],
                        "upper_ok": csv_value(oracle_result["upper_ok"]),
                        "lower_ok": csv_value(oracle_result["lower_ok"]),
                        "algorithm": algorithm_name,
                        "run_index": run_index,
                        "time_ns": run_result["time_ns"],
                        "sorted_correct": run_result["sorted_correct"],
                        "error": run_result["error"],
                    }
                )

    return rows


def write_csv(rows, output_csv):
    """把实验结果写入 CSV。"""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def validate_rows(rows):
    """检查实验结果是否满足 Week 1 Day 6 完成条件。"""
    failed_rows = [
        row
        for row in rows
        if row["error"] != "" or row["sorted_correct"] is not True
    ]
    if failed_rows:
        raise RuntimeError(
            f"{len(failed_rows)} baseline runs failed; inspect the CSV output"
        )

    invalid_family_rows = [
        row
        for row in rows
        if row["family"] in INVALID_FAMILIES and row["oracle_valid"] is not False
    ]
    if invalid_family_rows:
        raise RuntimeError(
            f"{len(invalid_family_rows)} invalid-family rows were not oracle-invalid"
        )

    valid_family_rows = [
        row
        for row in rows
        if row["family"] in VALID_FAMILIES and row["oracle_valid"] is not True
    ]
    if valid_family_rows:
        raise RuntimeError(
            f"{len(valid_family_rows)} valid-family rows were not oracle-valid"
        )


def expected_row_count(config):
    """返回当前配置应该产生的 raw timing 行数。"""
    return (
        len(config.families)
        * len(config.sizes)
        * config.cases_per_size
        * len(config.algorithms)
        * config.timing_runs
    )


def run_experiment(config):
    """运行一次实验配置，写 CSV，并返回所有结果行。"""
    rows = make_result_rows(config)
    write_csv(rows, config.output_csv)
    validate_rows(rows)

    expected_rows = expected_row_count(config)
    if len(rows) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} rows, got {len(rows)}")

    return rows


def parse_args():
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="run the minimal smoke-test configuration",
    )
    return parser.parse_args()


def main():
    """命令行入口。"""
    args = parse_args()
    config = SMOKE_CONFIG if args.smoke else FULL_CONFIG
    rows = run_experiment(config)
    print(
        f"wrote {len(rows)} rows to {config.output_csv.relative_to(PROJECT_ROOT)}"
    )


if __name__ == "__main__":
    main()
