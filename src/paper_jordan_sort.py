"""1990 Jordan-sorting 论文算法的 valid-input ordinary-list 主循环。"""

from paper_jordan import (
    METRIC_NAMES,
    _initialize_paper_jordan_state_values,
    step1_select_predecessor_boundary,
    step2_select_successor_boundary,
    step3a_decreasing,
    step3a_increasing,
    step3b_decreasing,
    step3b_increasing,
    step3c_decreasing,
    step3c_increasing,
    validate_paper_jordan_state,
)


def paper_jordan_sort_valid(seq):
    """使用论文控制流排序一个预先认证的 valid Jordan sequence。

    调用者负责保证元素互异、可比较，并满足项目采用的 Jordan-sequence
    validity model。该纯核心不调用 oracle，也不自行识别 invalid 输入。
    """
    values = list(seq)
    n = len(values)

    if n == 0:
        return []
    if n == 1:
        return [values[0]]
    if n == 2:
        return _order_two(values[0], values[1])

    state = _run_paper_jordan_valid(values)
    return state.partial_order.to_list()


def paper_jordan_diagnostics_valid(seq):
    """在非计时路径运行同一核心，并返回 trace、metrics 和 invariant 结果。"""
    values = list(seq)
    n = len(values)
    if n < 3:
        return {
            "output": _order_small(values),
            "processed_count": n,
            "metrics": {name: 0 for name in METRIC_NAMES},
            "trace": [],
            "invariants_valid": True,
        }

    state = _run_paper_jordan_valid(
        values,
        invariant_callback=validate_paper_jordan_state,
    )
    return {
        "output": state.partial_order.to_list(),
        "processed_count": state.processed_count,
        "metrics": dict(state.metrics),
        "trace": [dict(event) for event in state.trace],
        "invariants_valid": True,
    }


def _run_paper_jordan_valid(values, invariant_callback=None):
    """对已物化、长度至少为三的 values 执行唯一 paper 主循环。"""
    if not isinstance(values, list):
        raise TypeError("values must be a materialized list")
    if len(values) < 3:
        raise ValueError("paper runner requires at least three values")
    if invariant_callback is not None and not callable(invariant_callback):
        raise TypeError("invariant_callback must be callable")

    state = _initialize_paper_jordan_state_values(values)
    if invariant_callback is not None:
        invariant_callback(state)

    n = len(values)
    for iteration in range(4, n + 1):
        left_boundary = step1_select_predecessor_boundary(state, iteration)
        right_boundary = step2_select_successor_boundary(state, iteration)

        previous_value = state.point_value(iteration - 1)
        current_value = state.point_value(iteration)
        if previous_value < current_value:
            new_pair = step3a_increasing(state, iteration, left_boundary)
            step3b_increasing(
                state,
                iteration,
                new_pair.pair_id,
                right_boundary,
            )
            step3c_increasing(state, iteration, new_pair.pair_id)
        elif current_value < previous_value:
            new_pair = step3a_decreasing(state, iteration, right_boundary)
            step3b_decreasing(
                state,
                iteration,
                new_pair.pair_id,
                left_boundary,
            )
            step3c_decreasing(state, iteration, new_pair.pair_id)
        else:
            raise ValueError("point values must be distinct")

        if invariant_callback is not None:
            invariant_callback(state)

    return state


def _order_small(values):
    if not values:
        return []
    if len(values) == 1:
        return [values[0]]
    return _order_two(values[0], values[1])


def _order_two(first, second):
    if first < second:
        return [first, second]
    if second < first:
        return [second, first]
    raise ValueError("point values must be distinct")
