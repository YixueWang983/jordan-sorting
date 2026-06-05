"""Correctness oracle for simplified Jordan sorting."""


def upper_pairs(seq):
    """Return pairs (x1, x2), (x3, x4), ... from a sequence."""
    values = list(seq)
    return [(values[i], values[i + 1]) for i in range(0, len(values) - 1, 2)]


def lower_pairs(seq):
    """Return pairs (x2, x3), (x4, x5), ... from a sequence."""
    values = list(seq)
    return [(values[i], values[i + 1]) for i in range(1, len(values) - 1, 2)]


def rank_map(seq):
    """Map each value to its one-based rank in sorted order."""
    values = list(seq)
    return {value: index for index, value in enumerate(sorted(values), start=1)}


def pair_to_interval(pair, rank):
    """Convert a pair into a closed rank interval."""
    first, second = pair
    left = rank[first]
    right = rank[second]
    return (min(left, right), max(left, right))


def crosses(interval1, interval2):
    """Return True if two rank intervals cross."""
    a, b = interval1
    c, d = interval2
    return (a < c < b < d) or (c < a < d < b)


def is_laminar(pairs, rank):
    """Return True if the intervals induced by pairs are laminar."""
    intervals = [pair_to_interval(pair, rank) for pair in pairs]
    for i, first in enumerate(intervals):
        for second in intervals[i + 1 :]:
            if crosses(first, second):
                return False
    return True


def oracle(seq):
    """Check whether a sequence satisfies upper and lower laminarity."""
    values = list(seq)
    sorted_values = sorted(values)

    if len(values) != len(set(values)):
        return {
            "valid": False,
            "sorted": sorted_values,
            "upper_ok": False,
            "lower_ok": False,
            "reason": "duplicate values",
        }

    rank = rank_map(values)
    upper_ok = is_laminar(upper_pairs(values), rank)
    lower_ok = is_laminar(lower_pairs(values), rank)

    reason = None
    if not upper_ok and not lower_ok:
        reason = "upper and lower crossing"
    elif not upper_ok:
        reason = "upper crossing"
    elif not lower_ok:
        reason = "lower crossing"

    return {
        "valid": upper_ok and lower_ok,
        "sorted": sorted_values,
        "upper_ok": upper_ok,
        "lower_ok": lower_ok,
        "reason": reason,
    }
