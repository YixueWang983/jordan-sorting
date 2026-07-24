"""Audit generator coverage with structural and invalid-severity metrics."""

import argparse
import csv
import hashlib
import json
import random
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
    generate_flat,
    generate_incremental_valid,
    generate_invalid_lower_crossing,
    generate_invalid_upper_crossing,
    generate_nested,
    generate_random_permutation,
    generate_sequence,
    insert_rank_at_end,
    make_case_id,
    mutate_by_swap,
    safe_extension_ranks,
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
DEFAULT_SIZES = [31, 32, 33, 63, 64, 65, 127, 128, 129, 255, 256, 257]
DEFAULT_RANDOMIZED_REPETITIONS = 30
DEFAULT_SEED = 20260723
DEFAULT_OUTPUT_CSV = PROJECT_ROOT / "results" / "week7_generator_coverage_audit.csv"
DEFAULT_SUMMARY_CSV = PROJECT_ROOT / "results" / "week8_generator_coverage_summary.csv"

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
    "total_attempts",
    "oracle_calls",
    "fallback_count",
    "accepted_random_extensions",
    "safe_extensions",
    "attempts_until_invalid",
    "accepted_seed",
    "base_sequence_hash",
    "base_seed",
    "swap_i",
    "swap_j",
    "mutation_attempts",
]

SUMMARY_FIELDS = [
    "family",
    "n",
    "case_count",
    "unique_case_count",
    "duplicate_case_count",
    "duplicate_case_rate",
    "valid_count",
    "invalid_count",
    "duplicate_value_count",
    "avg_crossing_pair_density",
    "avg_total_attempts",
    "avg_oracle_calls",
    "avg_fallback_count",
    "avg_mutation_attempts",
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


def _empty_metadata():
    return {
        "total_attempts": "",
        "oracle_calls": "",
        "fallback_count": "",
        "accepted_random_extensions": "",
        "safe_extensions": "",
        "attempts_until_invalid": "",
        "accepted_seed": "",
        "base_sequence_hash": "",
        "base_seed": "",
        "swap_i": "",
        "swap_j": "",
        "mutation_attempts": "",
    }


def generate_incremental_valid_with_metadata(n, seed=None, max_attempts_per_step=20):
    """Generate incremental-valid input and expose construction diagnostics."""
    rng = random.Random(seed)
    seq = []
    total_attempts = 0
    oracle_calls = 0
    fallback_count = 0
    accepted_random_extensions = 0
    safe_extensions = 0

    while len(seq) < n:
        accepted = False
        for _ in range(max_attempts_per_step):
            total_attempts += 1
            new_rank = rng.randint(1, len(seq) + 1)
            candidate = insert_rank_at_end(seq, new_rank)
            oracle_calls += 1
            if oracle(candidate)["valid"]:
                seq = candidate
                accepted = True
                accepted_random_extensions += 1
                break

        if not accepted:
            fallback_count += 1
            safe_extensions += 1
            new_rank = rng.choice(safe_extension_ranks(seq))
            candidate = insert_rank_at_end(seq, new_rank)
            oracle_calls += 1
            result = oracle(candidate)
            if not result["valid"]:
                raise RuntimeError(
                    f"safe extension failed unexpectedly: {candidate}, reason={result['reason']}"
                )
            seq = candidate

    metadata = _empty_metadata()
    metadata.update(
        {
            "total_attempts": total_attempts,
            "oracle_calls": oracle_calls,
            "fallback_count": fallback_count,
            "accepted_random_extensions": accepted_random_extensions,
            "safe_extensions": safe_extensions,
        }
    )
    return seq, metadata


def generate_random_invalid_with_metadata(n, seed=None, max_attempts=1000):
    """Generate random-invalid input and expose rejection-sampling diagnostics."""
    if n < 4:
        raise ValueError("random invalid sequence requires n >= 4")

    oracle_calls = 0
    for attempt in range(max_attempts):
        attempt_seed = None if seed is None else seed + attempt
        values = generate_random_permutation(n, seed=attempt_seed)
        oracle_calls += 1
        if not oracle(values)["valid"]:
            metadata = _empty_metadata()
            metadata.update(
                {
                    "total_attempts": attempt + 1,
                    "oracle_calls": oracle_calls,
                    "attempts_until_invalid": attempt + 1,
                    "accepted_seed": csv_value(attempt_seed),
                }
            )
            return values, metadata
    raise ValueError("failed to generate random invalid sequence")


def generate_mutation_based_invalid_with_metadata(n, seed=None, max_attempts=1000):
    """Generate mutation-based invalid input and expose base/swap diagnostics."""
    if n < 4:
        raise ValueError("mutation-based invalid cases require n >= 4")

    base, base_metadata = generate_incremental_valid_with_metadata(n, seed=seed)
    base_seed = seed
    oracle_calls = base_metadata["oracle_calls"]

    for attempt in range(max_attempts):
        attempt_seed = None if seed is None else seed + attempt
        rng = random.Random(attempt_seed)
        swap_i, swap_j = rng.sample(range(len(base)), 2)
        candidate = mutate_by_swap(base, i=swap_i, j=swap_j)
        oracle_calls += 1
        if not oracle(candidate)["valid"]:
            metadata = _empty_metadata()
            metadata.update(
                {
                    "total_attempts": base_metadata["total_attempts"] + attempt + 1,
                    "oracle_calls": oracle_calls,
                    "fallback_count": base_metadata["fallback_count"],
                    "accepted_random_extensions": base_metadata[
                        "accepted_random_extensions"
                    ],
                    "safe_extensions": base_metadata["safe_extensions"],
                    "base_sequence_hash": sequence_hash(base),
                    "base_seed": csv_value(base_seed),
                    "swap_i": swap_i,
                    "swap_j": swap_j,
                    "mutation_attempts": attempt + 1,
                }
            )
            return candidate, metadata
    raise ValueError("failed to generate invalid mutation")


def generate_sequence_with_metadata(family, n, seed=None):
    """Generate a sequence plus family-specific construction metadata."""
    metadata = _empty_metadata()
    if family == FLAT_VALID:
        return generate_flat(n), metadata
    if family == NESTED_VALID:
        return generate_nested(n), metadata
    if family == INVALID_UPPER_CROSSING:
        return generate_invalid_upper_crossing(n), metadata
    if family == INVALID_LOWER_CROSSING:
        return generate_invalid_lower_crossing(n), metadata
    if family == INCREMENTAL_VALID:
        return generate_incremental_valid_with_metadata(n, seed=seed)
    if family == RANDOM_INVALID:
        return generate_random_invalid_with_metadata(n, seed=seed)
    if family == MUTATION_BASED_INVALID:
        return generate_mutation_based_invalid_with_metadata(n, seed=seed)
    return generate_sequence(family, n, seed=seed), metadata


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
                seq, generation_metadata = generate_sequence_with_metadata(
                    family,
                    n,
                    seed=case_seed,
                )
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
                        **generation_metadata,
                    }
                )
    return rows


def _numeric(row, field):
    value = row.get(field)
    if value in {"", None}:
        return None
    return float(value)


def summarize_audit_rows(rows):
    """Summarize generator audit rows by family and size."""
    grouped = {}
    for row in rows:
        grouped.setdefault((row["family"], row["n"]), []).append(row)

    summaries = []
    for (family, n), group_rows in sorted(grouped.items()):
        hashes = [row["sequence_hash"] for row in group_rows]

        def avg(field):
            values = [_numeric(row, field) for row in group_rows if _numeric(row, field) is not None]
            return sum(values) / len(values) if values else ""

        summaries.append(
            {
                "family": family,
                "n": n,
                "case_count": len(group_rows),
                "unique_case_count": len(set(hashes)),
                "duplicate_case_count": len(hashes) - len(set(hashes)),
                "duplicate_case_rate": (
                    (len(hashes) - len(set(hashes))) / len(hashes)
                    if hashes
                    else 0.0
                ),
                "valid_count": sum(1 for row in group_rows if row["valid"]),
                "invalid_count": sum(1 for row in group_rows if not row["valid"]),
                "duplicate_value_count": sum(
                    1 for row in group_rows if row["has_duplicate_values"]
                ),
                "avg_crossing_pair_density": avg("crossing_pair_density"),
                "avg_total_attempts": avg("total_attempts"),
                "avg_oracle_calls": avg("oracle_calls"),
                "avg_fallback_count": avg("fallback_count"),
                "avg_mutation_attempts": avg("mutation_attempts"),
            }
        )
    return summaries


def write_audit(rows, output_csv):
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_audit_summary(rows, output_csv):
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
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
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
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
    summary_rows = summarize_audit_rows(rows)
    write_audit_summary(summary_rows, args.summary_csv)
    print(
        f"wrote {len(rows)} audit rows to {args.output_csv}; "
        f"wrote {len(summary_rows)} summary rows to {args.summary_csv}"
    )


if __name__ == "__main__":
    main()
