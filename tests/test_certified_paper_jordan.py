"""Safe public certification-wrapper tests."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import certified_paper_jordan  # noqa: E402
from paper_execution_policy import PAPER_EXECUTION_MODE_NAMES  # noqa: E402


class CertifiedPaperJordanSortTests(unittest.TestCase):
    def test_valid_input_is_certified_and_sorted_in_every_mode(self):
        values = [2, 3, 1, 4]

        for mode in PAPER_EXECUTION_MODE_NAMES:
            with self.subTest(mode=mode):
                self.assertEqual(
                    certified_paper_jordan.certified_paper_jordan_sort(
                        values,
                        execution_mode=mode,
                    ),
                    [1, 2, 3, 4],
                )

        self.assertEqual(values, [2, 3, 1, 4])

    def test_invalid_input_is_rejected_before_the_paper_sorter(self):
        with patch.object(
            certified_paper_jordan,
            "paper_jordan_sort_valid",
        ) as sorter_mock:
            with self.assertRaisesRegex(
                ValueError,
                "oracle-certified valid input: upper crossing",
            ):
                certified_paper_jordan.certified_paper_jordan_sort(
                    [1, 3, 2, 4]
                )

        sorter_mock.assert_not_called()

    def test_wrapper_calls_certification_and_core_once(self):
        values = [2, 3, 1, 4]
        real_oracle = certified_paper_jordan.oracle
        real_sorter = certified_paper_jordan.paper_jordan_sort_valid

        with patch.object(
            certified_paper_jordan,
            "oracle",
            wraps=real_oracle,
        ) as oracle_mock, patch.object(
            certified_paper_jordan,
            "paper_jordan_sort_valid",
            wraps=real_sorter,
        ) as sorter_mock:
            result = certified_paper_jordan.certified_paper_jordan_sort(values)

        self.assertEqual(result, [1, 2, 3, 4])
        oracle_mock.assert_called_once()
        sorter_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
