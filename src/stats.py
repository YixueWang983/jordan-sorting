"""Structural statistics for candidate Jordan sequences."""

from family_tree import (
    LOWER,
    UPPER,
    build_family_trees,
    proper_interval_contains,
)
from oracle import (
    crosses,
    lower_pairs,
    oracle,
    pair_to_interval,
    rank_map,
    upper_pairs,
)

INVALID_CATEGORY = "invalid"
STRICT_FLAT = "strict_flat"
LOW_NESTING_VALID = "low_nesting_valid"
MEDIUM_NESTING_VALID = "medium_nesting_valid"
NESTED_HEAVY_VALID = "nested_heavy_valid"


def _pair_count(size):
    """Return C(size, 2)."""
    return size * (size - 1) // 2


def _containment_pair_count(tree):
    """Count all proper containment pairs in one family tree."""
    count = 0
    for i, first in enumerate(tree.nodes):
        for second in tree.nodes[i + 1 :]:
            first_contains_second = proper_interval_contains(
                first.interval,
                second.interval,
            )
            second_contains_first = proper_interval_contains(
                second.interval,
                first.interval,
            )
            if first_contains_second or second_contains_first:
                count += 1
    return count


def _family_intervals(values, pair_family):
    """Return rank intervals for a pair family."""
    rank = rank_map(values)
    pairs = upper_pairs(values) if pair_family == UPPER else lower_pairs(values)
    return [pair_to_interval(pair, rank) for pair in pairs]


def crossing_pair_count(seq, pair_family):
    """Count crossing interval pairs for one pair family.

    This diagnostic helper requires distinct values. Duplicate sequences do not
    have a reliable rank-interval interpretation here.
    """
    if pair_family not in {UPPER, LOWER}:
        raise ValueError("pair_family must be 'upper' or 'lower'")

    values = list(seq)
    if len(values) != len(set(values)):
        return None

    intervals = _family_intervals(values, pair_family)
    count = 0
    for i, first in enumerate(intervals):
        for second in intervals[i + 1 :]:
            if crosses(first, second):
                count += 1
    return count


def _invalid_profile(seq, oracle_result):
    """返回无效候选对应的统计结构。"""
    reason = oracle_result["reason"]
    if oracle_result.get("distinct_values"):
        upper_crossing_pair_count = crossing_pair_count(seq, UPPER)
        lower_crossing_pair_count = crossing_pair_count(seq, LOWER)
        total_crossing_pair_count = (
            upper_crossing_pair_count + lower_crossing_pair_count
        )
        crossing_fields = {
            "upper_crossing_pair_count": upper_crossing_pair_count,
            "lower_crossing_pair_count": lower_crossing_pair_count,
            "total_crossing_pair_count": total_crossing_pair_count,
        }
    else:
        crossing_fields = {
            "upper_crossing_pair_count": None,
            "lower_crossing_pair_count": None,
            "total_crossing_pair_count": None,
        }

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
        "parented_interval_ratio": None,
        "upper_max_depth": None,
        "lower_max_depth": None,
        "max_depth": None,
        "upper_containment_pair_count": None,
        "lower_containment_pair_count": None,
        "containment_pair_count": None,
        "containment_pair_density": None,
        **crossing_fields,
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


def classify_valid_profile(nesting_count, total_interval_count, max_depth):
    """Classify a valid profile by nesting shape.

    Returns one of:
    - ``strict_flat``
    - ``low_nesting_valid``
    - ``medium_nesting_valid``
    - ``nested_heavy_valid``
    """
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


# Backward-compatible alias: existing tests and callers may import this name.
_classify_valid_profile = classify_valid_profile


def structure_profile(seq, oracle_result=None, family_trees=None):
    """返回 candidate sequence 的结构统计 profile。"""
    values = list(seq)
    if oracle_result is None:
        oracle_result = oracle(values)

    if not oracle_result["valid"]:
        return _invalid_profile(values, oracle_result)

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
    parented_interval_ratio = nesting_density

    upper_containment_pair_count = _containment_pair_count(upper_tree)
    lower_containment_pair_count = _containment_pair_count(lower_tree)
    containment_pair_count = upper_containment_pair_count + lower_containment_pair_count
    containment_pair_denominator = _pair_count(upper_interval_count) + _pair_count(
        lower_interval_count
    )
    containment_pair_density = (
        containment_pair_count / containment_pair_denominator
        if containment_pair_denominator > 0
        else 0.0
    )

    upper_max_depth = _max_depth(upper_tree)
    lower_max_depth = _max_depth(lower_tree)
    max_depth = max(upper_max_depth, lower_max_depth)

    category = classify_valid_profile(
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
        "parented_interval_ratio": parented_interval_ratio,
        "upper_max_depth": upper_max_depth,
        "lower_max_depth": lower_max_depth,
        "max_depth": max_depth,
        "upper_containment_pair_count": upper_containment_pair_count,
        "lower_containment_pair_count": lower_containment_pair_count,
        "containment_pair_count": containment_pair_count,
        "containment_pair_density": containment_pair_density,
        "upper_crossing_pair_count": 0,
        "lower_crossing_pair_count": 0,
        "total_crossing_pair_count": 0,
        "category": category,
    }
