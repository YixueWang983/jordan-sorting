"""Standalone paper-algorithm exhaustive validator tests."""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from validate_paper_algorithm import (  # noqa: E402
    main,
    validate_exhaustive,
    validate_generated_cases,
)


class ValidatePaperAlgorithmTests(unittest.TestCase):
    def test_validate_exhaustive_through_n5(self):
        result = validate_exhaustive(max_n=5)

        self.assertEqual(
            result["valid_permutations_by_n"],
            {
                "0": 1,
                "1": 1,
                "2": 2,
                "3": 6,
                "4": 16,
                "5": 50,
            },
        )
        self.assertEqual(result["total_valid_permutations"], 76)
        self.assertTrue(result["all_valid"])

    def test_validate_exhaustive_rejects_invalid_max_n(self):
        for max_n in (True, 1.5, "5"):
            with self.subTest(max_n=max_n):
                with self.assertRaises(TypeError):
                    validate_exhaustive(max_n)

        for max_n in (-1, 10):
            with self.subTest(max_n=max_n):
                with self.assertRaises(ValueError):
                    validate_exhaustive(max_n)

    def test_validate_generated_cases_uses_reproducible_family_counts(self):
        result = validate_generated_cases(
            sizes=(4, 5),
            incremental_cases_per_size=2,
            seed=31,
        )

        self.assertEqual(
            result["cases_by_family"],
            {
                "flat_valid": 2,
                "nested_valid": 2,
                "incremental_valid": 4,
            },
        )
        self.assertEqual(result["total_cases"], 8)
        self.assertTrue(result["all_valid"])

    def test_validate_generated_cases_rejects_invalid_configuration(self):
        for sizes in ((), (-1,), (True,), (4.5,)):
            with self.subTest(sizes=sizes):
                with self.assertRaises(ValueError):
                    validate_generated_cases(sizes=sizes)

        for repetitions in (0, -1, True, 1.5):
            with self.subTest(repetitions=repetitions):
                with self.assertRaises(ValueError):
                    validate_generated_cases(
                        sizes=(4,),
                        incremental_cases_per_size=repetitions,
                    )

        with self.assertRaises(TypeError):
            validate_generated_cases(sizes=(4,), seed=True)

    def test_main_prints_machine_readable_summary(self):
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            main(["--max-n", "4", "--skip-generated"])

        result = json.loads(stdout.getvalue())
        self.assertEqual(result["exhaustive"]["max_n"], 4)
        self.assertEqual(result["exhaustive"]["total_valid_permutations"], 26)
        self.assertTrue(result["exhaustive"]["all_valid"])
        self.assertNotIn("generated", result)


if __name__ == "__main__":
    unittest.main()
