"""Test instance generators for simplified Jordan sorting."""

import random


def generate_flat(n):
    """Generate the flat sequence [1, 2, ..., n]."""
    return list(range(1, n + 1))


def generate_nested(n):
    """Generate [1, n, 2, n-1, ...] style nested examples."""
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
    """Generate a small sequence with an upper-family crossing."""
    return [1, 3, 2, 4]


def generate_invalid_lower_crossing():
    """Generate a small sequence with a lower-family crossing."""
    return [5, 1, 3, 2, 4]


def generate_random_permutation(n, seed=None):
    """Generate a random permutation of [1, 2, ..., n]."""
    values = list(range(1, n + 1))
    random.Random(seed).shuffle(values)
    return values


def mutate_by_swap(seq, i=None, j=None, seed=None):
    """Return a copy of seq with two positions swapped."""
    values = list(seq)
    if len(values) < 2:
        return values

    if i is None or j is None:
        i, j = random.Random(seed).sample(range(len(values)), 2)

    values[i], values[j] = values[j], values[i]
    return values


def generate_small_handmade_valid_cases():
    """Return small valid cases for debugging and thesis examples."""
    return [
        [],
        [1],
        [1, 2],
        [1, 2, 3, 4, 5, 6],
        [1, 6, 2, 5, 3, 4],
    ]
