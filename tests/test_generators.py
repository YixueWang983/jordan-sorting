"""测试实例生成器的单元测试。"""

import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generators import (  # noqa: E402
    FLAT_VALID,
    INVALID_LOWER_CROSSING,
    INVALID_UPPER_CROSSING,
    MUTATION_BASED_INVALID,
    NESTED_VALID,
    RANDOM_INVALID,
    RANDOM_PERMUTATION,
    generate_flat,
    generate_dataset,
    generate_invalid_lower_crossing,
    generate_invalid_upper_crossing,
    generate_mutation_based_invalid,
    generate_nested,
    generate_random_invalid,
    generate_random_permutation,
    generate_small_handmade_valid_cases,
    load_test_case,
    make_case_id,
    make_test_case,
    mutate_by_swap,
    save_test_case,
)
from oracle import oracle  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_generate_flat(self):
        seq = generate_flat(6)

        self.assertEqual(seq, [1, 2, 3, 4, 5, 6])
        self.assertTrue(oracle(seq)["valid"])

    def test_generate_nested_even_size(self):
        seq = generate_nested(6)

        self.assertEqual(seq, [1, 6, 2, 5, 3, 4])
        self.assertTrue(oracle(seq)["valid"])

    def test_nested_generator_outputs_valid_cases_for_small_even_n(self):
        for n in [2, 4, 6, 8, 10]:
            seq = generate_nested(n)
            result = oracle(seq)

            self.assertTrue(result["valid"], seq)

    def test_generate_nested_odd_size(self):
        seq = generate_nested(5)

        self.assertEqual(seq, [1, 5, 2, 4, 3])
        self.assertTrue(oracle(seq)["valid"])

    def test_generate_invalid_upper_crossing(self):
        seq = generate_invalid_upper_crossing(8)
        result = oracle(seq)

        self.assertEqual(seq, [1, 3, 2, 4, 5, 6, 7, 8])
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "upper crossing")

    def test_generate_invalid_lower_crossing(self):
        seq = generate_invalid_lower_crossing(8)
        result = oracle(seq)

        self.assertEqual(seq, [1, 2, 4, 3, 5, 6, 7, 8])
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "lower crossing")

    def test_invalid_upper_crossing_requires_at_least_four_elements(self):
        with self.assertRaises(ValueError):
            generate_invalid_upper_crossing(3)

    def test_invalid_lower_crossing_requires_at_least_five_elements(self):
        with self.assertRaises(ValueError):
            generate_invalid_lower_crossing(4)

    def test_generate_random_permutation(self):
        seq = generate_random_permutation(8, seed=11)

        self.assertEqual(sorted(seq), list(range(1, 9)))
        self.assertEqual(len(set(seq)), 8)

    def test_generate_random_permutation_is_reproducible(self):
        seq1 = generate_random_permutation(8, seed=11)
        seq2 = generate_random_permutation(8, seed=11)

        self.assertEqual(seq1, seq2)

    def test_generate_random_invalid_is_certified_invalid(self):
        seq = generate_random_invalid(8, seed=11)
        result = oracle(seq)

        self.assertEqual(sorted(seq), list(range(1, 9)))
        self.assertFalse(result["valid"])

    def test_generate_random_invalid_is_reproducible(self):
        seq1 = generate_random_invalid(8, seed=11)
        seq2 = generate_random_invalid(8, seed=11)

        self.assertEqual(seq1, seq2)

    def test_generate_random_invalid_raises_after_max_attempts(self):
        with self.assertRaises(ValueError):
            generate_random_invalid(1, seed=11, max_attempts=3)

    def test_mutate_by_swap(self):
        self.assertEqual(mutate_by_swap([1, 2, 3], i=0, j=2), [3, 2, 1])

    def test_mutate_by_swap_does_not_modify_original(self):
        original = [1, 2, 3]
        mutated = mutate_by_swap(original, i=0, j=2)

        self.assertEqual(original, [1, 2, 3])
        self.assertEqual(mutated, [3, 2, 1])

    def test_generate_mutation_based_invalid_is_certified_invalid(self):
        base = generate_nested(8)
        seq = generate_mutation_based_invalid(base, seed=1)
        result = oracle(seq)

        self.assertEqual(sorted(seq), list(range(1, 9)))
        self.assertFalse(result["valid"])

    def test_generate_mutation_based_invalid_is_reproducible(self):
        base = generate_nested(8)
        seq1 = generate_mutation_based_invalid(base, seed=1)
        seq2 = generate_mutation_based_invalid(base, seed=1)

        self.assertEqual(seq1, seq2)

    def test_generate_mutation_based_invalid_does_not_modify_original(self):
        base = generate_nested(8)
        original = list(base)

        generate_mutation_based_invalid(base, seed=1)

        self.assertEqual(base, original)

    def test_generate_mutation_based_invalid_raises_after_max_attempts(self):
        with self.assertRaises(ValueError):
            generate_mutation_based_invalid([1], seed=11, max_attempts=3)

    def test_small_handmade_valid_cases(self):
        for seq in generate_small_handmade_valid_cases():
            self.assertTrue(oracle(seq)["valid"], seq)

    def test_make_case_id(self):
        self.assertEqual(make_case_id(FLAT_VALID, 16, 3), "flat_valid_n16_003")
        self.assertEqual(
            make_case_id(MUTATION_BASED_INVALID, 8, 1),
            "mutation_based_invalid_n8_001",
        )

    def test_make_test_case_contains_oracle_result(self):
        case = make_test_case([1, 2, 3, 4], FLAT_VALID, "flat_valid_n4_001")

        self.assertEqual(case["id"], "flat_valid_n4_001")
        self.assertEqual(case["n"], 4)
        self.assertEqual(case["family"], FLAT_VALID)
        self.assertIsNone(case["seed"])
        self.assertEqual(case["sequence"], [1, 2, 3, 4])
        self.assertTrue(case["oracle"]["valid"])
        self.assertEqual(case["oracle"]["sorted"], [1, 2, 3, 4])

    def test_save_and_load_test_case_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "flat_valid_n4_001.json"

            saved = save_test_case(
                [1, 2, 3, 4],
                FLAT_VALID,
                path,
                case_id="flat_valid_n4_001",
            )
            loaded = load_test_case(path)

            self.assertEqual(loaded, saved)

    def test_dataset_generation_creates_json_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_dataset(FLAT_VALID, sizes=[4, 6], repetitions=2, output_dir=tmpdir)

            self.assertEqual(len(paths), 4)
            for path in paths:
                case = load_test_case(path)
                self.assertEqual(case["family"], FLAT_VALID)
                self.assertTrue(case["oracle"]["valid"])

    def test_dataset_generation_preserves_random_seeds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_dataset(
                RANDOM_PERMUTATION,
                sizes=[8],
                repetitions=2,
                output_dir=tmpdir,
                seed=11,
            )

            cases = [load_test_case(path) for path in paths]

            self.assertEqual([case["seed"] for case in cases], [8012, 8013])
            self.assertNotEqual(cases[0]["sequence"], cases[1]["sequence"])

    def test_random_invalid_dataset_family_is_certified_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_dataset(
                RANDOM_INVALID,
                sizes=[8],
                repetitions=2,
                output_dir=tmpdir,
                seed=11,
            )
            cases = [load_test_case(path) for path in paths]

            self.assertEqual([case["family"] for case in cases], [RANDOM_INVALID, RANDOM_INVALID])
            self.assertEqual([case["seed"] for case in cases], [8012, 8013])
            for case in cases:
                self.assertFalse(case["oracle"]["valid"])

    def test_invalid_dataset_families_are_certified_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            families = [INVALID_UPPER_CROSSING, INVALID_LOWER_CROSSING]
            for family in families:
                min_size = 5 if family == INVALID_LOWER_CROSSING else 4
                paths = generate_dataset(family, sizes=[min_size], repetitions=1, output_dir=tmpdir)
                case = load_test_case(paths[0])

                self.assertEqual(case["family"], family)
                self.assertFalse(case["oracle"]["valid"])

    def test_invalid_dataset_generation_respects_requested_sizes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_dataset(
                INVALID_UPPER_CROSSING,
                sizes=[4, 8],
                repetitions=1,
                output_dir=tmpdir,
            )
            cases = [load_test_case(path) for path in paths]

            self.assertEqual([case["n"] for case in cases], [4, 8])
            self.assertEqual(
                [case["id"] for case in cases],
                ["invalid_upper_crossing_n4_001", "invalid_upper_crossing_n8_001"],
            )

    def test_invalid_lower_dataset_generation_respects_requested_sizes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_dataset(
                INVALID_LOWER_CROSSING,
                sizes=[5, 8],
                repetitions=1,
                output_dir=tmpdir,
            )
            cases = [load_test_case(path) for path in paths]

            self.assertEqual([case["n"] for case in cases], [5, 8])
            self.assertEqual(
                [case["id"] for case in cases],
                ["invalid_lower_crossing_n5_001", "invalid_lower_crossing_n8_001"],
            )

    def test_nested_dataset_family_is_certified_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_dataset(NESTED_VALID, sizes=[6], repetitions=1, output_dir=tmpdir)
            case = load_test_case(paths[0])

            self.assertTrue(case["oracle"]["valid"])


if __name__ == "__main__":
    unittest.main()
