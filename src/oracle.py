"""简化 Jordan sorting 的正确性 oracle。"""


def upper_pairs(seq):
    """从序列中取出 upper pairs: (x1, x2), (x3, x4), ...。"""
    values = list(seq)
    return [(values[i], values[i + 1]) for i in range(0, len(values) - 1, 2)]


def lower_pairs(seq):
    """从序列中取出 lower pairs: (x2, x3), (x4, x5), ...。"""
    values = list(seq)
    return [(values[i], values[i + 1]) for i in range(1, len(values) - 1, 2)]


def rank_map(seq):
    """把每个元素映射到它在排序结果中的 1-based rank。"""
    values = list(seq)
    return {value: index for index, value in enumerate(sorted(values), start=1)}


def pair_to_interval(pair, rank):
    """把一个 pair 转换成闭区间形式的 rank interval。"""
    first, second = pair
    left = rank[first]
    right = rank[second]
    return (min(left, right), max(left, right))


def crosses(interval1, interval2):
    """如果两个 rank intervals 发生 crossing，则返回 True。"""
    a, b = interval1
    c, d = interval2
    return (a < c < b < d) or (c < a < d < b)


def is_laminar(pairs, rank):
    """如果一组 pairs 对应的 intervals 是 laminar family，则返回 True。"""
    intervals = [pair_to_interval(pair, rank) for pair in pairs]
    for i, first in enumerate(intervals):
        for second in intervals[i + 1 :]:
            if crosses(first, second):
                return False
    return True


def oracle(seq):
    """检查序列是否同时满足 upper 和 lower family 的 laminarity。"""
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
