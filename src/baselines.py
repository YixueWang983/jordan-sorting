"""Baseline 排序算法和计时辅助函数。"""

import time

from oracle import oracle


def python_sort(seq):
    """使用 Python 内置排序，作为优化过的 practical baseline。"""
    return sorted(seq)


def merge_sort(seq):
    """返回归并排序后的新列表，不修改原始输入。"""
    values = list(seq)
    if len(values) <= 1:
        return values

    mid = len(values) // 2
    left = merge_sort(values[:mid])
    right = merge_sort(values[mid:])
    return _merge_sorted_lists(left, right)


def _merge_sorted_lists(left, right):
    """合并两个已排序列表。"""
    merged = []
    left_index = 0
    right_index = 0

    while left_index < len(left) and right_index < len(right):
        if left[left_index] <= right[right_index]:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    merged.extend(left[left_index:])
    merged.extend(right[right_index:])
    return merged


def quick_sort(seq):
    """返回快速排序后的新列表，使用固定 pivot 保持可复现。"""
    values = list(seq)
    if len(values) <= 1:
        return values

    pivot = values[len(values) // 2]
    smaller = []
    equal = []
    greater = []

    for value in values:
        if value < pivot:
            smaller.append(value)
        elif value > pivot:
            greater.append(value)
        else:
            equal.append(value)

    return quick_sort(smaller) + equal + quick_sort(greater)


def sort_plus_laminarity_check(seq):
    """先运行 oracle 检查 Jordan 结构，再返回普通排序结果。"""
    values = list(seq)
    oracle_result = oracle(values)

    return {
        "sorted": python_sort(values),
        "oracle": oracle_result,
        "valid": oracle_result["valid"],
        "reason": oracle_result["reason"],
    }


def time_function(func, seq):
    """计时一个函数在序列副本上的运行时间，返回结果和纳秒耗时。"""
    values = list(seq)
    start = time.perf_counter_ns()
    result = func(values)
    end = time.perf_counter_ns()

    return {
        "result": result,
        "time_ns": end - start,
    }
