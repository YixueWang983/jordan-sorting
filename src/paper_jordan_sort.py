"""1990 Jordan-sorting 论文算法的 valid-input ordinary-list 主循环。"""

from paper_execution_policy import (
    CHECKED_MODE,
    CHECKED_POLICY,
    resolve_paper_execution_policy,
)
from paper_jordan import (
    METRIC_NAMES,
    _run_paper_jordan_state_values,
    validate_paper_jordan_state,
)


def paper_jordan_sort_valid(seq, execution_mode=CHECKED_MODE):
    """使用论文控制流排序一个预先认证的 valid Jordan sequence。

    调用者负责保证元素互异、可比较，并满足项目采用的 Jordan-sequence
    validity model。该纯核心不调用 oracle，也不自行识别 invalid 输入。
    execution_mode 仅控制完整 backend audit、trace 和 operation counters，
    不改变 Step 1/2/3、局部安全检查、stage results 或输出恢复。
    """
    execution_policy = resolve_paper_execution_policy(execution_mode)
    values = list(seq)
    n = len(values)

    if n == 0:
        return []
    if n == 1:
        return [values[0]]
    if n == 2:
        return _order_two(values[0], values[1])

    state = _run_paper_jordan_valid(
        values,
        execution_policy=execution_policy,
    )
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
        execution_policy=CHECKED_POLICY,
    )
    return {
        "output": state.partial_order.to_list(),
        "processed_count": state.processed_count,
        "metrics": dict(state.metrics),
        "trace": [dict(event) for event in state.trace],
        "invariants_valid": True,
    }


def _run_paper_jordan_valid(
    values,
    invariant_callback=None,
    execution_policy=CHECKED_POLICY,
):
    """对已物化、长度至少为三的 values 执行唯一 paper 主循环。"""
    return _run_paper_jordan_state_values(
        values,
        invariant_callback=invariant_callback,
        execution_policy=execution_policy,
    )


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
