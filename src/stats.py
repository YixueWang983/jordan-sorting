"""Structural statistics for candidate Jordan sequences."""

from family_tree import LOWER, UPPER, build_family_trees
from oracle import oracle

INVALID_CATEGORY = "invalid"
STRICT_FLAT = "strict_flat"
LOW_NESTING_VALID = "low_nesting_valid"
MEDIUM_NESTING_VALID = "medium_nesting_valid"
NESTED_HEAVY_VALID = "nested_heavy_valid"


def _invalid_profile(reason):
    """返回无效候选对应的统计结构。"""
    return {
        "valid": False,
        "reason": reason,
        "upper_interval_count": None,
        "lower_interval_count": None,
        "total_interval_count": None,
        "upper_root_count": None,
        "lower_root_count": None,
        "upper_nesting_count": None,
        "lower_nesting_count": None,
        "nesting_count": None,
        "nesting_density": None,
        "upper_max_depth": None,
        "lower_max_depth": None,
        "max_depth": None,
        "category": INVALID_CATEGORY,
    }


def _nesting_count(tree):
    """返回树中的非根节点数量（父指针已存在的节点数）。"""
    return sum(1 for node in tree.nodes if node.parent is not None)


def _max_depth(tree):
    """返回树的最大深度；空树返回 0。"""
    if not tree.nodes:
        return 0
    return max(node.depth for node in tree.nodes)


def _classify_valid_profile(nesting_count, total_interval_count, max_depth):
    """按简化分类返回结构类型。"""
    if nesting_count == 0:
        return STRICT_FLAT

    nesting_density = (
        nesting_count / total_interval_count if total_interval_count > 0 else 0.0
    )

    if max_depth <= 1 and nesting_density <= 0.35:
        return LOW_NESTING_VALID
    if max_depth <= 3 and nesting_density <= 0.70:
        return MEDIUM_NESTING_VALID
    return NESTED_HEAVY_VALID


def structure_profile(seq, oracle_result=None, family_trees=None):
    """返回 candidate sequence 的结构统计 profile。"""
    values = list(seq)
    if oracle_result is None:
        oracle_result = oracle(values)

    if not oracle_result["valid"]:
        return _invalid_profile(oracle_result["reason"])

    if family_trees is None:
        trees = build_family_trees(values, oracle_result=oracle_result)
    else:
        if (
            not isinstance(family_trees, dict)
            or UPPER not in family_trees
            or LOWER not in family_trees
        ):
            raise ValueError("family_trees must be a dict with upper and lower entries")
        trees = family_trees

    upper_tree = trees[UPPER]
    lower_tree = trees[LOWER]

    upper_interval_count = len(upper_tree.nodes)
    lower_interval_count = len(lower_tree.nodes)
    total_interval_count = upper_interval_count + lower_interval_count

    upper_root_count = len(upper_tree.roots)
    lower_root_count = len(lower_tree.roots)

    upper_nesting_count = _nesting_count(upper_tree)
    lower_nesting_count = _nesting_count(lower_tree)
    nesting_count = upper_nesting_count + lower_nesting_count

    nesting_density = (
        nesting_count / total_interval_count if total_interval_count > 0 else 0.0
    )

    upper_max_depth = _max_depth(upper_tree)
    lower_max_depth = _max_depth(lower_tree)
    max_depth = max(upper_max_depth, lower_max_depth)

    category = _classify_valid_profile(
        nesting_count=nesting_count,
        total_interval_count=total_interval_count,
        max_depth=max_depth,
    )

    return {
        "valid": True,
        "reason": None,
        "upper_interval_count": upper_interval_count,
        "lower_interval_count": lower_interval_count,
        "total_interval_count": total_interval_count,
        "upper_root_count": upper_root_count,
        "lower_root_count": lower_root_count,
        "upper_nesting_count": upper_nesting_count,
        "lower_nesting_count": lower_nesting_count,
        "nesting_count": nesting_count,
        "nesting_density": nesting_density,
        "upper_max_depth": upper_max_depth,
        "lower_max_depth": lower_max_depth,
        "max_depth": max_depth,
        "category": category,
    }
