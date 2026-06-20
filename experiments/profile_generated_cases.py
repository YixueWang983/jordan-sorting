"""Profile generated generator cases with structure statistics."""

from collections import Counter, defaultdict
from pathlib import Path
import sys

from dataclasses import dataclass
import argparse
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from generators import (
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
from stats import (
    MEDIUM_NESTING_VALID,
    NESTED_HEAVY_VALID,
    LOW_NESTING_VALID,
    STRICT_FLAT,
)
from stats import structure_profile


DEFAULT_FAMILIES = [
    FLAT_VALID,
    NESTED_VALID,
    INCREMENTAL_VALID,
    INVALID_UPPER_CROSSING,
    INVALID_LOWER_CROSSING,
    RANDOM_INVALID,
    MUTATION_BASED_INVALID,
]

DEFAULT_SIZES = [8, 16, 32]
DEFAULT_REPETITIONS = 3
DEFAULT_SEED = 20260610
SUMMARY_OUTPUT = "results/generator_structure_profile.csv"
DEFAULT_CASES_DIR = Path("results/generator_audit_cases")

SUMMARY_FIELDS = [
    "family",
    "n",
    "total_cases",
    "valid_cases",
    "invalid_cases",
    "strict_flat",
    "low_nesting_valid",
    "medium_nesting_valid",
    "nested_heavy_valid",
    "invalid",
    "invalid_reason_duplicate_values",
    "invalid_reason_upper_crossing",
    "invalid_reason_lower_crossing",
    "invalid_reason_upper_and_lower_crossing",
    "invalid_reason_other",
    "avg_nesting_density",
    "avg_nesting_count",
    "avg_max_depth",
]


def csv_value(value):
    if value is None:
        return ""
    return value


def _build_case_profiles(families, sizes, repetitions, seed, cases_dir):
    output_dir = Path(cases_dir)
    rows = []
    for family in families:
        paths = generate_dataset(
            family=family,
            sizes=sizes,
            repetitions=repetitions,
            output_dir=output_dir,
            seed=seed,
        )
        for path in paths:
            case = load_test_case(path)
            n = int(case["n"])
            profile = structure_profile(case["sequence"], oracle_result=case["oracle"])
            profile_row = {
                "case_id": case["id"],
                "family": family,
                "n": n,
                "seed": csv_value(case["seed"]),
                "oracle_valid": case["oracle"]["valid"],
                "oracle_reason": csv_value(case["oracle"]["reason"]),
                "category": profile["category"],
                "nesting_density": profile["nesting_density"],
                "nesting_count": profile["nesting_count"],
                "max_depth": profile["max_depth"],
            }
            rows.append(profile_row)
    return rows


def _normalize_family_category_row(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["family"], row["n"])].append(row)

    summary = []
    for (family, n), records in sorted(grouped.items()):
        valid_records = [r for r in records if r["oracle_valid"]]
        invalid_records = [r for r in records if not r["oracle_valid"]]

        category_counter = Counter(r["category"] for r in records)
        invalid_reason_counter = Counter(
            r["oracle_reason"] for r in invalid_records if r["oracle_reason"]
        )

        density_values = [
            r["nesting_density"] for r in records if r["nesting_density"] is not None
        ]
        nesting_values = [
            r["nesting_count"] for r in records if r["nesting_count"] is not None
        ]
        depth_values = [r["max_depth"] for r in records if r["max_depth"] is not None]

        def mean(values):
            return sum(values) / len(values) if values else 0.0

        summary.append(
            {
                "family": family,
                "n": n,
                "total_cases": len(records),
                "valid_cases": len(valid_records),
                "invalid_cases": len(invalid_records),
                "strict_flat": category_counter[STRICT_FLAT],
                "low_nesting_valid": category_counter[LOW_NESTING_VALID],
                "medium_nesting_valid": category_counter[MEDIUM_NESTING_VALID],
                "nested_heavy_valid": category_counter[NESTED_HEAVY_VALID],
                "invalid": category_counter["invalid"],
                "invalid_reason_duplicate_values": invalid_reason_counter["duplicate values"],
                "invalid_reason_upper_crossing": invalid_reason_counter["upper crossing"],
                "invalid_reason_lower_crossing": invalid_reason_counter["lower crossing"],
                "invalid_reason_upper_and_lower_crossing": invalid_reason_counter[
                    "upper and lower crossing"
                ],
                "invalid_reason_other": sum(
                    count
                    for reason, count in invalid_reason_counter.items()
                    if reason
                    not in {
                        "duplicate values",
                        "upper crossing",
                        "lower crossing",
                        "upper and lower crossing",
                    }
                ),
                "avg_nesting_density": mean(density_values),
                "avg_nesting_count": mean(nesting_values),
                "avg_max_depth": mean(depth_values),
            }
        )
    return summary


def profile_and_write(
    families,
    sizes,
    repetitions,
    output_csv,
    cases_dir=DEFAULT_CASES_DIR,
    seed=DEFAULT_SEED,
):
    case_profiles = _build_case_profiles(
        families=families,
        sizes=sizes,
        repetitions=repetitions,
        seed=seed,
        cases_dir=cases_dir,
    )
    summary_rows = _normalize_family_category_row(case_profiles)

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary_rows)

    return summary_rows


@dataclass(frozen=True)
class ProfileExperimentConfig:
    families: list[str]
    sizes: list[int]
    repetitions: int
    output_csv: Path
    cases_dir: Path
    seed: int = DEFAULT_SEED


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--families",
        nargs="*",
        default=DEFAULT_FAMILIES,
        help="generator families to audit",
    )
    parser.add_argument(
        "--sizes",
        nargs="*",
        type=int,
        default=DEFAULT_SIZES,
        help="input sizes to audit",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
        help="cases per family-size pair",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="base seed for randomized families",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path(SUMMARY_OUTPUT),
        help=f"output summary CSV, default: {SUMMARY_OUTPUT}",
    )
    parser.add_argument(
        "--cases-dir",
        type=Path,
        default=DEFAULT_CASES_DIR,
        help=f"directory for generated audit cases, default: {DEFAULT_CASES_DIR}",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    config = ProfileExperimentConfig(
        families=args.families,
        sizes=args.sizes,
        repetitions=args.repetitions,
        output_csv=args.output_csv,
        cases_dir=args.cases_dir,
        seed=args.seed,
    )
    if config.repetitions < 1:
        raise ValueError("repetitions must be positive")

    rows = profile_and_write(
        families=config.families,
        sizes=config.sizes,
        repetitions=config.repetitions,
        output_csv=config.output_csv,
        cases_dir=config.cases_dir,
        seed=config.seed,
    )
    print(f"wrote {len(rows)} summary rows to {config.output_csv}")


if __name__ == "__main__":
    run()
