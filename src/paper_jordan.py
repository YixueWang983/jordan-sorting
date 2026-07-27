"""1990 Jordan-sorting 论文算法的初始化与 Step 1/2/3(a-b) 结构操作。"""

from __future__ import annotations

from dataclasses import dataclass

from partial_sorted_list import (
    NEGATIVE_INFINITY,
    POSITIVE_INFINITY,
    PointRef,
    SortedOrderList,
)
from sibling_list_backend import (
    AFTER,
    BEFORE,
    LEFT,
    LOWER,
    RIGHT,
    UPPER,
    OrdinarySiblingListBackend,
    PairRecord,
)


UPPER_DUMMY_PAIR_ID = -1
LOWER_DUMMY_PAIR_ID = -2
INCREASING = "increasing"
DECREASING = "decreasing"
SINGLETON_LIST = "singleton_list"
BOUNDARY_INSERTION = "boundary_insertion"

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


@dataclass(frozen=True)
class Step3AResult:
    """Step 3(a) 创建并插入新 pair 后的结构结果。"""

    pair_id: int
    orientation: str
    insertion_mode: str
    boundary_pair_id: int
    parent_pair_id: int
    sibling_list_id: int


@dataclass(frozen=True)
class Step3BResult:
    """Step 3(b) 的 split/skip 结果，不包含 Step 3(c) 输出插入。"""

    performed: bool
    pair_id: int
    orientation: str
    boundary_pair_id: int
    input_list_id: int | None
    left_list_id: int | None
    right_list_id: int | None
    acquired_side: str | None
    reason: str | None


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

    candidate_end_index = _same_family_end_index(state, point_id, iteration)
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
    _validated_live_finite_pair(state, pair_id)

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


def pair_encloses_point(state, pair_id, point_id):
    """判断 finite pair 是否严格包围 processed point；dummy 始终包围。"""
    _require_state(state)
    _require_processed_point(state, point_id)
    pair = _validated_state_backend_pair(state, pair_id)
    if pair.is_dummy:
        return True

    first_value = state.point_value(pair.first_point_id)
    second_value = state.point_value(pair.second_point_id)
    point_value = state.point_value(point_id)
    left_value = first_value if first_value < second_value else second_value
    right_value = second_value if first_value < second_value else first_value
    return left_value < point_value and point_value < right_value


def step3a_increasing(state, iteration, left_boundary):
    """执行 increasing Step 3(a)，但不插入输出点。"""
    return _step3a(
        state,
        iteration,
        left_boundary,
        orientation=INCREASING,
        insertion_side=AFTER,
        boundary_trace_step="step1_select_boundary_pair",
    )


def step3a_decreasing(state, iteration, right_boundary):
    """执行 decreasing Step 3(a)，但不插入输出点。"""
    return _step3a(
        state,
        iteration,
        right_boundary,
        orientation=DECREASING,
        insertion_side=BEFORE,
        boundary_trace_step="step2_select_boundary_pair",
    )


def step3b_increasing(state, iteration, new_pair_id, right_boundary):
    """执行 increasing Step 3(b)：skip 或 acquire left split side。"""
    return _step3b(
        state,
        iteration,
        new_pair_id,
        right_boundary,
        orientation=INCREASING,
        acquired_side=LEFT,
        boundary_trace_step="step2_select_boundary_pair",
    )


def step3b_decreasing(state, iteration, new_pair_id, left_boundary):
    """执行 decreasing Step 3(b)：skip 或 acquire right split side。"""
    return _step3b(
        state,
        iteration,
        new_pair_id,
        left_boundary,
        orientation=DECREASING,
        acquired_side=RIGHT,
        boundary_trace_step="step1_select_boundary_pair",
    )


def _step3a(
    state,
    iteration,
    boundary,
    orientation,
    insertion_side,
    boundary_trace_step,
):
    _require_next_iteration(state, iteration)
    _require_orientation(state, iteration, orientation)
    _require_boundary_trace(state, boundary_trace_step, boundary, iteration)
    if iteration in state.pair_by_end_index or iteration in state.pairs:
        raise RuntimeError("Step 3(a) pair already exists for this iteration")

    boundary_pair = _validated_boundary_pair(state, boundary, iteration)
    previous_point_id = iteration - 1
    creates_singleton = pair_encloses_point(
        state,
        boundary_pair.pair_id,
        previous_point_id,
    )
    new_pair = PairRecord(
        pair_id=iteration,
        end_index=iteration,
        first_point_id=previous_point_id,
        second_point_id=iteration,
        family=pair_family_for_end_index(iteration),
    )

    state.sibling_backend.register_pair(new_pair)
    try:
        if creates_singleton:
            sibling_list_id = state.sibling_backend.make_list(
                new_pair.pair_id,
                boundary_pair.pair_id,
            )
            insertion_mode = SINGLETON_LIST
            state.metrics["sibling_lists_created"] += 1
        else:
            if boundary_pair.is_dummy:
                raise RuntimeError("dummy boundary must enclose every finite point")
            sibling_list_id = state.sibling_backend.insert_at_boundary(
                new_pair.pair_id,
                boundary_pair.pair_id,
                insertion_side,
            )
            insertion_mode = BOUNDARY_INSERTION
            state.metrics["sibling_list_insertions"] += 1
    except Exception:
        state.sibling_backend.unregister_unowned_pair(new_pair.pair_id)
        raise

    state.pairs[new_pair.pair_id] = new_pair
    state.pair_by_end_index[iteration] = new_pair.pair_id
    result = Step3AResult(
        pair_id=new_pair.pair_id,
        orientation=orientation,
        insertion_mode=insertion_mode,
        boundary_pair_id=boundary_pair.pair_id,
        parent_pair_id=new_pair.parent_pair_id,
        sibling_list_id=sibling_list_id,
    )
    _record_trace(
        state,
        {
            "step": "step3a_insert_pair",
            "iteration": iteration,
            "family": new_pair.family,
            "orientation": orientation,
            "pair_id": new_pair.pair_id,
            "boundary_pair_id": boundary_pair.pair_id,
            "insertion_mode": insertion_mode,
            "parent_pair_id": new_pair.parent_pair_id,
            "sibling_list_id": sibling_list_id,
        },
    )
    return result


def _step3b(
    state,
    iteration,
    new_pair_id,
    boundary,
    orientation,
    acquired_side,
    boundary_trace_step,
):
    _require_next_iteration(state, iteration)
    _require_orientation(state, iteration, orientation)
    _require_boundary_trace(state, boundary_trace_step, boundary, iteration)
    _require_step3a_trace(state, iteration, new_pair_id)
    _require_trace_step_absent(state, "step3b_split_sibling_list", iteration)
    new_pair = _validated_new_iteration_pair(state, iteration, new_pair_id)
    if new_pair.child_sibling_list_ids:
        raise RuntimeError("new pair already owns child sibling lists before Step 3(b)")

    boundary_pair = _validated_boundary_pair(state, boundary, iteration)
    previous_point_id = iteration - 1
    if pair_encloses_point(state, boundary_pair.pair_id, previous_point_id):
        result = Step3BResult(
            performed=False,
            pair_id=new_pair.pair_id,
            orientation=orientation,
            boundary_pair_id=boundary_pair.pair_id,
            input_list_id=None,
            left_list_id=None,
            right_list_id=None,
            acquired_side=None,
            reason="boundary pair encloses previous point",
        )
        _record_step3b_trace(state, result, input_size=0, left_size=0, right_size=0)
        return result

    if boundary_pair.is_dummy or boundary_pair.sibling_list_id is None:
        raise RuntimeError("non-enclosing Step 3(b) boundary must be a live finite pair")
    input_list = state.sibling_backend.get_list(boundary_pair.sibling_list_id)
    if orientation == INCREASING:
        if input_list.pair_ids[0] != boundary_pair.pair_id:
            raise RuntimeError("increasing Step 3(b) boundary must be first")
    elif input_list.pair_ids[-1] != boundary_pair.pair_id:
        raise RuntimeError("decreasing Step 3(b) boundary must be last")

    input_list_id = input_list.list_id
    input_size = len(input_list.pair_ids)
    split_result = state.sibling_backend.split_pairs_at_value(
        input_list_id,
        boundary_value=state.point_value(iteration),
        acquired_side=acquired_side,
        new_parent_pair_id=new_pair.pair_id,
    )
    left_size = _sibling_list_size(state, split_result.left_list_id)
    right_size = _sibling_list_size(state, split_result.right_list_id)
    moved_size = left_size if acquired_side == LEFT else right_size

    state.metrics["sibling_scan_checks"] += input_size
    state.metrics["sibling_list_splits"] += 1
    state.metrics["split_items_scanned"] += input_size
    state.metrics["split_items_moved"] += moved_size
    result = Step3BResult(
        performed=True,
        pair_id=new_pair.pair_id,
        orientation=orientation,
        boundary_pair_id=boundary_pair.pair_id,
        input_list_id=input_list_id,
        left_list_id=split_result.left_list_id,
        right_list_id=split_result.right_list_id,
        acquired_side=acquired_side,
        reason=None,
    )
    _record_step3b_trace(
        state,
        result,
        input_size=input_size,
        left_size=left_size,
        right_size=right_size,
    )
    return result


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


def _validated_boundary_pair(state, boundary, iteration):
    if not isinstance(boundary, BoundarySelection):
        raise TypeError("boundary must be a BoundarySelection")

    expected_family = pair_family_for_end_index(iteration)
    if boundary.used_dummy_pair:
        if boundary.neighbor_point_id is not None:
            raise RuntimeError("dummy boundary cannot have a finite neighbor")
        expected_dummy_id = (
            state.upper_dummy_pair_id
            if expected_family == UPPER
            else state.lower_dummy_pair_id
        )
        if boundary.pair_id != expected_dummy_id:
            raise RuntimeError("boundary uses the wrong configured family dummy")
        _validated_dummy_pair_id(state, iteration, boundary.pair_id)
        return state.pairs[boundary.pair_id]

    if boundary.neighbor_point_id is None:
        raise RuntimeError("finite boundary must identify its neighbor point")
    _require_processed_point(state, boundary.neighbor_point_id)
    expected_end_index = _same_family_end_index(
        state,
        boundary.neighbor_point_id,
        iteration,
    )
    if expected_end_index is None:
        raise RuntimeError("boundary neighbor has no processed same-family pair")
    expected_pair_id = state.pair_by_end_index.get(expected_end_index)
    if boundary.pair_id != expected_pair_id:
        raise RuntimeError("boundary pair does not match its neighbor and family")

    pair = _validated_live_finite_pair(state, boundary.pair_id)
    if pair.family != expected_family:
        raise RuntimeError("finite boundary pair belongs to the wrong family")
    if boundary.neighbor_point_id not in {
        pair.first_point_id,
        pair.second_point_id,
    }:
        raise RuntimeError("finite boundary pair does not contain its neighbor")
    return pair


def _validated_state_backend_pair(state, pair_id):
    try:
        pair = state.pairs[pair_id]
        backend_pair = state.sibling_backend.get_pair(pair_id)
    except (KeyError, TypeError) as exc:
        raise RuntimeError("pair is missing from state or sibling backend") from exc

    if backend_pair is not pair or pair.pair_id != pair_id:
        raise RuntimeError("state and sibling backend disagree about pair identity")
    return pair


def _validated_live_finite_pair(state, pair_id):
    pair = _validated_state_backend_pair(state, pair_id)
    if pair.is_dummy:
        raise RuntimeError("expected a live finite pair, received a dummy")
    if pair.parent_pair_id is None or pair.sibling_list_id is None:
        raise RuntimeError("finite pair has no live sibling-list ownership")

    sibling_list = state.sibling_backend.get_list(pair.sibling_list_id)
    if sibling_list.list_id != pair.sibling_list_id:
        raise RuntimeError("finite pair and sibling-list IDs disagree")
    if sibling_list.owner_parent_pair_id != pair.parent_pair_id:
        raise RuntimeError("finite pair and sibling-list parent mappings disagree")
    if sibling_list.pair_ids.count(pair_id) != 1:
        raise RuntimeError("finite pair is absent from its sibling list")
    return pair


def _validated_new_iteration_pair(state, iteration, pair_id):
    if pair_id != iteration:
        raise RuntimeError("new pair ID must equal the current paper end index")
    if state.pair_by_end_index.get(iteration) != pair_id:
        raise RuntimeError("new pair is missing from the end-index mapping")

    pair = _validated_live_finite_pair(state, pair_id)
    if (
        pair.end_index != iteration
        or pair.first_point_id != iteration - 1
        or pair.second_point_id != iteration
        or pair.family != pair_family_for_end_index(iteration)
    ):
        raise RuntimeError("new iteration pair record is inconsistent")
    return pair


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


def _same_family_end_index(state, point_id, iteration):
    if point_id >= 2 and point_id % 2 == iteration % 2:
        return point_id
    if (
        point_id + 1 <= state.processed_count
        and (point_id + 1) % 2 == iteration % 2
    ):
        return point_id + 1
    return None


def _require_orientation(state, iteration, expected_orientation):
    previous_value = state.point_value(iteration - 1)
    current_value = state.point_value(iteration)
    if previous_value < current_value:
        actual_orientation = INCREASING
    elif current_value < previous_value:
        actual_orientation = DECREASING
    else:
        raise ValueError("consecutive point values must be distinct")

    if actual_orientation != expected_orientation:
        raise ValueError(
            f"iteration orientation is {actual_orientation}, not {expected_orientation}"
        )


def _require_trace_step_absent(state, step, iteration):
    if any(
        event.get("step") == step and event.get("iteration") == iteration
        for event in state.trace
    ):
        raise RuntimeError(f"{step} already completed for iteration {iteration}")


def _require_boundary_trace(state, step, boundary, iteration):
    if not isinstance(boundary, BoundarySelection):
        raise TypeError("boundary must be a BoundarySelection")

    matching_events = [
        event
        for event in state.trace
        if event.get("step") == step and event.get("iteration") == iteration
    ]
    if len(matching_events) != 1:
        raise RuntimeError(f"{step} must occur exactly once before Step 3")

    event = matching_events[0]
    expected_fields = {
        "neighbor_point_id": boundary.neighbor_point_id,
        "selected_pair_id": boundary.pair_id,
        "used_dummy_pair": boundary.used_dummy_pair,
        "adjusted_for_z1": boundary.adjusted_for_z1,
    }
    if any(event.get(name) != value for name, value in expected_fields.items()):
        raise RuntimeError("Step 3 boundary does not match its Step 1/2 trace")


def _require_step3a_trace(state, iteration, new_pair_id):
    matching_events = [
        event
        for event in state.trace
        if event.get("step") == "step3a_insert_pair"
        and event.get("iteration") == iteration
        and event.get("pair_id") == new_pair_id
    ]
    if len(matching_events) != 1:
        raise RuntimeError("Step 3(a) must complete exactly once before Step 3(b)")


def _sibling_list_size(state, list_id):
    if list_id is None:
        return 0
    return len(state.sibling_backend.get_list(list_id).pair_ids)


def _record_step3b_trace(state, result, input_size, left_size, right_size):
    _record_trace(
        state,
        {
            "step": "step3b_split_sibling_list",
            "iteration": result.pair_id,
            "family": pair_family_for_end_index(result.pair_id),
            "orientation": result.orientation,
            "pair_id": result.pair_id,
            "boundary_pair_id": result.boundary_pair_id,
            "performed": result.performed,
            "reason": result.reason,
            "input_list_id": result.input_list_id,
            "input_size": input_size,
            "left_list_id": result.left_list_id,
            "left_size": left_size,
            "right_list_id": result.right_list_id,
            "right_size": right_size,
            "acquired_side": result.acquired_side,
        },
    )


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
