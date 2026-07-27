"""1990 Jordan-sorting 论文算法的初始化与 Step 1/2 边界选择。"""

from __future__ import annotations

from dataclasses import dataclass

from partial_sorted_list import (
    NEGATIVE_INFINITY,
    POSITIVE_INFINITY,
    PointRef,
    SortedOrderList,
)
from sibling_list_backend import (
    LOWER,
    UPPER,
    OrdinarySiblingListBackend,
    PairRecord,
)


UPPER_DUMMY_PAIR_ID = -1
LOWER_DUMMY_PAIR_ID = -2

METRIC_NAMES = (
    "predecessor_accesses",
    "successor_accesses",
    "boundary_pair_checks",
    "sibling_scan_checks",
    "sibling_lists_created",
    "sibling_list_insertions",
    "sibling_list_splits",
    "split_items_scanned",
    "split_items_moved",
    "output_insertions",
    "z1_anchor_adjustments",
    "invariant_checks",
    "trace_event_count",
)


@dataclass(frozen=True)
class BoundarySelection:
    """Step 1 或 Step 2 返回的边界 pair 及其邻接点信息。"""

    neighbor_point_id: int | None
    pair_id: int
    used_dummy_pair: bool
    adjusted_for_z1: bool


@dataclass
class PaperJordanState:
    """保存论文算法当前已处理前缀所需的普通数据结构。"""

    points: tuple[PointRef, ...]
    processed_count: int
    partial_order: SortedOrderList
    pairs: dict[int, PairRecord]
    pair_by_end_index: dict[int, int]
    sibling_backend: OrdinarySiblingListBackend
    upper_dummy_pair_id: int
    lower_dummy_pair_id: int
    trace: list[dict]
    metrics: dict[str, int]

    def point(self, paper_index):
        """按论文的一基下标返回 PointRef。"""
        _require_paper_index(paper_index, len(self.points))
        return self.points[paper_index - 1]

    def point_value(self, paper_index):
        """按论文的一基下标返回原始值。"""
        return self.point(paper_index).value


def pair_family_for_end_index(end_index):
    """根据 pair 结束下标的奇偶性返回 upper 或 lower。"""
    if isinstance(end_index, bool) or not isinstance(end_index, int):
        raise TypeError("end_index must be an integer")
    if end_index < 2:
        raise ValueError("a finite pair requires end_index >= 2")
    return UPPER if end_index % 2 == 0 else LOWER


def initialize_paper_jordan_state(seq):
    """为 n >= 3 的输入建立前三点、P2/P3 和两棵 family 根结构。"""
    values = list(seq)
    if len(values) < 3:
        raise ValueError("PaperJordanState initialization requires n >= 3")

    points = tuple(
        PointRef(paper_index=index, value=value)
        for index, value in enumerate(values, start=1)
    )
    partial_order = _order_first_three(points[:3])
    point_value = lambda point_id: points[point_id - 1].value
    sibling_backend = OrdinarySiblingListBackend(point_value)

    upper_dummy = PairRecord(
        UPPER_DUMMY_PAIR_ID,
        None,
        None,
        None,
        UPPER,
        is_dummy=True,
    )
    lower_dummy = PairRecord(
        LOWER_DUMMY_PAIR_ID,
        None,
        None,
        None,
        LOWER,
        is_dummy=True,
    )
    pair_2 = PairRecord(2, 2, 1, 2, UPPER)
    pair_3 = PairRecord(3, 3, 2, 3, LOWER)
    pairs = {
        upper_dummy.pair_id: upper_dummy,
        lower_dummy.pair_id: lower_dummy,
        pair_2.pair_id: pair_2,
        pair_3.pair_id: pair_3,
    }

    for pair in (upper_dummy, lower_dummy, pair_2, pair_3):
        sibling_backend.register_pair(pair)

    upper_list_id = sibling_backend.make_list(
        pair_2.pair_id,
        upper_dummy.pair_id,
    )
    lower_list_id = sibling_backend.make_list(
        pair_3.pair_id,
        lower_dummy.pair_id,
    )

    metrics = {name: 0 for name in METRIC_NAMES}
    state = PaperJordanState(
        points=points,
        processed_count=3,
        partial_order=partial_order,
        pairs=pairs,
        pair_by_end_index={2: pair_2.pair_id, 3: pair_3.pair_id},
        sibling_backend=sibling_backend,
        upper_dummy_pair_id=upper_dummy.pair_id,
        lower_dummy_pair_id=lower_dummy.pair_id,
        trace=[],
        metrics=metrics,
    )
    _record_trace(
        state,
        {
            "step": "initialize_partial_order",
            "processed_count": 3,
            "point_ids": partial_order.to_point_ids(),
        },
    )
    _record_trace(
        state,
        {
            "step": "initialize_pair_families",
            "upper_pair_id": pair_2.pair_id,
            "lower_pair_id": pair_3.pair_id,
            "upper_list_id": upper_list_id,
            "lower_list_id": lower_list_id,
        },
    )

    partial_order.validate_links()
    sibling_backend.validate_invariants()
    return state


def select_processed_same_family_pair(state, point_id, iteration):
    """选出包含 point、与 P_iteration 同 family 的已处理 finite pair。"""
    _require_next_iteration(state, iteration)
    _require_processed_point(state, point_id)

    candidate_end_index = None
    if point_id >= 2 and point_id % 2 == iteration % 2:
        candidate_end_index = point_id
    elif (
        point_id + 1 <= state.processed_count
        and (point_id + 1) % 2 == iteration % 2
    ):
        candidate_end_index = point_id + 1

    if candidate_end_index is None:
        raise ValueError(
            "processed point has no finite same-family pair for this iteration"
        )

    try:
        pair_id = state.pair_by_end_index[candidate_end_index]
        pair = state.pairs[pair_id]
    except KeyError as exc:
        raise RuntimeError("processed same-family pair is missing from state") from exc

    expected_family = pair_family_for_end_index(iteration)
    if pair.end_index != candidate_end_index or pair.family != expected_family:
        raise RuntimeError("processed same-family pair mapping is inconsistent")
    if point_id not in {pair.first_point_id, pair.second_point_id}:
        raise RuntimeError("selected pair does not contain the requested point")
    if state.sibling_backend.get_pair(pair_id) is not pair:
        raise RuntimeError("state and sibling backend disagree about the selected pair")
    if pair.parent_pair_id is None or pair.sibling_list_id is None:
        raise RuntimeError("selected processed pair has no live sibling-list ownership")
    sibling_list = state.sibling_backend.get_list(pair.sibling_list_id)
    if sibling_list.list_id != pair.sibling_list_id:
        raise RuntimeError("selected pair and sibling-list IDs disagree")
    if sibling_list.owner_parent_pair_id != pair.parent_pair_id:
        raise RuntimeError("selected pair and sibling-list parent mappings disagree")
    if sibling_list.pair_ids.count(pair_id) != 1:
        raise RuntimeError("selected processed pair is absent from its sibling list")

    state.metrics["boundary_pair_checks"] += 1
    return pair.pair_id


def step1_select_predecessor_boundary(state, iteration):
    """执行论文 Step 1：选择 predecessor 一侧的 family boundary pair。"""
    _require_next_iteration(state, iteration)
    previous_point_id = iteration - 1
    neighbor = state.partial_order.predecessor(previous_point_id)
    state.metrics["predecessor_accesses"] += 1
    adjusted_for_z1 = False

    if iteration % 2 == 1 and neighbor == 1:
        neighbor = state.partial_order.predecessor(1)
        state.metrics["predecessor_accesses"] += 1
        state.metrics["z1_anchor_adjustments"] += 1
        adjusted_for_z1 = True

    _record_trace(
        state,
        {
            "step": "step1_find_predecessor",
            "iteration": iteration,
            "family": pair_family_for_end_index(iteration),
            "previous_point_id": previous_point_id,
            "neighbor_point_id": _finite_neighbor_id(neighbor),
            "adjusted_for_z1": adjusted_for_z1,
        },
    )

    selection = _boundary_selection(
        state,
        iteration,
        neighbor,
        NEGATIVE_INFINITY,
        state.upper_dummy_pair_id
        if iteration % 2 == 0
        else state.lower_dummy_pair_id,
        adjusted_for_z1,
    )
    _record_boundary_pair_trace(state, "step1_select_boundary_pair", iteration, selection)
    return selection


def step2_select_successor_boundary(state, iteration):
    """执行论文 Step 2：选择 successor 一侧的 family boundary pair。"""
    _require_next_iteration(state, iteration)
    previous_point_id = iteration - 1
    neighbor = state.partial_order.successor(previous_point_id)
    state.metrics["successor_accesses"] += 1
    adjusted_for_z1 = False

    if iteration % 2 == 1 and neighbor == 1:
        neighbor = state.partial_order.successor(1)
        state.metrics["successor_accesses"] += 1
        state.metrics["z1_anchor_adjustments"] += 1
        adjusted_for_z1 = True

    _record_trace(
        state,
        {
            "step": "step2_find_successor",
            "iteration": iteration,
            "family": pair_family_for_end_index(iteration),
            "previous_point_id": previous_point_id,
            "neighbor_point_id": _finite_neighbor_id(neighbor),
            "adjusted_for_z1": adjusted_for_z1,
        },
    )

    selection = _boundary_selection(
        state,
        iteration,
        neighbor,
        POSITIVE_INFINITY,
        state.upper_dummy_pair_id
        if iteration % 2 == 0
        else state.lower_dummy_pair_id,
        adjusted_for_z1,
    )
    _record_boundary_pair_trace(state, "step2_select_boundary_pair", iteration, selection)
    return selection


def _order_first_three(points):
    partial_order = SortedOrderList()
    first, second, third = points

    if first.value < second.value:
        left = first
        right = second
    elif second.value < first.value:
        left = second
        right = first
    else:
        raise ValueError("point values must be distinct")

    partial_order.insert_after(NEGATIVE_INFINITY, left)
    partial_order.insert_after(left.paper_index, right)

    if third.value < left.value:
        partial_order.insert_before(left.paper_index, third)
    elif right.value < third.value:
        partial_order.insert_after(right.paper_index, third)
    elif left.value < third.value and third.value < right.value:
        partial_order.insert_after(left.paper_index, third)
    else:
        raise ValueError("point values must be distinct")

    return partial_order


def _boundary_selection(
    state,
    iteration,
    neighbor,
    expected_sentinel,
    dummy_pair_id,
    adjusted_for_z1,
):
    if neighbor is expected_sentinel:
        validated_dummy_pair_id = _validated_dummy_pair_id(
            state,
            iteration,
            dummy_pair_id,
        )
        return BoundarySelection(
            neighbor_point_id=None,
            pair_id=validated_dummy_pair_id,
            used_dummy_pair=True,
            adjusted_for_z1=adjusted_for_z1,
        )
    if neighbor is NEGATIVE_INFINITY or neighbor is POSITIVE_INFINITY:
        raise RuntimeError("boundary selection encountered the wrong infinity sentinel")

    pair_id = select_processed_same_family_pair(state, neighbor, iteration)
    return BoundarySelection(
        neighbor_point_id=neighbor,
        pair_id=pair_id,
        used_dummy_pair=False,
        adjusted_for_z1=adjusted_for_z1,
    )


def _validated_dummy_pair_id(state, iteration, dummy_pair_id):
    expected_family = pair_family_for_end_index(iteration)
    try:
        dummy = state.pairs[dummy_pair_id]
        backend_dummy = state.sibling_backend.get_pair(dummy_pair_id)
    except (KeyError, TypeError) as exc:
        raise RuntimeError("family dummy pair is missing from state or backend") from exc

    if backend_dummy is not dummy:
        raise RuntimeError("state and sibling backend disagree about the family dummy")
    if dummy.pair_id != dummy_pair_id or not dummy.is_dummy:
        raise RuntimeError("configured family boundary is not the expected dummy pair")
    if dummy.family != expected_family:
        raise RuntimeError("configured dummy pair belongs to the wrong family")
    if dummy.parent_pair_id is not None or dummy.sibling_list_id is not None:
        raise RuntimeError("family dummy pair cannot have ordinary ownership")
    return dummy.pair_id


def _record_boundary_pair_trace(state, step, iteration, selection):
    _record_trace(
        state,
        {
            "step": step,
            "iteration": iteration,
            "family": pair_family_for_end_index(iteration),
            "neighbor_point_id": selection.neighbor_point_id,
            "selected_pair_id": selection.pair_id,
            "used_dummy_pair": selection.used_dummy_pair,
            "adjusted_for_z1": selection.adjusted_for_z1,
        },
    )


def _record_trace(state, event):
    state.trace.append(event)
    state.metrics["trace_event_count"] += 1


def _finite_neighbor_id(neighbor):
    if neighbor is NEGATIVE_INFINITY or neighbor is POSITIVE_INFINITY:
        return None
    return neighbor


def _require_state(state):
    if not isinstance(state, PaperJordanState):
        raise TypeError("state must be a PaperJordanState")


def _require_paper_index(paper_index, n):
    if isinstance(paper_index, bool) or not isinstance(paper_index, int):
        raise TypeError("paper_index must be an integer")
    if not 1 <= paper_index <= n:
        raise IndexError("paper_index out of range")


def _require_iteration_index(iteration, n):
    if isinstance(iteration, bool) or not isinstance(iteration, int):
        raise TypeError("iteration must be an integer")
    if not 4 <= iteration <= n:
        raise ValueError("iteration must satisfy 4 <= iteration <= n")


def _require_next_iteration(state, iteration):
    _require_state(state)
    _require_iteration_index(iteration, len(state.points))
    if iteration != state.processed_count + 1:
        raise ValueError("iteration must be the next unprocessed paper index")
    if iteration in state.partial_order:
        raise RuntimeError("current iteration point is already in the partial order")
    if iteration - 1 not in state.partial_order:
        raise RuntimeError("previous point is missing from the partial order")


def _require_processed_point(state, point_id):
    _require_paper_index(point_id, len(state.points))
    if point_id > state.processed_count or point_id not in state.partial_order:
        raise ValueError("point must already belong to the processed partial order")
