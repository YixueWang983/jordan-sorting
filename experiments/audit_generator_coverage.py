"""Audit generator coverage with structural and invalid-severity metrics."""

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
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
DEFAULT_RUNS_DIR = PROJECT_ROOT / "results" / "runs"

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
    "min_max_depth",
    "median_max_depth",
    "max_max_depth",
    "min_containment_pair_density",
    "median_containment_pair_density",
    "max_containment_pair_density",
    "min_crossing_pair_density",
    "median_crossing_pair_density",
    "max_crossing_pair_density",
    "avg_total_attempts",
    "avg_oracle_calls",
    "avg_fallback_count",
    "min_fallback_count",
    "median_fallback_count",
    "max_fallback_count",
    "avg_mutation_attempts",
    "category_distribution",
    "invalid_reason_distribution",
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


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _median(values):
    if not values:
        return ""
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _distribution(values):
    counts = Counter(value for value in values if value not in {"", None})
    return json.dumps(dict(sorted(counts.items())), sort_keys=True)


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

        def minimum(field):
            values = [_numeric(row, field) for row in group_rows if _numeric(row, field) is not None]
            return min(values) if values else ""

        def median(field):
            values = [_numeric(row, field) for row in group_rows if _numeric(row, field) is not None]
            return _median(values)

        def maximum(field):
            values = [_numeric(row, field) for row in group_rows if _numeric(row, field) is not None]
            return max(values) if values else ""

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
                "min_max_depth": minimum("max_depth"),
                "median_max_depth": median("max_depth"),
                "max_max_depth": maximum("max_depth"),
                "min_containment_pair_density": minimum(
                    "containment_pair_density"
                ),
                "median_containment_pair_density": median(
                    "containment_pair_density"
                ),
                "max_containment_pair_density": maximum(
                    "containment_pair_density"
                ),
                "min_crossing_pair_density": minimum("crossing_pair_density"),
                "median_crossing_pair_density": median("crossing_pair_density"),
                "max_crossing_pair_density": maximum("crossing_pair_density"),
                "avg_total_attempts": avg("total_attempts"),
                "avg_oracle_calls": avg("oracle_calls"),
                "avg_fallback_count": avg("fallback_count"),
                "min_fallback_count": minimum("fallback_count"),
                "median_fallback_count": median("fallback_count"),
                "max_fallback_count": maximum("fallback_count"),
                "avg_mutation_attempts": avg("mutation_attempts"),
                "category_distribution": _distribution(
                    row["structural_category"] for row in group_rows
                ),
                "invalid_reason_distribution": _distribution(
                    row["invalid_reason"] for row in group_rows
                ),
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


def write_audit_config(path, families, sizes, randomized_repetitions, seed):
    data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "families": families,
        "sizes": sizes,
        "randomized_repetitions": randomized_repetitions,
        "seed": seed,
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_audit_manifest(path, config_json, output_csv, summary_csv):
    files = {
        "audit_config_json": Path(config_json),
        "coverage_audit_csv": Path(output_csv),
        "coverage_summary_csv": Path(summary_csv),
    }
    data = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            label: {
                "path": str(file_path),
                "sha256": file_sha256(file_path),
            }
            for label, file_path in files.items()
        },
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output-csv", type=Path, default=None)
    parser.add_argument("--summary-csv", type=Path, default=None)
    parser.add_argument("--config-json", type=Path, default=None)
    parser.add_argument("--manifest-json", type=Path, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.randomized_repetitions < 1:
        raise ValueError("randomized-repetitions must be positive")
    if any(n <= 0 for n in args.sizes):
        raise ValueError("sizes must be positive")

    run_id = args.run_id or "week8_generator_coverage_audit"
    run_dir = args.run_dir or (DEFAULT_RUNS_DIR / run_id)
    explicit_outputs = [
        args.output_csv,
        args.summary_csv,
        args.config_json,
        args.manifest_json,
    ]
    if not any(explicit_outputs) and run_dir.exists() and not args.overwrite:
        raise ValueError(f"run directory already exists: {run_dir}")

    output_csv = args.output_csv or (run_dir / "coverage_audit.csv")
    summary_csv = args.summary_csv or (run_dir / "coverage_summary.csv")
    config_json = args.config_json or (run_dir / "audit_config.json")
    manifest_json = args.manifest_json or (run_dir / "audit_manifest.json")

    rows = audit_generator_coverage(
        families=args.families,
        sizes=args.sizes,
        randomized_repetitions=args.randomized_repetitions,
        seed=args.seed,
    )
    write_audit_config(
        config_json,
        families=args.families,
        sizes=args.sizes,
        randomized_repetitions=args.randomized_repetitions,
        seed=args.seed,
    )
    write_audit(rows, output_csv)
    summary_rows = summarize_audit_rows(rows)
    write_audit_summary(summary_rows, summary_csv)
    write_audit_manifest(
        manifest_json,
        config_json=config_json,
        output_csv=output_csv,
        summary_csv=summary_csv,
    )
    print(
        f"wrote {len(rows)} audit rows to {output_csv}; "
        f"wrote {len(summary_rows)} summary rows to {summary_csv}"
    )


if __name__ == "__main__":
    main()
