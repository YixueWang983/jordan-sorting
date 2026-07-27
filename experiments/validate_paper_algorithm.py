"""Exhaustively validate the paper Jordan loop without feeding expected order back."""

import argparse
import itertools
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import (  # noqa: E402
    generate_flat,
    generate_incremental_valid,
    generate_nested,
)
from oracle import oracle  # noqa: E402
from paper_jordan import validate_paper_jordan_state  # noqa: E402
from paper_jordan_sort import (  # noqa: E402
    _run_paper_jordan_valid,
    paper_jordan_sort_valid,
)


def validate_exhaustive(max_n=8):
    """Return counts after validating every oracle-accepted permutation."""
    if isinstance(max_n, bool) or not isinstance(max_n, int):
        raise TypeError("max_n must be an integer")
    if not 0 <= max_n <= 9:
        raise ValueError("max_n must satisfy 0 <= max_n <= 9")

    counts = {}
    total_valid = 0
    for n in range(max_n + 1):
        expected_order = list(range(1, n + 1))
        valid_count = 0

        for sequence in itertools.permutations(expected_order):
            if not oracle(sequence)["valid"]:
                continue

            valid_count += 1
            output = _validate_sequence(
                sequence,
                context=f"exhaustive n={n}, sequence={sequence}",
            )

            if output != expected_order:
                raise AssertionError(
                    f"final mismatch: n={n}, sequence={sequence}, output={output}"
                )

        counts[str(n)] = valid_count
        total_valid += valid_count

    return {
        "max_n": max_n,
        "valid_permutations_by_n": counts,
        "total_valid_permutations": total_valid,
        "all_valid": True,
    }


def validate_generated_cases(
    sizes=(16, 32, 64, 128),
    incremental_cases_per_size=10,
    seed=27000,
):
    """Validate reproducible flat, nested, and incremental valid cases."""
    normalized_sizes = tuple(sizes)
    if not normalized_sizes:
        raise ValueError("sizes must not be empty")
    if any(
        isinstance(size, bool) or not isinstance(size, int) or size < 0
        for size in normalized_sizes
    ):
        raise ValueError("sizes must contain non-negative integers")
    if (
        isinstance(incremental_cases_per_size, bool)
        or not isinstance(incremental_cases_per_size, int)
        or incremental_cases_per_size < 1
    ):
        raise ValueError("incremental_cases_per_size must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    counts = {"flat_valid": 0, "nested_valid": 0, "incremental_valid": 0}
    for size in normalized_sizes:
        canonical_cases = (
            ("flat_valid", generate_flat(size)),
            ("nested_valid", generate_nested(size)),
        )
        for family, sequence in canonical_cases:
            _validate_generated_sequence(family, size, None, sequence)
            counts[family] += 1

        for case_index in range(incremental_cases_per_size):
            case_seed = seed + size * 1000 + case_index
            sequence = generate_incremental_valid(size, seed=case_seed)
            _validate_generated_sequence(
                "incremental_valid",
                size,
                case_seed,
                sequence,
            )
            counts["incremental_valid"] += 1

    return {
        "sizes": list(normalized_sizes),
        "incremental_cases_per_size": incremental_cases_per_size,
        "base_seed": seed,
        "cases_by_family": counts,
        "total_cases": sum(counts.values()),
        "all_valid": True,
    }


def _validate_generated_sequence(family, size, seed, sequence):
    oracle_result = oracle(sequence)
    context = f"family={family}, n={size}, seed={seed}"
    if not oracle_result["valid"]:
        raise AssertionError(
            f"generated candidate is invalid: {context}, "
            f"reason={oracle_result['reason']}"
        )

    output = _validate_sequence(sequence, context=context)
    if output != oracle_result["sorted"]:
        raise AssertionError(f"final mismatch: {context}, output={output}")


def _validate_sequence(sequence, context):
    if len(sequence) < 3:
        return paper_jordan_sort_valid(sequence)

    def validate_prefix(state):
        validate_paper_jordan_state(state)
        expected_prefix = sorted(sequence[: state.processed_count])
        if state.partial_order.to_list() != expected_prefix:
            raise AssertionError(
                f"prefix mismatch: {context}, processed={state.processed_count}"
            )

    state = _run_paper_jordan_valid(
        list(sequence),
        invariant_callback=validate_prefix,
    )
    return state.partial_order.to_list()


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-n", type=int, default=8)
    parser.add_argument(
        "--skip-generated",
        action="store_true",
        help="run only exhaustive permutation validation",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = {"exhaustive": validate_exhaustive(args.max_n)}
    if not args.skip_generated:
        result["generated"] = validate_generated_cases()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
