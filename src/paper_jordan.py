"""1990 Jordan-sorting 论文算法的初始化与 Step 1/2/3 结构操作。"""

from __future__ import annotations

from dataclasses import dataclass

from paper_execution_policy import (
    CHECKED_MODE,
    CHECKED_POLICY,
    PaperExecutionPolicy,
    require_fixed_paper_execution_policy,
    resolve_paper_execution_policy,
)
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
    left_endpoint_id,
    right_endpoint_id,
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
    "split_items_copied",
    "split_items_transferred",
    "output_insertions",
    "z1_boundary_adjustments",
    "z1_output_anchor_adjustments",
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


@dataclass(frozen=True)
class Step3CResult:
    """Step 3(c) 选择输出 anchor 并插入当前点后的结果。"""

    pair_id: int
    orientation: str
    child_pair_id: int | None
    base_anchor_point_id: int
    output_anchor_point_id: int
    insertion_side: str
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
    execution_policy: PaperExecutionPolicy
    trace: list[dict]
    metrics: dict[str, int]
    stage_results: dict[int, dict[str, object]]

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


def initialize_paper_jordan_state(seq, execution_mode=CHECKED_MODE):
    """为 n >= 3 的输入建立前三点、P2/P3 和两棵 family 根结构。"""
    execution_policy = resolve_paper_execution_policy(execution_mode)
    return _initialize_paper_jordan_state_values(
        list(seq),
        execution_policy=execution_policy,
    )


def _initialize_paper_jordan_state_values(
    values,
    execution_policy=CHECKED_POLICY,
):
    """从已物化 values 初始化 state；调用者负责输入所有权。"""
    execution_policy = require_fixed_paper_execution_policy(execution_policy)
    if len(values) < 3:
        raise ValueError("PaperJordanState initialization requires n >= 3")

    points = tuple(
        PointRef(paper_index=index, value=value)
        for index, value in enumerate(values, start=1)
    )
    partial_order = _order_first_three(points[:3])
    point_value = lambda point_id: points[point_id - 1].value
    sibling_backend = OrdinarySiblingListBackend(
        point_value,
        execution_policy=execution_policy,
    )

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
        execution_policy=execution_policy,
        trace=[],
        metrics=metrics,
        stage_results={},
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


def validate_paper_jordan_state(state):
    """执行不依赖 oracle/全局排序的完整 correctness/debug invariant audit。"""
    _require_state(state)
    execution_policy = require_fixed_paper_execution_policy(
        state.execution_policy
    )
    if state.sibling_backend.execution_policy is not execution_policy:
        raise RuntimeError("state and backend execution policies differ")
    if not 3 <= state.processed_count <= len(state.points):
        raise RuntimeError("processed_count is outside the initialized point range")
    if set(state.metrics) != set(METRIC_NAMES):
        raise RuntimeError("metric fields do not match the paper-state contract")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in state.metrics.values()
    ):
        raise RuntimeError("paper-state metrics must be non-negative integers")
    _validate_point_records(state)

    state.partial_order.validate_links()

    expected_point_ids = set(range(1, state.processed_count + 1))
    actual_point_ids = state.partial_order.to_point_ids()
    if len(actual_point_ids) != state.processed_count:
        raise RuntimeError("partial-order size does not match processed_count")
    if set(actual_point_ids) != expected_point_ids:
        raise RuntimeError("partial order does not contain exactly the processed points")

    expected_end_indices = set(range(2, state.processed_count + 1))
    expected_pair_ids = {
        state.upper_dummy_pair_id,
        state.lower_dummy_pair_id,
        *expected_end_indices,
    }
    if state.upper_dummy_pair_id != UPPER_DUMMY_PAIR_ID:
        raise RuntimeError("upper dummy pair ID does not match the state contract")
    if state.lower_dummy_pair_id != LOWER_DUMMY_PAIR_ID:
        raise RuntimeError("lower dummy pair ID does not match the state contract")
    if set(state.pairs) != expected_pair_ids:
        raise RuntimeError("state pair mapping does not match the processed prefix")
    if set(state.sibling_backend.registered_pair_ids()) != expected_pair_ids:
        raise RuntimeError("backend pair registry does not match the state mapping")

    _validate_configured_dummy(state, state.upper_dummy_pair_id, UPPER)
    _validate_configured_dummy(state, state.lower_dummy_pair_id, LOWER)

    if set(state.pair_by_end_index) != expected_end_indices:
        raise RuntimeError("pair end-index mapping does not match processed prefix")
    if len(set(state.pair_by_end_index.values())) != len(expected_end_indices):
        raise RuntimeError("multiple processed indices map to the same pair")
    for end_index in expected_end_indices:
        pair_id = state.pair_by_end_index[end_index]
        if pair_id != end_index:
            raise RuntimeError("finite pair ID must equal its end index")
        pair = _validated_live_finite_pair(state, pair_id)
        if state.pairs.get(pair_id) is not pair:
            raise RuntimeError("pair mapping key does not match its pair object")
        if (
            pair.pair_id != pair_id
            or pair.end_index != end_index
            or pair.first_point_id != end_index - 1
            or pair.second_point_id != end_index
            or pair.family != pair_family_for_end_index(end_index)
        ):
            raise RuntimeError("processed pair record is inconsistent")

    state.sibling_backend.validate_invariants()
    derived_metrics = _validate_stage_results_and_trace(state, actual_point_ids)
    for metric_name, expected_value in derived_metrics.items():
        if state.metrics[metric_name] != expected_value:
            raise RuntimeError(f"metric does not match validated trace: {metric_name}")
    _validate_state_against_deterministic_replay(state)

    state.metrics["invariant_checks"] += 1
    return True


def _validate_point_records(state):
    if not isinstance(state.points, tuple) or len(state.points) < 3:
        raise RuntimeError("state points must be an initialized tuple")
    for paper_index, point in enumerate(state.points, start=1):
        if not isinstance(point, PointRef) or point.paper_index != paper_index:
            raise RuntimeError("point records do not match one-based paper indices")
        try:
            backend_value = state.sibling_backend.point_value(paper_index)
        except (IndexError, KeyError, TypeError) as exc:
            raise RuntimeError("backend point-value source is incomplete") from exc
        if point.value != backend_value:
            raise RuntimeError("state and backend point values differ")
        if paper_index <= state.processed_count:
            try:
                ordered_point = state.partial_order.get_point(paper_index)
            except KeyError as exc:
                raise RuntimeError("processed point is missing from partial order") from exc
            if ordered_point is not point:
                raise RuntimeError(
                    "partial order and state points do not share PointRef identity"
                )


def _validate_configured_dummy(state, dummy_pair_id, expected_family):
    try:
        dummy = state.pairs[dummy_pair_id]
        backend_dummy = state.sibling_backend.get_pair(dummy_pair_id)
    except (KeyError, TypeError) as exc:
        raise RuntimeError("configured family dummy is missing") from exc
    if backend_dummy is not dummy:
        raise RuntimeError("state and backend dummy identities differ")
    if (
        dummy.pair_id != dummy_pair_id
        or not dummy.is_dummy
        or dummy.family != expected_family
        or dummy.end_index is not None
        or dummy.first_point_id is not None
        or dummy.second_point_id is not None
        or dummy.parent_pair_id is not None
        or dummy.sibling_list_id is not None
    ):
        raise RuntimeError("configured family dummy record is inconsistent")


def _validate_stage_results_and_trace(state, final_point_order):
    expected_iterations = tuple(range(4, state.processed_count + 1))
    if set(state.stage_results) != set(expected_iterations):
        raise RuntimeError("stage-result iterations do not match processed prefix")

    expected_trace_length = 2 + 7 * len(expected_iterations)
    if len(state.trace) != expected_trace_length:
        raise RuntimeError("trace length does not match completed iterations")
    if state.metrics["trace_event_count"] != expected_trace_length:
        raise RuntimeError("trace counter does not match recorded events")

    expected_initial_trace = (
        {
            "step": "initialize_partial_order",
            "processed_count": 3,
            "point_ids": [
                point_id for point_id in final_point_order if point_id <= 3
            ],
        },
        {
            "step": "initialize_pair_families",
            "upper_pair_id": 2,
            "lower_pair_id": 3,
            "upper_list_id": 1,
            "lower_list_id": 2,
        },
    )
    if tuple(state.trace[:2]) != expected_initial_trace:
        raise RuntimeError("initialization trace payload or order is inconsistent")

    derived_metrics = {
        name: 0
        for name in METRIC_NAMES
        if name != "invariant_checks"
    }
    derived_metrics["trace_event_count"] = expected_trace_length

    for offset, iteration in enumerate(expected_iterations):
        stages = state.stage_results[iteration]
        expected_stage_names = {
            "step1_select_boundary_pair",
            "step2_select_boundary_pair",
            "step3a_insert_pair",
            "step3b_split_sibling_list",
            "step3c_insert_output_point",
        }
        if set(stages) != expected_stage_names:
            raise RuntimeError("completed iteration has incomplete stage results")

        events = state.trace[2 + offset * 7 : 2 + (offset + 1) * 7]
        _validate_iteration_records(
            state,
            iteration,
            stages,
            events,
            final_point_order,
            derived_metrics,
        )

    return derived_metrics


def _validate_iteration_records(
    state,
    iteration,
    stages,
    events,
    final_point_order,
    derived_metrics,
):
    family = pair_family_for_end_index(iteration)
    orientation = _orientation_for_iteration(state, iteration)
    left_selection = stages["step1_select_boundary_pair"]
    right_selection = stages["step2_select_boundary_pair"]
    expected_left = _expected_boundary_selection(
        state,
        iteration,
        final_point_order,
        predecessor_side=True,
    )
    expected_right = _expected_boundary_selection(
        state,
        iteration,
        final_point_order,
        predecessor_side=False,
    )
    if (
        not isinstance(left_selection, BoundarySelection)
        or left_selection != expected_left
    ):
        raise RuntimeError("Step 1 boundary stage result is inconsistent")
    if (
        not isinstance(right_selection, BoundarySelection)
        or right_selection != expected_right
    ):
        raise RuntimeError("Step 2 boundary stage result is inconsistent")

    expected_prefix_events = (
        {
            "step": "step1_find_predecessor",
            "iteration": iteration,
            "family": family,
            "previous_point_id": iteration - 1,
            "neighbor_point_id": left_selection.neighbor_point_id,
            "adjusted_for_z1": left_selection.adjusted_for_z1,
        },
        _boundary_trace_event(
            "step1_select_boundary_pair",
            iteration,
            family,
            left_selection,
        ),
        {
            "step": "step2_find_successor",
            "iteration": iteration,
            "family": family,
            "previous_point_id": iteration - 1,
            "neighbor_point_id": right_selection.neighbor_point_id,
            "adjusted_for_z1": right_selection.adjusted_for_z1,
        },
        _boundary_trace_event(
            "step2_select_boundary_pair",
            iteration,
            family,
            right_selection,
        ),
    )
    if tuple(events[:4]) != expected_prefix_events:
        raise RuntimeError("Step 1/2 trace payload or order is inconsistent")

    step3a = stages["step3a_insert_pair"]
    _validate_step3a_result(
        state,
        iteration,
        orientation,
        left_selection,
        right_selection,
        step3a,
    )
    expected_step3a_event = {
        "step": "step3a_insert_pair",
        "iteration": iteration,
        "family": family,
        "orientation": step3a.orientation,
        "pair_id": step3a.pair_id,
        "boundary_pair_id": step3a.boundary_pair_id,
        "insertion_mode": step3a.insertion_mode,
        "parent_pair_id": step3a.parent_pair_id,
        "sibling_list_id": step3a.sibling_list_id,
    }
    if events[4] != expected_step3a_event:
        raise RuntimeError("Step 3(a) trace payload or order is inconsistent")

    step3b = stages["step3b_split_sibling_list"]
    opposite_boundary = (
        right_selection if orientation == INCREASING else left_selection
    )
    _validate_step3b_result(
        state,
        iteration,
        orientation,
        opposite_boundary,
        step3b,
    )
    split_sizes = _validate_step3b_trace(
        iteration,
        family,
        step3b,
        events[5],
    )

    step3c = stages["step3c_insert_output_point"]
    _validate_step3c_result(
        state,
        iteration,
        orientation,
        step3c,
        final_point_order,
    )
    expected_step3c_event = {
        "step": "step3c_insert_output_point",
        "iteration": iteration,
        "family": family,
        "orientation": step3c.orientation,
        "pair_id": step3c.pair_id,
        "child_pair_id": step3c.child_pair_id,
        "base_anchor_point_id": step3c.base_anchor_point_id,
        "output_anchor_point_id": step3c.output_anchor_point_id,
        "insertion_side": step3c.insertion_side,
        "adjusted_for_z1": step3c.adjusted_for_z1,
        "processed_count": iteration,
    }
    if events[6] != expected_step3c_event:
        raise RuntimeError("Step 3(c) trace payload or order is inconsistent")

    derived_metrics["predecessor_accesses"] += (
        1 + left_selection.adjusted_for_z1
    )
    derived_metrics["successor_accesses"] += (
        1 + right_selection.adjusted_for_z1
    )
    derived_metrics["boundary_pair_checks"] += (
        int(not left_selection.used_dummy_pair)
        + int(not right_selection.used_dummy_pair)
    )
    derived_metrics["z1_boundary_adjustments"] += (
        int(left_selection.adjusted_for_z1)
        + int(right_selection.adjusted_for_z1)
    )
    if step3a.insertion_mode == SINGLETON_LIST:
        derived_metrics["sibling_lists_created"] += 1
    else:
        derived_metrics["sibling_list_insertions"] += 1

    input_size, left_size, right_size = split_sizes
    if step3b.performed:
        derived_metrics["sibling_scan_checks"] += input_size
        derived_metrics["sibling_list_splits"] += 1
        derived_metrics["split_items_scanned"] += input_size
        derived_metrics["split_items_copied"] += input_size
        transferred_size = (
            left_size if step3b.acquired_side == LEFT else right_size
        )
        derived_metrics["split_items_transferred"] += transferred_size

    derived_metrics["output_insertions"] += 1
    derived_metrics["z1_output_anchor_adjustments"] += int(
        step3c.adjusted_for_z1
    )


def _expected_boundary_selection(
    state,
    iteration,
    final_point_order,
    predecessor_side,
):
    prefix_order = [
        point_id for point_id in final_point_order if point_id < iteration
    ]
    previous_point_id = iteration - 1
    previous_position = prefix_order.index(previous_point_id)
    neighbor_position = (
        previous_position - 1
        if predecessor_side
        else previous_position + 1
    )
    neighbor_point_id = (
        prefix_order[neighbor_position]
        if 0 <= neighbor_position < len(prefix_order)
        else None
    )
    adjusted_for_z1 = iteration % 2 == 1 and neighbor_point_id == 1
    if adjusted_for_z1:
        first_position = prefix_order.index(1)
        neighbor_position = (
            first_position - 1
            if predecessor_side
            else first_position + 1
        )
        neighbor_point_id = (
            prefix_order[neighbor_position]
            if 0 <= neighbor_position < len(prefix_order)
            else None
        )

    if neighbor_point_id is None:
        pair_id = (
            state.upper_dummy_pair_id
            if iteration % 2 == 0
            else state.lower_dummy_pair_id
        )
        return BoundarySelection(None, pair_id, True, adjusted_for_z1)

    candidate_end_index = None
    if neighbor_point_id >= 2 and neighbor_point_id % 2 == iteration % 2:
        candidate_end_index = neighbor_point_id
    elif (
        neighbor_point_id + 1 <= iteration - 1
        and (neighbor_point_id + 1) % 2 == iteration % 2
    ):
        candidate_end_index = neighbor_point_id + 1
    if candidate_end_index is None:
        raise RuntimeError("trace neighbor has no processed same-family pair")

    try:
        pair_id = state.pair_by_end_index[candidate_end_index]
    except KeyError as exc:
        raise RuntimeError("trace neighbor pair is missing") from exc
    return BoundarySelection(neighbor_point_id, pair_id, False, adjusted_for_z1)


def _boundary_trace_event(step, iteration, family, selection):
    return {
        "step": step,
        "iteration": iteration,
        "family": family,
        "neighbor_point_id": selection.neighbor_point_id,
        "selected_pair_id": selection.pair_id,
        "used_dummy_pair": selection.used_dummy_pair,
        "adjusted_for_z1": selection.adjusted_for_z1,
    }


def _orientation_for_iteration(state, iteration):
    previous_value = state.point_value(iteration - 1)
    current_value = state.point_value(iteration)
    if previous_value < current_value:
        return INCREASING
    if current_value < previous_value:
        return DECREASING
    raise RuntimeError("processed iteration contains duplicate consecutive values")


def _validate_step3a_result(
    state,
    iteration,
    orientation,
    left_selection,
    right_selection,
    result,
):
    if not isinstance(result, Step3AResult):
        raise RuntimeError("Step 3(a) stage result has the wrong type")
    expected_boundary = (
        left_selection if orientation == INCREASING else right_selection
    )
    expected_mode = (
        SINGLETON_LIST
        if pair_encloses_point(state, expected_boundary.pair_id, iteration - 1)
        else BOUNDARY_INSERTION
    )
    if (
        result.pair_id != iteration
        or result.orientation != orientation
        or result.boundary_pair_id != expected_boundary.pair_id
        or result.insertion_mode != expected_mode
        or not _is_integer_id(result.parent_pair_id)
        or not _is_positive_integer(result.sibling_list_id)
    ):
        raise RuntimeError("Step 3(a) stage result is inconsistent")
    if expected_mode == SINGLETON_LIST and (
        result.parent_pair_id != expected_boundary.pair_id
    ):
        raise RuntimeError("Step 3(a) singleton parent is inconsistent")


def _validate_step3b_result(
    state,
    iteration,
    orientation,
    boundary,
    result,
):
    if not isinstance(result, Step3BResult):
        raise RuntimeError("Step 3(b) stage result has the wrong type")
    expected_performed = not pair_encloses_point(
        state,
        boundary.pair_id,
        iteration - 1,
    )
    expected_acquired_side = LEFT if orientation == INCREASING else RIGHT
    if (
        result.pair_id != iteration
        or result.orientation != orientation
        or result.boundary_pair_id != boundary.pair_id
        or result.performed != expected_performed
    ):
        raise RuntimeError("Step 3(b) stage result is inconsistent")

    if not expected_performed:
        if (
            result.input_list_id is not None
            or result.left_list_id is not None
            or result.right_list_id is not None
            or result.acquired_side is not None
            or result.reason != "boundary pair encloses previous point"
        ):
            raise RuntimeError("skipped Step 3(b) stage payload is inconsistent")
        return

    if (
        not _is_positive_integer(result.input_list_id)
        or result.acquired_side != expected_acquired_side
        or result.reason is not None
        or (
            result.left_list_id is not None
            and not _is_positive_integer(result.left_list_id)
        )
        or (
            result.right_list_id is not None
            and not _is_positive_integer(result.right_list_id)
        )
        or (
            result.left_list_id is None
            and result.right_list_id is None
        )
    ):
        raise RuntimeError("performed Step 3(b) stage payload is inconsistent")


def _validate_step3b_trace(iteration, family, result, event):
    expected_keys = {
        "step",
        "iteration",
        "family",
        "orientation",
        "pair_id",
        "boundary_pair_id",
        "performed",
        "reason",
        "input_list_id",
        "input_size",
        "left_list_id",
        "left_size",
        "right_list_id",
        "right_size",
        "acquired_side",
    }
    if not isinstance(event, dict) or set(event) != expected_keys:
        raise RuntimeError("Step 3(b) trace fields are inconsistent")
    input_size = event["input_size"]
    left_size = event["left_size"]
    right_size = event["right_size"]
    if not all(
        isinstance(size, int) and not isinstance(size, bool) and size >= 0
        for size in (input_size, left_size, right_size)
    ):
        raise RuntimeError("Step 3(b) trace sizes must be non-negative integers")

    expected_event = {
        "step": "step3b_split_sibling_list",
        "iteration": iteration,
        "family": family,
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
    }
    if event != expected_event:
        raise RuntimeError("Step 3(b) trace payload or order is inconsistent")

    if result.performed:
        if (
            input_size < 1
            or left_size + right_size != input_size
            or (result.left_list_id is None) != (left_size == 0)
            or (result.right_list_id is None) != (right_size == 0)
        ):
            raise RuntimeError("performed Step 3(b) trace sizes are inconsistent")
    elif input_size != 0 or left_size != 0 or right_size != 0:
        raise RuntimeError("skipped Step 3(b) trace sizes must be zero")
    return input_size, left_size, right_size


def _validate_step3c_result(
    state,
    iteration,
    orientation,
    result,
    final_point_order,
):
    if not isinstance(result, Step3CResult):
        raise RuntimeError("Step 3(c) stage result has the wrong type")
    expected_side = AFTER if orientation == INCREASING else BEFORE
    if (
        result.pair_id != iteration
        or result.orientation != orientation
        or result.insertion_side != expected_side
    ):
        raise RuntimeError("Step 3(c) stage result is inconsistent")

    if result.child_pair_id is None:
        expected_base_anchor = iteration - 1
    else:
        child_pair = _validated_live_finite_pair(state, result.child_pair_id)
        if child_pair.end_index >= iteration:
            raise RuntimeError("Step 3(c) child must precede the current pair")
        expected_base_anchor = (
            right_endpoint_id(child_pair, state.point_value)
            if orientation == INCREASING
            else left_endpoint_id(child_pair, state.point_value)
        )
    if result.base_anchor_point_id != expected_base_anchor:
        raise RuntimeError("Step 3(c) base anchor is inconsistent")

    base_value = state.point_value(result.base_anchor_point_id)
    first_value = state.point_value(1)
    current_value = state.point_value(iteration)
    expected_adjustment = iteration % 2 == 1 and (
        base_value < first_value < current_value
        if orientation == INCREASING
        else current_value < first_value < base_value
    )
    expected_output_anchor = 1 if expected_adjustment else expected_base_anchor
    if (
        result.adjusted_for_z1 != expected_adjustment
        or result.output_anchor_point_id != expected_output_anchor
    ):
        raise RuntimeError("Step 3(c) output anchor is inconsistent")

    prefix_order = [
        point_id for point_id in final_point_order if point_id <= iteration
    ]
    current_position = prefix_order.index(iteration)
    anchor_position = prefix_order.index(result.output_anchor_point_id)
    if orientation == INCREASING:
        is_adjacent = current_position == anchor_position + 1
    else:
        is_adjacent = anchor_position == current_position + 1
    if not is_adjacent:
        raise RuntimeError("Step 3(c) output insertion is not adjacent to its anchor")


def _is_integer_id(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_positive_integer(value):
    return _is_integer_id(value) and value > 0


def _validate_state_against_deterministic_replay(state):
    replayed = _run_paper_jordan_state_values(
        [point.value for point in state.points],
        stop_after=state.processed_count,
        execution_policy=state.execution_policy,
    )
    actual_metrics = {
        name: value
        for name, value in state.metrics.items()
        if name != "invariant_checks"
    }
    replayed_metrics = {
        name: value
        for name, value in replayed.metrics.items()
        if name != "invariant_checks"
    }
    comparisons = (
        (
            state.partial_order.to_point_ids(),
            replayed.partial_order.to_point_ids(),
            "partial order",
        ),
        (
            state.pair_by_end_index,
            replayed.pair_by_end_index,
            "pair end-index mapping",
        ),
        (state.stage_results, replayed.stage_results, "stage results"),
        (state.trace, replayed.trace, "trace"),
        (actual_metrics, replayed_metrics, "operation metrics"),
        (
            state.sibling_backend.audit_snapshot(),
            replayed.sibling_backend.audit_snapshot(),
            "sibling backend",
        ),
    )
    for actual, expected, label in comparisons:
        if actual != expected:
            raise RuntimeError(
                f"state does not match deterministic replay: {label}"
            )


def _run_paper_jordan_state_values(
    values,
    stop_after=None,
    invariant_callback=None,
    execution_policy=CHECKED_POLICY,
):
    """使用唯一 Step 1/2/3 控制流运行已物化 valid-input values。"""
    execution_policy = require_fixed_paper_execution_policy(execution_policy)
    if not isinstance(values, list):
        raise TypeError("values must be a materialized list")
    if len(values) < 3:
        raise ValueError("paper runner requires at least three values")
    if stop_after is None:
        stop_after = len(values)
    if (
        isinstance(stop_after, bool)
        or not isinstance(stop_after, int)
        or not 3 <= stop_after <= len(values)
    ):
        raise ValueError("stop_after must satisfy 3 <= stop_after <= len(values)")
    if invariant_callback is not None and not callable(invariant_callback):
        raise TypeError("invariant_callback must be callable")

    state = _initialize_paper_jordan_state_values(
        values,
        execution_policy=execution_policy,
    )
    if invariant_callback is not None:
        invariant_callback(state)

    for iteration in range(4, stop_after + 1):
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
    _require_stage_absent(state, "step1_select_boundary_pair", iteration)
    previous_point_id = iteration - 1
    neighbor = state.partial_order.predecessor(previous_point_id)
    state.metrics["predecessor_accesses"] += 1
    adjusted_for_z1 = False

    if iteration % 2 == 1 and neighbor == 1:
        neighbor = state.partial_order.predecessor(1)
        state.metrics["predecessor_accesses"] += 1
        state.metrics["z1_boundary_adjustments"] += 1
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
    _record_stage_result(state, "step1_select_boundary_pair", iteration, selection)
    return selection


def step2_select_successor_boundary(state, iteration):
    """执行论文 Step 2：选择 successor 一侧的 family boundary pair。"""
    _require_next_iteration(state, iteration)
    _require_stage_absent(state, "step2_select_boundary_pair", iteration)
    previous_point_id = iteration - 1
    neighbor = state.partial_order.successor(previous_point_id)
    state.metrics["successor_accesses"] += 1
    adjusted_for_z1 = False

    if iteration % 2 == 1 and neighbor == 1:
        neighbor = state.partial_order.successor(1)
        state.metrics["successor_accesses"] += 1
        state.metrics["z1_boundary_adjustments"] += 1
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
    _record_stage_result(state, "step2_select_boundary_pair", iteration, selection)
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


def step3c_increasing(state, iteration, new_pair_id):
    """执行 increasing Step 3(c)：在输出 anchor 后插入 z_i。"""
    return _step3c(
        state,
        iteration,
        new_pair_id,
        orientation=INCREASING,
        insertion_side=AFTER,
    )


def step3c_decreasing(state, iteration, new_pair_id):
    """执行 decreasing Step 3(c)：在输出 anchor 前插入 z_i。"""
    return _step3c(
        state,
        iteration,
        new_pair_id,
        orientation=DECREASING,
        insertion_side=BEFORE,
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
    _require_boundary_stage(state, boundary_trace_step, boundary, iteration)
    _require_stage_absent(state, "step3a_insert_pair", iteration)
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
    _record_stage_result(state, "step3a_insert_pair", iteration, result)
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
    _require_boundary_stage(state, boundary_trace_step, boundary, iteration)
    _require_step3a_stage(state, iteration, new_pair_id)
    _require_stage_absent(state, "step3b_split_sibling_list", iteration)
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
        _record_stage_result(state, "step3b_split_sibling_list", iteration, result)
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
    transferred_size = left_size if acquired_side == LEFT else right_size

    state.metrics["sibling_scan_checks"] += input_size
    state.metrics["sibling_list_splits"] += 1
    state.metrics["split_items_scanned"] += input_size
    state.metrics["split_items_copied"] += input_size
    state.metrics["split_items_transferred"] += transferred_size
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
    _record_stage_result(state, "step3b_split_sibling_list", iteration, result)
    return result


def _step3c(state, iteration, new_pair_id, orientation, insertion_side):
    _require_state(state)
    _require_iteration_index(iteration, len(state.points))
    _require_stage_absent(state, "step3c_insert_output_point", iteration)
    _require_next_iteration(state, iteration)
    _require_orientation(state, iteration, orientation)
    _require_step3a_stage(state, iteration, new_pair_id)
    _require_step3b_stage(state, iteration, new_pair_id, orientation)

    new_pair = _validated_new_iteration_pair(state, iteration, new_pair_id)
    child_pair_id, base_anchor_point_id = _step3c_base_anchor(
        state,
        new_pair,
        orientation,
    )
    output_anchor_point_id = base_anchor_point_id
    adjusted_for_z1 = False

    if iteration % 2 == 1:
        base_value = state.point_value(base_anchor_point_id)
        first_value = state.point_value(1)
        current_value = state.point_value(iteration)
        if orientation == INCREASING:
            adjusted_for_z1 = base_value < first_value < current_value
        else:
            adjusted_for_z1 = current_value < first_value < base_value
        if adjusted_for_z1:
            output_anchor_point_id = 1

    current_point = state.point(iteration)
    if insertion_side == AFTER:
        state.partial_order.insert_after(output_anchor_point_id, current_point)
    else:
        state.partial_order.insert_before(output_anchor_point_id, current_point)

    result = Step3CResult(
        pair_id=new_pair.pair_id,
        orientation=orientation,
        child_pair_id=child_pair_id,
        base_anchor_point_id=base_anchor_point_id,
        output_anchor_point_id=output_anchor_point_id,
        insertion_side=insertion_side,
        adjusted_for_z1=adjusted_for_z1,
    )
    state.processed_count = iteration
    state.metrics["output_insertions"] += 1
    if adjusted_for_z1:
        state.metrics["z1_output_anchor_adjustments"] += 1
    _record_trace(
        state,
        {
            "step": "step3c_insert_output_point",
            "iteration": iteration,
            "family": new_pair.family,
            "orientation": orientation,
            "pair_id": new_pair.pair_id,
            "child_pair_id": child_pair_id,
            "base_anchor_point_id": base_anchor_point_id,
            "output_anchor_point_id": output_anchor_point_id,
            "insertion_side": insertion_side,
            "adjusted_for_z1": adjusted_for_z1,
            "processed_count": state.processed_count,
        },
    )
    _record_stage_result(state, "step3c_insert_output_point", iteration, result)
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


def _require_stage_absent(state, step, iteration):
    if step in state.stage_results.get(iteration, {}):
        raise RuntimeError(f"{step} already completed for iteration {iteration}")


def _require_boundary_stage(state, step, boundary, iteration):
    if not isinstance(boundary, BoundarySelection):
        raise TypeError("boundary must be a BoundarySelection")

    recorded = state.stage_results.get(iteration, {}).get(step)
    if recorded is None:
        raise RuntimeError(f"{step} must complete before Step 3")
    if recorded != boundary:
        raise RuntimeError("Step 3 boundary does not match its Step 1/2 result")


def _require_step3a_stage(state, iteration, new_pair_id):
    recorded = state.stage_results.get(iteration, {}).get("step3a_insert_pair")
    if not isinstance(recorded, Step3AResult) or recorded.pair_id != new_pair_id:
        raise RuntimeError("Step 3(a) must complete before Step 3(b)")


def _require_step3b_stage(state, iteration, new_pair_id, orientation):
    recorded = state.stage_results.get(iteration, {}).get(
        "step3b_split_sibling_list"
    )
    if (
        not isinstance(recorded, Step3BResult)
        or recorded.pair_id != new_pair_id
        or recorded.orientation != orientation
    ):
        raise RuntimeError("matching Step 3(b) must complete before Step 3(c)")


def _step3c_base_anchor(state, new_pair, orientation):
    child_list_ids = new_pair.child_sibling_list_ids
    if not child_list_ids:
        return None, new_pair.first_point_id

    if orientation == INCREASING:
        child_list_id = child_list_ids[-1]
    else:
        child_list_id = child_list_ids[0]

    child_list = state.sibling_backend.get_list(child_list_id)
    if child_list.owner_parent_pair_id != new_pair.pair_id:
        raise RuntimeError("Step 3(c) child list has the wrong owner")
    if not child_list.pair_ids:
        raise RuntimeError("Step 3(c) child sibling list cannot be empty")

    child_pair_id = (
        child_list.pair_ids[-1]
        if orientation == INCREASING
        else child_list.pair_ids[0]
    )
    child_pair = _validated_live_finite_pair(state, child_pair_id)
    if child_pair.parent_pair_id != new_pair.pair_id:
        raise RuntimeError("Step 3(c) extreme child has the wrong parent")

    if orientation == INCREASING:
        anchor_point_id = right_endpoint_id(child_pair, state.point_value)
    else:
        anchor_point_id = left_endpoint_id(child_pair, state.point_value)
    _require_processed_point(state, anchor_point_id)
    return child_pair.pair_id, anchor_point_id


def _record_stage_result(state, step, iteration, result):
    stages = state.stage_results.setdefault(iteration, {})
    if step in stages:
        raise RuntimeError(f"{step} already completed for iteration {iteration}")
    stages[step] = result


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
