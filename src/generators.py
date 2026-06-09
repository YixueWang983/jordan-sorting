"""简化 Jordan sorting 的测试实例生成器。"""

import json
import random
from pathlib import Path

from oracle import oracle


FLAT_VALID = "flat_valid"
NESTED_VALID = "nested_valid"
INVALID_UPPER_CROSSING = "invalid_upper_crossing"
INVALID_LOWER_CROSSING = "invalid_lower_crossing"
RANDOM_PERMUTATION = "random_permutation"
RANDOM_INVALID = "random_invalid"
MUTATION_BASED_INVALID = "mutation_based_invalid"

SUPPORTED_FAMILIES = {
    FLAT_VALID,
    NESTED_VALID,
    INVALID_UPPER_CROSSING,
    INVALID_LOWER_CROSSING,
    RANDOM_PERMUTATION,
    RANDOM_INVALID,
}


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


def generate_invalid_upper_crossing(n):
    """生成长度为 n 且 upper family 发生 crossing 的序列。"""
    if n < 4:
        raise ValueError("upper crossing requires n >= 4")
    return [1, 3, 2, 4] + list(range(5, n + 1))


def generate_invalid_lower_crossing(n):
    """生成长度为 n 且 lower family 发生 crossing 的序列。"""
    if n < 5:
        raise ValueError("lower crossing requires n >= 5")
    return [1, 2, 4, 3, 5] + list(range(6, n + 1))


def generate_random_permutation(n, seed=None):
    """生成 [1, 2, ..., n] 的随机排列。"""
    values = list(range(1, n + 1))
    random.Random(seed).shuffle(values)
    return values


def generate_random_invalid(n, seed=None, max_attempts=1000):
    """生成一个由 oracle 认证为 invalid 的随机排列。"""
    for attempt in range(max_attempts):
        attempt_seed = None if seed is None else seed + attempt
        values = generate_random_permutation(n, seed=attempt_seed)
        if not oracle(values)["valid"]:
            return values
    raise ValueError("failed to generate random invalid sequence")


def mutate_by_swap(seq, i=None, j=None, seed=None):
    """返回交换了两个位置之后的序列副本。"""
    values = list(seq)
    if len(values) < 2:
        return values

    if i is None or j is None:
        i, j = random.Random(seed).sample(range(len(values)), 2)

    values[i], values[j] = values[j], values[i]
    return values


def generate_mutation_based_invalid(seq, seed=None, max_attempts=1000):
    """从给定序列出发，生成一个由 oracle 认证为 invalid 的 swap mutation。"""
    values = list(seq)
    for attempt in range(max_attempts):
        attempt_seed = None if seed is None else seed + attempt
        candidate = mutate_by_swap(values, seed=attempt_seed)
        if not oracle(candidate)["valid"]:
            return candidate
    raise ValueError("failed to generate invalid mutation")


def generate_small_handmade_valid_cases():
    """返回用于调试和论文示例的小型 valid cases。"""
    return [
        [],
        [1],
        [1, 2],
        [1, 2, 3, 4, 5, 6],
        [1, 6, 2, 5, 3, 4],
    ]


def make_case_id(family, n, index):
    """生成稳定的测试用例 id，方便实验和 debug 引用。"""
    return f"{family}_n{n}_{index:03d}"


def make_test_case(seq, family, case_id=None, seed=None):
    """把序列包装成标准 JSON test case 字典，并附上 oracle 结果。"""
    values = list(seq)
    return {
        "id": case_id,
        "n": len(values),
        "family": family,
        "seed": seed,
        "sequence": values,
        "oracle": oracle(values),
    }


def save_test_case(seq, family, path, seed=None, case_id=None):
    """保存一个带 oracle 认证结果的 JSON test case。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    case = make_test_case(seq, family, case_id=case_id, seed=seed)
    output_path.write_text(
        json.dumps(case, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return case


def load_test_case(path):
    """从 JSON 文件读取一个 test case。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_sequence(family, n, seed=None):
    """根据 family 名称生成一个序列。"""
    if family == FLAT_VALID:
        return generate_flat(n)
    if family == NESTED_VALID:
        return generate_nested(n)
    if family == INVALID_UPPER_CROSSING:
        return generate_invalid_upper_crossing(n)
    if family == INVALID_LOWER_CROSSING:
        return generate_invalid_lower_crossing(n)
    if family == RANDOM_PERMUTATION:
        return generate_random_permutation(n, seed=seed)
    if family == RANDOM_INVALID:
        return generate_random_invalid(n, seed=seed)
    raise ValueError(f"unsupported family: {family}")


def generate_dataset(family, sizes, repetitions, output_dir, seed=0):
    """批量生成 JSON test cases，并返回生成出的文件路径列表。"""
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(f"unsupported family: {family}")

    output_root = Path(output_dir)
    paths = []
    for n in sizes:
        for index in range(1, repetitions + 1):
            case_seed = None
            if family in {RANDOM_PERMUTATION, RANDOM_INVALID}:
                case_seed = seed + n * 1000 + index

            seq = generate_sequence(family, n, seed=case_seed)
            case_id = make_case_id(family, len(seq), index)
            path = output_root / family / f"{case_id}.json"
            save_test_case(seq, family, path, seed=case_seed, case_id=case_id)
            paths.append(path)
    return paths
