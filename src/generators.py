"""简化 Jordan sorting 的测试实例生成器。"""

import random


def generate_flat(n):
    """生成 flat 序列 [1, 2, ..., n]。"""
    return list(range(1, n + 1))


def generate_nested(n):
    """生成 [1, n, 2, n-1, ...] 形式的 nested 候选序列。"""
    values = []
    left = 1
    right = n
    while left <= right:
        values.append(left)
        if left != right:
            values.append(right)
        left += 1
        right -= 1
    return values


def generate_invalid_upper_crossing():
    """生成一个 upper family 发生 crossing 的小序列。"""
    return [1, 3, 2, 4]


def generate_invalid_lower_crossing():
    """生成一个 lower family 发生 crossing 的小序列。"""
    return [5, 1, 3, 2, 4]


def generate_random_permutation(n, seed=None):
    """生成 [1, 2, ..., n] 的随机排列。"""
    values = list(range(1, n + 1))
    random.Random(seed).shuffle(values)
    return values


def mutate_by_swap(seq, i=None, j=None, seed=None):
    """返回交换了两个位置之后的序列副本。"""
    values = list(seq)
    if len(values) < 2:
        return values

    if i is None or j is None:
        i, j = random.Random(seed).sample(range(len(values)), 2)

    values[i], values[j] = values[j], values[i]
    return values


def generate_small_handmade_valid_cases():
    """返回用于调试和论文示例的小型 valid cases。"""
    return [
        [],
        [1],
        [1, 2],
        [1, 2, 3, 4, 5, 6],
        [1, 6, 2, 5, 3, 4],
    ]
