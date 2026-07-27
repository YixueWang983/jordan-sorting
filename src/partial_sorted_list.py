"""1990 Jordan-sorting 算法使用的增量部分有序双向链表。"""

from __future__ import annotations

from dataclasses import dataclass


class _Sentinel:
    """用对象身份区分的链表哨兵。"""

    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


NEGATIVE_INFINITY = _Sentinel("NEGATIVE_INFINITY")
POSITIVE_INFINITY = _Sentinel("POSITIVE_INFINITY")


@dataclass(frozen=True)
class PointRef:
    """保留论文下标和原始可比较值的交点引用。"""

    paper_index: int
    value: object

    def __post_init__(self):
        if isinstance(self.paper_index, bool) or not isinstance(self.paper_index, int):
            raise TypeError("paper_index must be an integer")
        if self.paper_index < 1:
            raise ValueError("paper_index must be positive")


@dataclass(eq=False)
class _Node:
    key: object
    point: PointRef | None
    previous: _Node | None = None
    next: _Node | None = None


class SortedOrderList:
    """维护已处理点的严格递增顺序，并提供 O(1) 邻接访问和插入。"""

    def __init__(self):
        self._negative = _Node(NEGATIVE_INFINITY, None)
        self._positive = _Node(POSITIVE_INFINITY, None)
        self._negative.next = self._positive
        self._positive.previous = self._negative
        self._nodes = {}
        self._size = 0

    def __len__(self):
        return self._size

    def __contains__(self, point_id):
        return point_id in self._nodes

    def predecessor(self, point_or_sentinel):
        """返回相邻前驱的 point id；边界处返回负无穷哨兵。"""
        node = self._node_for(point_or_sentinel)
        if node.previous is None:
            raise IndexError("negative infinity has no predecessor")
        return node.previous.key

    def successor(self, point_or_sentinel):
        """返回相邻后继的 point id；边界处返回正无穷哨兵。"""
        node = self._node_for(point_or_sentinel)
        if node.next is None:
            raise IndexError("positive infinity has no successor")
        return node.next.key

    def insert_before(self, anchor_point_or_sentinel, point):
        """在 anchor 前插入 PointRef，并保持严格递增的局部顺序。"""
        anchor = self._node_for(anchor_point_or_sentinel)
        if anchor is self._negative:
            raise IndexError("cannot insert before negative infinity")
        return self._insert_between(anchor.previous, anchor, point)

    def insert_after(self, anchor_point_or_sentinel, point):
        """在 anchor 后插入 PointRef，并保持严格递增的局部顺序。"""
        anchor = self._node_for(anchor_point_or_sentinel)
        if anchor is self._positive:
            raise IndexError("cannot insert after positive infinity")
        return self._insert_between(anchor, anchor.next, point)

    def get_point(self, point_id):
        """根据论文 point id 返回不可变 PointRef。"""
        try:
            return self._nodes[point_id].point
        except KeyError as exc:
            raise KeyError(f"unknown point id: {point_id}") from exc

    def to_point_ids(self):
        """按当前 x 顺序返回 point id，不包含哨兵。"""
        return [node.point.paper_index for node in self._real_nodes()]

    def to_list(self):
        """按当前 x 顺序返回原始值，不包含哨兵。"""
        return [node.point.value for node in self._real_nodes()]

    def validate_links(self):
        """验证双向链接、映射、计数和严格递增顺序。"""
        if self._negative.previous is not None:
            raise RuntimeError("negative sentinel must not have a predecessor")
        if self._positive.next is not None:
            raise RuntimeError("positive sentinel must not have a successor")

        forward_nodes = []
        seen = set()
        node = self._negative

        while True:
            node_identity = id(node)
            if node_identity in seen:
                raise RuntimeError("cycle detected in forward links")
            seen.add(node_identity)

            if node is self._positive:
                break

            next_node = node.next
            if next_node is None or next_node.previous is not node:
                raise RuntimeError("inconsistent forward/backward link")

            node = next_node
            if node is not self._positive:
                forward_nodes.append(node)

        backward_nodes = []
        seen.clear()
        node = self._positive

        while True:
            node_identity = id(node)
            if node_identity in seen:
                raise RuntimeError("cycle detected in backward links")
            seen.add(node_identity)

            if node is self._negative:
                break

            previous_node = node.previous
            if previous_node is None or previous_node.next is not node:
                raise RuntimeError("inconsistent backward/forward link")

            node = previous_node
            if node is not self._negative:
                backward_nodes.append(node)

        if forward_nodes != list(reversed(backward_nodes)):
            raise RuntimeError("forward and backward traversals disagree")
        if len(forward_nodes) != self._size:
            raise RuntimeError("stored size does not match linked nodes")
        if set(self._nodes.values()) != set(forward_nodes):
            raise RuntimeError("point-id mapping does not match linked nodes")

        for point_id, mapped_node in self._nodes.items():
            if mapped_node.point is None or mapped_node.point.paper_index != point_id:
                raise RuntimeError("point-id mapping is inconsistent")

        for left, right in zip(forward_nodes, forward_nodes[1:]):
            if not left.point.value < right.point.value:
                raise RuntimeError("real point values are not strictly increasing")

        return True

    def _node_for(self, point_or_sentinel):
        if point_or_sentinel is NEGATIVE_INFINITY:
            return self._negative
        if point_or_sentinel is POSITIVE_INFINITY:
            return self._positive

        try:
            return self._nodes[point_or_sentinel]
        except (KeyError, TypeError) as exc:
            raise KeyError(f"unknown point or sentinel: {point_or_sentinel!r}") from exc

    def _insert_between(self, left, right, point):
        if not isinstance(point, PointRef):
            raise TypeError("point must be a PointRef")
        if point.paper_index in self._nodes:
            raise ValueError(f"duplicate point id: {point.paper_index}")
        if left is None or right is None or left.next is not right or right.previous is not left:
            raise RuntimeError("insertion anchors are not adjacent")

        if left.point is not None and not left.point.value < point.value:
            raise ValueError("point value is not greater than its left neighbor")
        if right.point is not None and not point.value < right.point.value:
            raise ValueError("point value is not less than its right neighbor")

        node = _Node(
            key=point.paper_index,
            point=point,
            previous=left,
            next=right,
        )
        left.next = node
        right.previous = node
        self._nodes[point.paper_index] = node
        self._size += 1
        return point.paper_index

    def _real_nodes(self):
        node = self._negative.next
        while node is not self._positive:
            yield node
            node = node.next
