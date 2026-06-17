"""Jordan 序列的 upper / lower 家族树数据结构。"""

from dataclasses import dataclass

from oracle import (
    lower_pairs,
    oracle,
    pair_to_interval,
    rank_map,
    upper_pairs,
    crosses,
)


UPPER = "upper"
LOWER = "lower"
PAIR_FAMILIES = {UPPER, LOWER}


@dataclass
class IntervalNode:
    id: int
    interval: tuple[int, int]
    pair_index: int
    parent: int | None
    children: list[int]
    depth: int


@dataclass
class FamilyTree:
    pair_family: str
    nodes: list[IntervalNode]
    roots: list[int]


def validate_pair_family(pair_family):
    """校验 family 是否为 upper 或 lower。"""
    if pair_family not in PAIR_FAMILIES:
        raise ValueError("pair_family must be 'upper' or 'lower'")


def interval_contains(outer, inner):
    """判断 inner 是否包含在 outer 内（可重合边界）。"""
    outer_left, outer_right = outer
    inner_left, inner_right = inner
    return outer_left <= inner_left and inner_right <= outer_right


def proper_interval_contains(outer, inner):
    """判断 inner 是否真包含在 outer 内（严格包含，不可重边界）。"""
    outer_left, outer_right = outer
    inner_left, inner_right = inner
    return outer_left < inner_left and inner_right < outer_right


def _normalize_interval(interval):
    if not isinstance(interval, tuple):
        raise ValueError("interval must be a tuple")

    if len(interval) != 2:
        raise ValueError("interval must have exactly two endpoints")

    left, right = interval

    if not isinstance(left, int) or not isinstance(right, int):
        raise ValueError("interval endpoints must be integers")

    if left >= right:
        raise ValueError("interval must satisfy left < right")

    return (left, right)


def _validate_direct_intervals(intervals):
    normalized = [_normalize_interval(interval) for interval in intervals]

    seen_intervals = set()
    seen_endpoints = set()

    for interval in normalized:
        if interval in seen_intervals:
            raise ValueError("duplicate interval")

        left, right = interval
        if left in seen_endpoints or right in seen_endpoints:
            raise ValueError("shared interval endpoint")

        seen_intervals.add(interval)
        seen_endpoints.add(left)
        seen_endpoints.add(right)

    for i, first in enumerate(normalized):
        for second in normalized[i + 1 :]:
            if crosses(first, second):
                raise ValueError("crossing intervals")

    return normalized


def _interval_sort_key(node):
    left, right = node.interval
    return (left, right, node.id)


def build_family_intervals(seq, pair_family):
    """从候选序列构造指定 family 的 rank interval 列表。"""
    validate_pair_family(pair_family)

    values = list(seq)
    rank = rank_map(values)

    pairs = upper_pairs(values) if pair_family == UPPER else lower_pairs(values)

    return [pair_to_interval(pair, rank) for pair in pairs]


def build_family_tree(intervals, pair_family):
    """根据 rank intervals 构造 family tree。"""
    validate_pair_family(pair_family)
    normalized = _validate_direct_intervals(intervals)

    nodes = [
        IntervalNode(
            id=index,
            interval=interval,
            pair_index=index,
            parent=None,
            children=[],
            depth=0,
        )
        for index, interval in enumerate(normalized)
    ]

    for node in nodes:
        containers = [
            candidate
            for candidate in nodes
            if candidate.id != node.id
            and proper_interval_contains(candidate.interval, node.interval)
        ]

        if containers:
            parent = min(
                containers,
                key=lambda candidate: (
                    candidate.interval[1] - candidate.interval[0],
                    candidate.interval[0],
                    candidate.interval[1],
                    candidate.pair_index,
                ),
            )
            node.parent = parent.id
            parent.children.append(node.id)

    roots = [node.id for node in nodes if node.parent is None]
    roots.sort(key=lambda node_id: _interval_sort_key(nodes[node_id]))

    for node in nodes:
        node.children.sort(key=lambda node_id: _interval_sort_key(nodes[node_id]))

    tree = FamilyTree(pair_family=pair_family, nodes=nodes, roots=roots)
    compute_depths(tree)
    return tree


def compute_depths(tree):
    """计算并写入节点深度：root 深度为 0。"""

    def visit(node_id, depth):
        node = tree.nodes[node_id]
        node.depth = depth
        for child_id in node.children:
            visit(child_id, depth + 1)

    for root_id in tree.roots:
        visit(root_id, 0)

    return tree


def build_family_trees(seq, oracle_result=None):
    """从原始序列构造 upper/lower 两棵家族树（仅对 valid 序列）。"""
    values = list(seq)

    if oracle_result is None:
        oracle_result = oracle(values)

    if not oracle_result["valid"]:
        raise ValueError(f"invalid candidate: {oracle_result['reason']}")

    upper_intervals = build_family_intervals(values, UPPER)
    lower_intervals = build_family_intervals(values, LOWER)

    return {
        UPPER: build_family_tree(upper_intervals, UPPER),
        LOWER: build_family_tree(lower_intervals, LOWER),
    }


def node_to_dict(node):
    """把 IntervalNode 转成可序列化字典。"""
    return {
        "id": node.id,
        "interval": list(node.interval),
        "pair_index": node.pair_index,
        "parent": node.parent,
        "children": list(node.children),
        "depth": node.depth,
    }


def family_tree_to_dict(tree):
    """把 FamilyTree 转成可序列化字典。"""
    return {
        "pair_family": tree.pair_family,
        "nodes": [node_to_dict(node) for node in tree.nodes],
        "roots": list(tree.roots),
    }
