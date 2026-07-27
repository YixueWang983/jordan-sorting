"""1990 Jordan-sorting 论文算法的 valid-input ordinary-list 主循环。"""

from paper_jordan import (
    initialize_paper_jordan_state,
    step1_select_predecessor_boundary,
    step2_select_successor_boundary,
    step3a_decreasing,
    step3a_increasing,
    step3b_decreasing,
    step3b_increasing,
    step3c_decreasing,
    step3c_increasing,
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

    state = initialize_paper_jordan_state(values)
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

    return state.partial_order.to_list()


def _order_two(first, second):
    if first < second:
        return [first, second]
    if second < first:
        return [second, first]
    raise ValueError("point values must be distinct")
