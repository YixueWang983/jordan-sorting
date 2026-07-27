"""1990 Jordan-sorting 算法的普通 Python list sibling-list backend。"""

from __future__ import annotations

from dataclasses import dataclass, field


UPPER = "upper"
LOWER = "lower"
PAIR_FAMILIES = {UPPER, LOWER}
BEFORE = "before"
AFTER = "after"
LEFT = "left"
RIGHT = "right"


@dataclass
class PairRecord:
    """保存 curve-order 端点以及 sibling-list ownership。"""

    pair_id: int
    end_index: int | None
    first_point_id: int | None
    second_point_id: int | None
    family: str
    parent_pair_id: int | None = None
    sibling_list_id: int | None = None
    child_sibling_list_ids: list[int] = field(default_factory=list)
    is_dummy: bool = False

    def __post_init__(self):
        _require_integer_id(self.pair_id, "pair_id")
        if self.family not in PAIR_FAMILIES:
            raise ValueError("family must be 'upper' or 'lower'")

        if self.is_dummy:
            if any(
                value is not None
                for value in (
                    self.end_index,
                    self.first_point_id,
                    self.second_point_id,
                    self.parent_pair_id,
                    self.sibling_list_id,
                )
            ):
                raise ValueError("dummy pair cannot have finite endpoints or ownership")
            if self.child_sibling_list_ids:
                raise ValueError("new dummy pair cannot start with child lists")
            return

        _require_positive_integer(self.pair_id, "pair_id")
        _require_positive_integer(self.end_index, "end_index")
        if self.end_index < 2:
            raise ValueError("finite pair end_index must be at least 2")
        _require_positive_integer(self.first_point_id, "first_point_id")
        _require_positive_integer(self.second_point_id, "second_point_id")
        if self.first_point_id == self.second_point_id:
            raise ValueError("pair endpoints must be distinct")

        expected_family = UPPER if self.end_index % 2 == 0 else LOWER
        if self.family != expected_family:
            raise ValueError("pair family does not match end-index parity")
        if self.parent_pair_id is not None or self.sibling_list_id is not None:
            raise ValueError("new finite pair must start without ownership")
        if self.child_sibling_list_ids:
            raise ValueError("new finite pair cannot start with child lists")


@dataclass
class SiblingList:
    """一个 live sibling list；owner 始终存在。"""

    list_id: int
    owner_parent_pair_id: int
    pair_ids: list[int]


@dataclass(frozen=True)
class SplitPlan:
    """不修改 live state 的 sibling-list 分区计划。"""

    retired_list_id: int
    previous_owner_parent_pair_id: int
    original_pair_ids: tuple[int, ...]
    left_pair_ids: tuple[int, ...]
    right_pair_ids: tuple[int, ...]


@dataclass(frozen=True)
class SplitCommitResult:
    """原子 split 提交后左右两侧的新 list id。"""

    left_list_id: int | None
    right_list_id: int | None


def left_endpoint_id(pair, point_value):
    """返回 finite pair 的几何左端点 id。"""
    first_value, second_value = _endpoint_values(pair, point_value)
    if first_value == second_value:
        raise ValueError("pair endpoint values must be distinct")
    return pair.first_point_id if first_value < second_value else pair.second_point_id


def right_endpoint_id(pair, point_value):
    """返回 finite pair 的几何右端点 id。"""
    first_value, second_value = _endpoint_values(pair, point_value)
    if first_value == second_value:
        raise ValueError("pair endpoint values must be distinct")
    return pair.second_point_id if first_value < second_value else pair.first_point_id


class OrdinarySiblingListBackend:
    """维护 sibling lists、pair ownership 和原子 split transaction。"""

    def __init__(self, point_value):
        if not callable(point_value):
            raise TypeError("point_value must be callable")
        self._point_value = point_value
        self._pairs = {}
        self._lists = {}
        self._dummy_pair_ids = {}
        self._next_list_id = 1

    def register_pair(self, pair):
        """注册尚未进入 sibling list 的 pair。"""
        if not isinstance(pair, PairRecord):
            raise TypeError("pair must be a PairRecord")
        if pair.pair_id in self._pairs:
            raise ValueError(f"duplicate pair id: {pair.pair_id}")
        if pair.is_dummy and pair.family in self._dummy_pair_ids:
            raise ValueError(f"duplicate dummy pair for family: {pair.family}")

        self._pairs[pair.pair_id] = pair
        if pair.is_dummy:
            self._dummy_pair_ids[pair.family] = pair.pair_id
        return pair.pair_id

    def get_pair(self, pair_id):
        try:
            return self._pairs[pair_id]
        except (KeyError, TypeError) as exc:
            raise KeyError(f"unknown pair id: {pair_id}") from exc

    def registered_pair_ids(self):
        """返回当前 backend 中全部 pair ID 的不可变快照。"""
        return tuple(self._pairs)

    def audit_snapshot(self):
        """返回可用于确定性重放比较的不可变 backend 状态。"""
        pair_records = tuple(
            (
                pair_id,
                pair.pair_id,
                pair.end_index,
                pair.first_point_id,
                pair.second_point_id,
                pair.family,
                pair.parent_pair_id,
                pair.sibling_list_id,
                tuple(pair.child_sibling_list_ids),
                pair.is_dummy,
            )
            for pair_id, pair in sorted(self._pairs.items())
        )
        sibling_lists = tuple(
            (
                list_id,
                sibling_list.list_id,
                sibling_list.owner_parent_pair_id,
                tuple(sibling_list.pair_ids),
            )
            for list_id, sibling_list in sorted(self._lists.items())
        )
        return (
            pair_records,
            sibling_lists,
            tuple(sorted(self._dummy_pair_ids.items())),
            self._next_list_id,
        )

    def get_list(self, list_id):
        try:
            return self._lists[list_id]
        except (KeyError, TypeError) as exc:
            raise KeyError(f"unknown sibling-list id: {list_id}") from exc

    def unregister_unowned_pair(self, pair_id):
        """移除尚未接入 family tree 的 finite pair，用于事务回滚。"""
        pair = self.get_pair(pair_id)
        if pair.is_dummy:
            raise ValueError("dummy pair cannot be unregistered")
        if (
            pair.parent_pair_id is not None
            or pair.sibling_list_id is not None
            or pair.child_sibling_list_ids
        ):
            raise ValueError("only a completely unowned finite pair can be unregistered")

        del self._pairs[pair.pair_id]
        return pair

    def make_list(self, pair_id, owner_parent_pair_id):
        """创建 singleton list，并建立 pair/parent/list 三方 ownership。"""
        pair = self._require_unowned_finite_pair(pair_id)
        owner = self.get_pair(owner_parent_pair_id)
        self._require_same_family(pair, owner)
        self._require_live_parent(owner)

        new_list_id = self._next_list_id
        new_list = SiblingList(new_list_id, owner.pair_id, [pair.pair_id])
        staged_lists = {new_list_id: new_list}
        final_owner_lists = self._order_child_list_ids(
            [*owner.child_sibling_list_ids, new_list_id],
            staged_lists,
        )

        self._lists[new_list_id] = new_list
        self._next_list_id += 1
        pair.parent_pair_id = owner.pair_id
        pair.sibling_list_id = new_list_id
        owner.child_sibling_list_ids = final_owner_lists
        return new_list_id

    def insert_at_boundary(self, pair_id, anchor_pair_id, side):
        """在现有 sibling list 的合法首端或尾端插入新 pair。"""
        if side not in {BEFORE, AFTER}:
            raise ValueError("side must be 'before' or 'after'")

        pair = self._require_unowned_finite_pair(pair_id)
        anchor = self.get_pair(anchor_pair_id)
        if anchor.is_dummy or anchor.sibling_list_id is None:
            raise ValueError("anchor must belong to a live sibling list")

        sibling_list = self.get_list(anchor.sibling_list_id)
        if side == BEFORE and sibling_list.pair_ids[0] != anchor.pair_id:
            raise ValueError("before insertion requires the first list item")
        if side == AFTER and sibling_list.pair_ids[-1] != anchor.pair_id:
            raise ValueError("after insertion requires the last list item")

        owner = self.get_pair(sibling_list.owner_parent_pair_id)
        self._require_same_family(pair, anchor)
        self._require_same_family(pair, owner)
        self._require_live_parent(owner)

        pair_key = self._pair_left_key(pair.pair_id)
        anchor_key = self._pair_left_key(anchor.pair_id)
        if side == BEFORE and not pair_key < anchor_key:
            raise ValueError("new pair does not belong before the anchor")
        if side == AFTER and not anchor_key < pair_key:
            raise ValueError("new pair does not belong after the anchor")

        if side == BEFORE:
            final_pair_ids = [pair.pair_id, *sibling_list.pair_ids]
        else:
            final_pair_ids = [*sibling_list.pair_ids, pair.pair_id]

        sibling_list.pair_ids = final_pair_ids
        pair.parent_pair_id = owner.pair_id
        pair.sibling_list_id = sibling_list.list_id
        return sibling_list.list_id

    def split_by_key(self, list_id, boundary_key, key_function):
        """按 key <= boundary / key > boundary 生成非破坏性 SplitPlan。"""
        if not callable(key_function):
            raise TypeError("key_function must be callable")

        sibling_list = self.get_list(list_id)
        left_pair_ids = []
        right_pair_ids = []
        reached_right = False

        for pair_id in sibling_list.pair_ids:
            pair = self.get_pair(pair_id)
            key = key_function(pair)
            belongs_left = key < boundary_key or key == boundary_key

            if belongs_left:
                if reached_right:
                    raise ValueError("split key does not partition the ordered list")
                left_pair_ids.append(pair_id)
            else:
                reached_right = True
                right_pair_ids.append(pair_id)

        return SplitPlan(
            retired_list_id=sibling_list.list_id,
            previous_owner_parent_pair_id=sibling_list.owner_parent_pair_id,
            original_pair_ids=tuple(sibling_list.pair_ids),
            left_pair_ids=tuple(left_pair_ids),
            right_pair_ids=tuple(right_pair_ids),
        )

    def split_pairs_at_value(
        self,
        list_id,
        boundary_value,
        acquired_side,
        new_parent_pair_id,
    ):
        """验证 pair 不跨 boundary，然后生成并原子提交 Jordan split。"""
        sibling_list = self.get_list(list_id)

        for pair_id in sibling_list.pair_ids:
            pair = self.get_pair(pair_id)
            first_value, second_value = _endpoint_values(pair, self._point_value)
            both_left = first_value < boundary_value and second_value < boundary_value
            both_right = boundary_value < first_value and boundary_value < second_value
            if not (both_left or both_right):
                raise ValueError(f"pair {pair_id} straddles the split boundary")

        plan = self.split_by_key(
            list_id,
            boundary_value,
            lambda pair: self._pair_left_key(pair.pair_id),
        )
        return self.commit_split(plan, acquired_side, new_parent_pair_id)

    def commit_split(self, plan, acquired_side, new_parent_pair_id):
        """验证完整 final state 后，一次性发布 split ownership 变更。"""
        if not isinstance(plan, SplitPlan):
            raise TypeError("plan must be a SplitPlan")
        if acquired_side not in {LEFT, RIGHT}:
            raise ValueError("acquired_side must be 'left' or 'right'")

        retired = self.get_list(plan.retired_list_id)
        old_owner = self.get_pair(plan.previous_owner_parent_pair_id)
        new_parent = self.get_pair(new_parent_pair_id)

        self._validate_live_split_plan(plan, retired, old_owner)
        if new_parent.is_dummy:
            raise ValueError("new split parent must be a finite pair")
        if new_parent.pair_id == old_owner.pair_id:
            raise ValueError("new split parent must differ from the old owner")
        if new_parent.pair_id in plan.original_pair_ids:
            raise ValueError("new parent cannot be an item in the split input")
        self._require_same_family(old_owner, new_parent)

        acquired_ids = plan.left_pair_ids if acquired_side == LEFT else plan.right_pair_ids
        retained_ids = plan.right_pair_ids if acquired_side == LEFT else plan.left_pair_ids
        self._require_live_parent(old_owner)
        self._require_live_parent(new_parent)
        self._reject_descendant_parent(new_parent, acquired_ids)

        next_list_id = self._next_list_id
        left_list_id = next_list_id if plan.left_pair_ids else None
        if left_list_id is not None:
            next_list_id += 1
        right_list_id = next_list_id if plan.right_pair_ids else None
        if right_list_id is not None:
            next_list_id += 1

        left_owner_id = (
            new_parent.pair_id if acquired_side == LEFT else old_owner.pair_id
        )
        right_owner_id = (
            new_parent.pair_id if acquired_side == RIGHT else old_owner.pair_id
        )

        staged_lists = {}
        if left_list_id is not None:
            staged_lists[left_list_id] = SiblingList(
                left_list_id,
                left_owner_id,
                list(plan.left_pair_ids),
            )
        if right_list_id is not None:
            staged_lists[right_list_id] = SiblingList(
                right_list_id,
                right_owner_id,
                list(plan.right_pair_ids),
            )

        retained_list_id = right_list_id if acquired_side == LEFT else left_list_id
        acquired_list_id = left_list_id if acquired_side == LEFT else right_list_id

        old_owner_lists = self._replace_child_list_id(
            old_owner.child_sibling_list_ids,
            retired.list_id,
            retained_list_id,
        )
        old_owner_lists = self._order_child_list_ids(old_owner_lists, staged_lists)

        new_parent_lists = list(new_parent.child_sibling_list_ids)
        if acquired_list_id is not None:
            new_parent_lists.append(acquired_list_id)
        new_parent_lists = self._order_child_list_ids(new_parent_lists, staged_lists)

        for pair_id in acquired_ids:
            pair = self.get_pair(pair_id)
            if pair.parent_pair_id != old_owner.pair_id:
                raise ValueError("acquired pair does not belong to the old parent")
        for pair_id in retained_ids:
            pair = self.get_pair(pair_id)
            if pair.parent_pair_id != old_owner.pair_id:
                raise ValueError("retained pair does not belong to the old parent")

        old_owner_lists_before = list(old_owner.child_sibling_list_ids)
        new_parent_lists_before = list(new_parent.child_sibling_list_ids)
        pair_ownership_before = {
            pair_id: (
                self.get_pair(pair_id).parent_pair_id,
                self.get_pair(pair_id).sibling_list_id,
            )
            for pair_id in plan.original_pair_ids
        }
        next_list_id_before = self._next_list_id

        try:
            del self._lists[retired.list_id]
            self._lists.update(staged_lists)
            self._next_list_id = next_list_id
            old_owner.child_sibling_list_ids = old_owner_lists
            new_parent.child_sibling_list_ids = new_parent_lists

            for pair_id in plan.left_pair_ids:
                pair = self.get_pair(pair_id)
                pair.sibling_list_id = left_list_id
                pair.parent_pair_id = left_owner_id
            for pair_id in plan.right_pair_ids:
                pair = self.get_pair(pair_id)
                pair.sibling_list_id = right_list_id
                pair.parent_pair_id = right_owner_id

            self.validate_invariants(require_all_owned=False)
        except Exception:
            for list_id in staged_lists:
                self._lists.pop(list_id, None)
            self._lists[retired.list_id] = retired
            self._next_list_id = next_list_id_before
            old_owner.child_sibling_list_ids = old_owner_lists_before
            new_parent.child_sibling_list_ids = new_parent_lists_before
            for pair_id, (parent_id, sibling_list_id) in pair_ownership_before.items():
                pair = self.get_pair(pair_id)
                pair.parent_pair_id = parent_id
                pair.sibling_list_id = sibling_list_id
            raise

        return SplitCommitResult(left_list_id, right_list_id)

    def validate_invariants(self, require_all_owned=True):
        """执行完整 correctness/debug 验证；该全局检查不属于计时路径。"""
        pair_occurrences = {}
        list_owner_occurrences = {}

        for list_id, sibling_list in self._lists.items():
            if sibling_list.list_id != list_id:
                raise RuntimeError("sibling-list mapping is inconsistent")
            if not sibling_list.pair_ids:
                raise RuntimeError("live sibling list cannot be empty")

            owner = self.get_pair(sibling_list.owner_parent_pair_id)
            if owner.child_sibling_list_ids.count(list_id) != 1:
                raise RuntimeError("live list must occur once in its owner's children")
            list_owner_occurrences[list_id] = list_owner_occurrences.get(list_id, 0) + 1

            previous_key = None
            for index, pair_id in enumerate(sibling_list.pair_ids):
                pair = self.get_pair(pair_id)
                if pair.is_dummy:
                    raise RuntimeError("dummy pair cannot be a sibling-list item")
                if pair.family != owner.family:
                    raise RuntimeError("list item and owner families differ")
                if pair.sibling_list_id != list_id:
                    raise RuntimeError("pair sibling-list mapping is inconsistent")
                if pair.parent_pair_id != owner.pair_id:
                    raise RuntimeError("pair parent does not match list owner")

                key = self._pair_left_key(pair_id)
                if index and not previous_key < key:
                    raise RuntimeError("sibling-list pair order is not increasing")
                previous_key = key
                pair_occurrences[pair_id] = pair_occurrences.get(pair_id, 0) + 1

        for pair in self._pairs.values():
            if pair.is_dummy:
                if pair.parent_pair_id is not None or pair.sibling_list_id is not None:
                    raise RuntimeError("dummy pair cannot have ordinary ownership")
                if self._dummy_pair_ids.get(pair.family) != pair.pair_id:
                    raise RuntimeError("family dummy mapping is inconsistent")
            else:
                has_parent = pair.parent_pair_id is not None
                has_list = pair.sibling_list_id is not None
                if has_parent != has_list:
                    raise RuntimeError("finite pair has partial ownership")
                if require_all_owned and not has_parent:
                    raise RuntimeError("finite pair is not owned")
                if has_parent and pair_occurrences.get(pair.pair_id) != 1:
                    raise RuntimeError("finite pair must occur in exactly one list")
                if not has_parent and pair.child_sibling_list_ids:
                    raise RuntimeError("unowned finite pair cannot own child lists")
                if has_parent:
                    self._validate_parent_chain(pair)

            child_ids = pair.child_sibling_list_ids
            if len(child_ids) > 2 or len(child_ids) != len(set(child_ids)):
                raise RuntimeError("parent child-list IDs violate uniqueness or limit")
            if child_ids != self._order_child_list_ids(child_ids):
                raise RuntimeError("parent child-list IDs are not left-to-right ordered")
            for child_id in child_ids:
                child_list = self.get_list(child_id)
                if child_list.owner_parent_pair_id != pair.pair_id:
                    raise RuntimeError("child-list owner mapping is inconsistent")

        if set(list_owner_occurrences) != set(self._lists):
            raise RuntimeError("not every live list has exactly one owner")
        return True

    def _require_unowned_finite_pair(self, pair_id):
        pair = self.get_pair(pair_id)
        if pair.is_dummy:
            raise ValueError("dummy pair cannot be a sibling-list item")
        if pair.parent_pair_id is not None or pair.sibling_list_id is not None:
            raise ValueError("pair already has sibling-list ownership")
        return pair

    def _require_same_family(self, first, second):
        if first.family != second.family:
            raise ValueError("pairs must belong to the same family")

    def _require_live_parent(self, pair):
        if pair.is_dummy:
            if self._dummy_pair_ids.get(pair.family) != pair.pair_id:
                raise ValueError("dummy pair is not the registered family root")
            return

        if pair.parent_pair_id is None or pair.sibling_list_id is None:
            raise ValueError("finite parent must already belong to the family tree")

        sibling_list = self.get_list(pair.sibling_list_id)
        if sibling_list.pair_ids.count(pair.pair_id) != 1:
            raise ValueError("finite parent is not present in its sibling list")
        if sibling_list.owner_parent_pair_id != pair.parent_pair_id:
            raise ValueError("finite parent ownership mapping is inconsistent")

        try:
            self._validate_parent_chain(pair)
        except RuntimeError as exc:
            raise ValueError("finite parent does not reach its family dummy root") from exc

    def _validate_parent_chain(self, pair):
        expected_dummy_id = self._dummy_pair_ids.get(pair.family)
        if expected_dummy_id is None:
            raise RuntimeError("family has no registered dummy root")

        seen = set()
        current = pair

        while not current.is_dummy:
            if current.pair_id in seen:
                raise RuntimeError("cycle detected in pair parent chain")
            seen.add(current.pair_id)

            if current.parent_pair_id is None or current.sibling_list_id is None:
                raise RuntimeError("parent chain contains an unowned finite pair")

            sibling_list = self.get_list(current.sibling_list_id)
            if sibling_list.pair_ids.count(current.pair_id) != 1:
                raise RuntimeError("parent-chain pair is absent from its sibling list")
            if sibling_list.owner_parent_pair_id != current.parent_pair_id:
                raise RuntimeError("parent-chain ownership mapping is inconsistent")

            parent = self.get_pair(current.parent_pair_id)
            if parent.family != pair.family:
                raise RuntimeError("parent chain crosses pair families")
            current = parent

        if current.pair_id != expected_dummy_id:
            raise RuntimeError("parent chain reaches the wrong family dummy")

    def _reject_descendant_parent(self, new_parent, acquired_pair_ids):
        acquired_pair_ids = set(acquired_pair_ids)
        current = new_parent

        while not current.is_dummy:
            if current.pair_id in acquired_pair_ids:
                raise ValueError("new parent is a descendant of an acquired pair")
            current = self.get_pair(current.parent_pair_id)

    def _pair_left_key(self, pair_id):
        pair = self.get_pair(pair_id)
        endpoint_id = left_endpoint_id(pair, self._point_value)
        return self._point_value(endpoint_id)

    def _list_order_key(self, list_id, staged_lists=None):
        if staged_lists and list_id in staged_lists:
            sibling_list = staged_lists[list_id]
        else:
            sibling_list = self.get_list(list_id)
        return self._pair_left_key(sibling_list.pair_ids[0])

    def _order_child_list_ids(self, list_ids, staged_lists=None):
        if len(list_ids) > 2:
            raise ValueError("a parent cannot own more than two sibling lists")
        if len(list_ids) != len(set(list_ids)):
            raise ValueError("child sibling-list IDs must be unique")
        if len(list_ids) < 2:
            return list(list_ids)

        first_id, second_id = list_ids
        first_key = self._list_order_key(first_id, staged_lists)
        second_key = self._list_order_key(second_id, staged_lists)
        if first_key == second_key:
            raise ValueError("child sibling lists must have distinct order keys")
        if first_key < second_key:
            return [first_id, second_id]
        return [second_id, first_id]

    def _replace_child_list_id(self, child_ids, retired_id, replacement_id):
        if child_ids.count(retired_id) != 1:
            raise ValueError("retired list must occur exactly once under old parent")
        result = list(child_ids)
        index = result.index(retired_id)
        if replacement_id is None:
            result.pop(index)
        else:
            result[index] = replacement_id
        return result

    def _validate_live_split_plan(self, plan, retired, old_owner):
        if retired.owner_parent_pair_id != old_owner.pair_id:
            raise ValueError("split plan owner no longer matches live state")
        if tuple(retired.pair_ids) != plan.original_pair_ids:
            raise ValueError("split plan is stale")
        if plan.left_pair_ids + plan.right_pair_ids != plan.original_pair_ids:
            raise ValueError("split plan does not preserve input order and union")
        if len(set(plan.original_pair_ids)) != len(plan.original_pair_ids):
            raise ValueError("split plan contains duplicate pair IDs")
        if old_owner.child_sibling_list_ids.count(retired.list_id) != 1:
            raise ValueError("retired list is not uniquely owned")

        for pair_id in plan.original_pair_ids:
            pair = self.get_pair(pair_id)
            if pair.sibling_list_id != retired.list_id:
                raise ValueError("split pair does not belong to the retired list")
            if pair.parent_pair_id != old_owner.pair_id:
                raise ValueError("split pair does not belong to the old parent")


def _endpoint_values(pair, point_value):
    if pair.is_dummy or pair.first_point_id is None or pair.second_point_id is None:
        raise ValueError("dummy pair has no finite geometric endpoints")
    return point_value(pair.first_point_id), point_value(pair.second_point_id)


def _require_integer_id(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")


def _require_positive_integer(value, field_name):
    _require_integer_id(value, field_name)
    if value < 1:
        raise ValueError(f"{field_name} must be positive")
