"""Audit generator coverage with structural and invalid-severity metrics."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

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
DEFAULT_SIZES = [16, 32, 64, 128]
DEFAULT_RANDOMIZED_REPETITIONS = 30
DEFAULT_SEED = 20260723
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "results" / "week7_generator_coverage_audit.csv"

FIELDS = [
    "family",
    "n",
    "case_id",
    "seed",
    "valid",
    "invalid_reason",
    "max_depth",
    "parented_interval_ratio",
    "containment_pair_density",
    "upper_crossing_pair_count",
    "lower_crossing_pair_count",
    "total_crossing_pair_count",
    "crossing_pair_density",
    "structural_category",
    "has_duplicate_values",
    "sequence_hash",
]


def csv_value(value):
    if value is None:
        return ""
    return value


def repetitions_for_family(family, randomized_repetitions):
    if family in RANDOMIZED_FAMILIES:
        return randomized_repetitions
    return 1


def seed_for_case(family, n, index, base_seed):
    if family in RANDOMIZED_FAMILIES:
        return base_seed + n * 1000 + index
    return None


def sequence_hash(seq):
    payload = json.dumps(list(seq), separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def crossing_pair_density(seq, profile):
    total_crossing = profile["total_crossing_pair_count"]
    if total_crossing is None:
        return None

    # Crossing counts are available only for distinct-value candidates. The
    # matching denominator is the same within-family pair universe used by
    # containment_pair_density.
    upper_count = len(seq) // 2
    lower_count = max((len(seq) - 1) // 2, 0)

    denominator = upper_count * (upper_count - 1) // 2
    denominator += lower_count * (lower_count - 1) // 2
    if denominator == 0:
        return 0.0
    return total_crossing / denominator


def audit_generator_coverage(
    families=DEFAULT_FAMILIES,
    sizes=DEFAULT_SIZES,
    randomized_repetitions=DEFAULT_RANDOMIZED_REPETITIONS,
    seed=DEFAULT_SEED,
):
    rows = []
    for family in families:
        repetitions = repetitions_for_family(family, randomized_repetitions)
        for n in sizes:
            for index in range(1, repetitions + 1):
                case_seed = seed_for_case(family, n, index, seed)
                seq = generate_sequence(family, n, seed=case_seed)
                oracle_result = oracle(seq)
                profile = structure_profile(seq, oracle_result=oracle_result)
                rows.append(
                    {
                        "family": family,
                        "n": len(seq),
                        "case_id": make_case_id(family, len(seq), index),
                        "seed": csv_value(case_seed),
                        "valid": oracle_result["valid"],
                        "invalid_reason": csv_value(oracle_result["reason"]),
                        "max_depth": csv_value(profile["max_depth"]),
                        "parented_interval_ratio": csv_value(
                            profile["parented_interval_ratio"]
                        ),
                        "containment_pair_density": csv_value(
                            profile["containment_pair_density"]
                        ),
                        "upper_crossing_pair_count": csv_value(
                            profile["upper_crossing_pair_count"]
                        ),
                        "lower_crossing_pair_count": csv_value(
                            profile["lower_crossing_pair_count"]
                        ),
                        "total_crossing_pair_count": csv_value(
                            profile["total_crossing_pair_count"]
                        ),
                        "crossing_pair_density": csv_value(
                            crossing_pair_density(seq, profile)
                        ),
                        "structural_category": profile["category"],
                        "has_duplicate_values": len(seq) != len(set(seq)),
                        "sequence_hash": sequence_hash(seq),
                    }
                )
    return rows


def write_audit(rows, output_csv):
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


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
        "--randomized-repetitions",
        type=int,
        default=DEFAULT_RANDOMIZED_REPETITIONS,
        help="cases per randomized family-size pair",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.randomized_repetitions < 1:
        raise ValueError("randomized-repetitions must be positive")

    rows = audit_generator_coverage(
        families=args.families,
        sizes=args.sizes,
        randomized_repetitions=args.randomized_repetitions,
        seed=args.seed,
    )
    write_audit(rows, args.output_csv)
    print(f"wrote {len(rows)} rows to {args.output_csv}")


if __name__ == "__main__":
    main()
