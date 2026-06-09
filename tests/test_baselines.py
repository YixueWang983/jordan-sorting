"""Baseline 排序算法和计时辅助函数的单元测试。"""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from baselines import (  # noqa: E402
    merge_sort,
    python_sort,
    quick_sort,
    sort_plus_laminarity_check,
    time_function,
)


class BaselineTests(unittest.TestCase):
    def test_python_sort(self):
        self.assertEqual(python_sort([3, 1, 2]), [1, 2, 3])

    def test_merge_sort(self):
        self.assertEqual(merge_sort([4, 1, 3, 2]), [1, 2, 3, 4])

    def test_quick_sort(self):
        self.assertEqual(quick_sort([4, 1, 3, 2]), [1, 2, 3, 4])

    def test_sort_functions_handle_empty_and_singleton_sequences(self):
        for sort_func in [python_sort, merge_sort, quick_sort]:
            self.assertEqual(sort_func([]), [])
            self.assertEqual(sort_func([1]), [1])

    def test_sort_functions_do_not_modify_original_input(self):
        for sort_func in [python_sort, merge_sort, quick_sort]:
            original = [3, 1, 2]

            result = sort_func(original)

            self.assertEqual(original, [3, 1, 2])
            self.assertEqual(result, [1, 2, 3])

    def test_sort_functions_match_python_sorted_on_duplicates(self):
        seq = [3, 1, 2, 3, 1]

        self.assertEqual(merge_sort(seq), sorted(seq))
        self.assertEqual(quick_sort(seq), sorted(seq))

    def test_sort_plus_laminarity_check_accepts_valid_case(self):
        result = sort_plus_laminarity_check([1, 6, 2, 5, 3, 4])

        self.assertEqual(result["sorted"], [1, 2, 3, 4, 5, 6])
        self.assertTrue(result["valid"])
        self.assertIsNone(result["reason"])
        self.assertTrue(result["oracle"]["upper_ok"])
        self.assertTrue(result["oracle"]["lower_ok"])

    def test_sort_plus_laminarity_check_reports_invalid_case(self):
        result = sort_plus_laminarity_check([1, 3, 2, 4])

        self.assertEqual(result["sorted"], [1, 2, 3, 4])
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "upper crossing")
        self.assertEqual(result["oracle"]["reason"], "upper crossing")

    def test_time_function_returns_result_and_elapsed_time(self):
        timed = time_function(python_sort, [3, 1, 2])

        self.assertEqual(timed["result"], [1, 2, 3])
        self.assertIsInstance(timed["time_ns"], int)
        self.assertGreaterEqual(timed["time_ns"], 0)

    def test_time_function_does_not_modify_original_input(self):
        original = [3, 1, 2]

        time_function(list.reverse, original)

        self.assertEqual(original, [3, 1, 2])


if __name__ == "__main__":
    unittest.main()
