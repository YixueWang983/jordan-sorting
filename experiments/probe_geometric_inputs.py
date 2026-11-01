"""Exploratory geometry-to-Jordan probe; no clocks, benchmarks, or timing data.

A randomized grid spanning tree is thickened into a simple orthogonal polygon.
Only the number of crossings is prescribed; split outcomes never guide sampling.
This file does not import or change the project's existing input generators.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
from statistics import median
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from heterogeneous_finger_backend import HeterogeneousFingerBackend
from oracle import oracle
from paper_jordan_sort import paper_jordan_diagnostics_valid
from sibling_backend_contract import SiblingBackendSpec

SIZES = (32, 64, 128, 256, 512)
MASTER_SEED = 20261101
PER_SIZE = 20
HEIGHT = 16
SCHEMA = "exploratory_geometric_jordan_probe_v1"
BACKEND = SiblingBackendSpec(
    HeterogeneousFingerBackend,
    (("detailed_work", False), ("instrumented", True)),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def case_seed(master_seed, size, index):
    label = f"geometric-grid-tree-v1/{master_seed}/{size}/{index}"
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], "big")


class DisjointSets:
    def __init__(self, size):
        self.parent = list(range(size))
        self.weight = [1] * size
        self.components = size

    def find(self, value):
        while value != self.parent[value]:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def join(self, first, second):
        first, second = self.find(first), self.find(second)
        if first == second:
            return False
        if self.weight[first] < self.weight[second]:
            first, second = second, first
        self.parent[second] = first
        self.weight[first] += self.weight[second]
        self.components -= 1
        return True


def polygon_boundary(cells):
    """Cancel shared unit edges, then certify one non-self-touching cycle.

Unit lattice edges cannot cross away from lattice vertices. Exactly one incoming
and outgoing edge at each vertex, plus a single cycle visiting all boundary
edges, rules out both pinches and extra boundary components (including holes).
"""
    boundary = set()
    for x, y in sorted(cells):
        corners = ((x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1))
        for first, second in zip(corners, corners[1:] + corners[:1]):
            if (second, first) in boundary:
                boundary.remove((second, first))
            else:
                boundary.add((first, second))
    require(bool(boundary), "empty boundary")
    successors, predecessors = {}, {}
    for first, second in sorted(boundary):
        require(first not in successors and second not in predecessors,
                "boundary branch or corner pinch")
        successors[first] = second
        predecessors[second] = first
    require(set(successors) == set(predecessors), "open boundary")
    start = min(successors)
    point = start
    visited, unit_vertices = set(), []
    while point not in visited:
        visited.add(point)
        unit_vertices.append(point)
        point = successors[point]
    require(point == start and len(visited) == len(boundary),
            "multiple boundary cycles or repeated vertex")
    vertices = []
    for index, point in enumerate(unit_vertices):
        before = unit_vertices[index - 1]
        after = unit_vertices[(index + 1) % len(unit_vertices)]
        incoming = (point[0] - before[0], point[1] - before[1])
        outgoing = (after[0] - point[0], after[1] - point[1])
        if incoming != outgoing:
            vertices.append(point)
    area_twice = sum(
        a[0] * b[1] - b[0] * a[1]
        for a, b in zip(vertices, vertices[1:] + vertices[:1])
    )
    require(len(vertices) >= 4 and area_twice == 2 * len(cells),
            "boundary area does not match occupied cells")
    return vertices, {
        "single_boundary_cycle": True,
        "boundary_vertices_unique": True,
        "unit_boundary_edges": len(boundary),
        "occupied_cells": len(cells),
        "area_twice": area_twice,
    }


def generate_polygon(size, seed, height=HEIGHT):
    """Randomized Kruskal completion after fixing only crossing cardinality.

Keep size/2 uniformly selected vertical edges across the middle row cut. These
edges are disjoint, so they form a forest. The allowed graph (two connected
half-grids joined by these edges) is connected; random-order Kruskal therefore
completes the forest to a spanning tree. This distribution is NOT uniform over
spanning trees, over polygons, or over Jordan permutations.
"""
    require(size >= 4 and size % 2 == 0, "size must be even and at least four")
    require(height >= 4 and height % 2 == 0, "height must be even and at least four")
    rng = random.Random(seed)
    width, cut_row = size, height // 2 - 1
    columns = sorted(rng.sample(range(width), size // 2))
    sets = DisjointSets(width * height)
    tree = []
    for x in columns:
        edge = (cut_row * width + x, (cut_row + 1) * width + x)
        require(sets.join(*edge), "prescribed crossing edges form a cycle")
        tree.append(edge)
    candidates = []
    for y in range(height):
        for x in range(width):
            point = y * width + x
            if x + 1 < width:
                candidates.append((point, point + 1))
            if y + 1 < height and y != cut_row:
                candidates.append((point, point + width))
    rng.shuffle(candidates)
    for edge in candidates:
        if sets.join(*edge):
            tree.append(edge)
        if sets.components == 1:
            break
    require(sets.components == 1 and len(tree) == width * height - 1,
            "grid tree not connected")

    # Node squares are three units apart; only selected edges get corridors.
    # Unrelated corridors cannot touch. Expanding a tree in this way adds no
    # cell-adjacency cycle and no hole.
    cells = {(3 * x, 3 * y) for y in range(height) for x in range(width)}
    for first, second in tree:
        x, y = first % width, first // width
        if second - first == 1:
            cells.update(((3 * x + 1, 3 * y), (3 * x + 2, 3 * y)))
        else:
            require(second - first == width, "non-grid edge")
            cells.update(((3 * x, 3 * y + 1), (3 * x, 3 * y + 2)))
    adjacency_count = sum(
        ((x + 1, y) in cells) + ((x, y + 1) in cells) for x, y in cells
    )
    require(adjacency_count == len(cells) - 1, "unexpected corridor contact")
    vertices, certificate = polygon_boundary(cells)
    direction = "clockwise" if rng.getrandbits(1) else "counterclockwise"
    if direction == "clockwise":
        vertices.reverse()
    start_index = rng.randrange(len(vertices))
    vertices = vertices[start_index:] + vertices[:start_index]
    # Odd doubled height: no integer-coordinate polygon vertex can lie here.
    line_y_twice = 6 * cut_row + 3
    certificate.update(
        grid_width=width, grid_height=height,
        grid_tree_vertices=width * height, grid_tree_edges=len(tree),
        cell_adjacencies=adjacency_count, crossing_columns=columns,
        polygon_vertices=len(vertices), polygon_sha256=digest(vertices),
        traversal_direction=direction, start_index_after_direction=start_index,
        start_vertex=vertices[0], line_y_twice=line_y_twice,
    )
    return vertices, line_y_twice, certificate


def intersection_sequence(vertices, line_y_twice):
    require(all(2 * y != line_y_twice for _, y in vertices),
            "a vertex lies on the line")
    intersections, xs = [], []
    for index, (first, second) in enumerate(zip(vertices, vertices[1:] + vertices[:1])):
        ax, ay = first
        bx, by = second
        if (2 * ay < line_y_twice < 2 * by or
                2 * by < line_y_twice < 2 * ay):
            x = Fraction(ax) + Fraction(line_y_twice - 2 * ay, 2 * (by - ay)) * (bx - ax)
            xs.append(x)
            intersections.append(dict(edge_index=index, x_numerator=x.numerator,
                                      x_denominator=x.denominator))
    require(len(xs) == len(set(xs)), "coincident intersection x coordinates")
    require(len(xs) >= 4 and len(xs) % 2 == 0, "unexpected crossing count")
    ranks = {x: index + 1 for index, x in enumerate(sorted(xs))}
    return [ranks[x] for x in xs], intersections


def split_statistics(split_trace):
    performed, smaller = [], []
    for event in split_trace:
        require(event["step"] == "step3b_split_sibling_list", "not a split trace event")
        require(type(event["performed"]) is bool, "bad split flag")
        if not event["performed"]:
            continue
        left, right, total = (event[k] for k in ("left_size", "right_size", "input_size"))
        require(all(type(x) is int and x >= 0 for x in (left, right, total))
                and total > 0 and left + right == total, "split size conservation")
        performed.append(event)
        if left > 0 and right > 0:
            smaller.append(min(left, right))
    return dict(total_splits=len(performed), interior_splits=len(smaller),
                interior_smaller_side_sizes=smaller,
                has_interior_split=bool(smaller))


def evaluate(size, index, seed, height):
    record = dict(case=f"geometric-n{size}-{index:02d}", target_n=size,
                  index=index, seed=seed, status="generation_error")
    try:
        vertices, line, certificate = generate_polygon(size, seed, height)
        values, intersections = intersection_sequence(vertices, line)
        require(len(values) == size, "crossing count differs from requested size")
        record.update(geometry=certificate, intersection_count=len(values),
                      intersections=intersections, rank_sequence=values,
                      rank_sequence_sha256=digest(values))
    except Exception as exc:
        record["error"] = dict(type=type(exc).__name__, message=str(exc))
        return record
    record["oracle"] = oracle(values)
    if not record["oracle"]["valid"]:
        record["status"] = "oracle_invalid"
        return record
    try:
        # This API fixes CHECKED_POLICY and performs state/backend audits.
        # Its operation counters are deliberately not used or archived here.
        diagnostic = paper_jordan_diagnostics_valid(values, backend=BACKEND)
        require(diagnostic["invariants_valid"] is True, "checked audit failed")
        require(diagnostic["output"] == list(range(1, size + 1)), "incorrect sorted output")
        trace = diagnostic["trace"]
        split_trace = [event for event in trace if event["step"] == "step3b_split_sibling_list"]
        require(len(split_trace) == size - 3, "incomplete split trace")
        record.update(status="pass", output_correct=True, checked_audits_passed=True,
                      backend_identity=diagnostic["backend_identity"],
                      full_trace_sha256=digest(trace), split_trace=split_trace,
                      statistics=split_statistics(split_trace))
    except Exception as exc:
        record.update(status="checked_error", error=dict(type=type(exc).__name__, message=str(exc)))
    return record


def summarize(cases):
    groups = []
    for size in sorted({case["target_n"] for case in cases}):
        selected = [case for case in cases if case["target_n"] == size]
        passed = [case for case in selected if case["status"] == "pass"]
        sizes = [k for case in passed for k in case["statistics"]["interior_smaller_side_sizes"]]
        total = sum(case["statistics"]["total_splits"] for case in passed)
        histogram = Counter(sizes)
        groups.append(dict(
            target_n=size, planned_inputs=len(selected),
            status_counts={status: sum(case["status"] == status for case in selected)
                           for status in ("pass", "oracle_invalid", "generation_error", "checked_error")},
            intersection_counts=sorted({case["intersection_count"] for case in selected if "intersection_count" in case}),
            inputs_with_interior_split=sum(case["statistics"]["has_interior_split"] for case in passed),
            total_splits=total, interior_splits=len(sizes),
            interior_fraction=len(sizes) / total if total else None,
            smaller_side_histogram={str(k): histogram[k] for k in sorted(histogram)},
            smaller_side_min=min(sizes) if sizes else None,
            smaller_side_median=median(sizes) if sizes else None,
            smaller_side_max=max(sizes) if sizes else None,
        ))
    return groups


def write_report(path, raw_path, payload):
    groups = payload["summary"]
    statuses = Counter(case["status"] for case in payload["cases"])
    covered = sum(group["inputs_with_interior_split"] for group in groups)
    total = sum(group["total_splits"] for group in groups)
    interior = sum(group["interior_splits"] for group in groups)
    all_sizes = [k for case in payload["cases"] if case["status"] == "pass"
                 for k in case["statistics"]["interior_smaller_side_sizes"]]
    largest = max(all_sizes) if all_sizes else 0
    raw_label = str(raw_path.relative_to(ROOT)) if raw_path.is_relative_to(ROOT) else str(raw_path)
    rows = []
    for group in groups:
        fraction = group["interior_fraction"]
        description = (f"{group['smaller_side_min']} / {group['smaller_side_median']:g} / {group['smaller_side_max']}"
                       if group["interior_splits"] else "—")
        rows.append(f"| {group['target_n']} | {group['planned_inputs']} | {group['status_counts']['oracle_invalid']} | "
                    f"{group['status_counts']['pass']} | {group['inputs_with_interior_split']} | "
                    f"{group['total_splits']} | {group['interior_splits']} | "
                    f"{fraction:.1%} | {description} |" if fraction is not None else
                    f"| {group['target_n']} | {group['planned_inputs']} | {group['status_counts']['oracle_invalid']} | "
                    f"{group['status_counts']['pass']} | 0 | 0 | 0 | — | — |")
    bins = (("1", 1, 1), ("2", 2, 2), ("3–4", 3, 4), ("5–8", 5, 8),
            ("9–16", 9, 16), ("17–32", 17, 32), ("≥33", 33, float("inf")))
    hist_rows = []
    for label, lower, upper in bins:
        counts = [sum(count for key, count in group["smaller_side_histogram"].items()
                      if lower <= int(key) <= upper) for group in groups]
        hist_rows.append("| " + label + " | " + " | ".join(map(str, counts)) + " | " + str(sum(counts)) + " |")
    examples = []
    for group in groups:
        options = [(min(event["left_size"], event["right_size"]), case["case"], event)
                   for case in payload["cases"] if case["target_n"] == group["target_n"] and case["status"] == "pass"
                   for event in case["split_trace"] if event["performed"] and event["left_size"] and event["right_size"]]
        if options:
            k, name, event = max(options, key=lambda item: item[0])
            examples.append(f"| {group['target_n']} | `{name}` | {event['iteration']} | {event['input_size']} | "
                            f"{event['left_size']} | {event['right_size']} | {k} |")
    text = f"""# 随机几何输入生成器试探（2026-11-01）

## 结果

这是一次结构探索，没有计时。预定 {len(payload['cases'])} 个输入，成功完成 checked
运行 {statuses['pass']} 个；oracle 不合法 {statuses['oracle_invalid']} 个，几何生成失败
{statuses['generation_error']} 个，checked 运行失败 {statuses['checked_error']} 个。
成功运行中有 **{covered} 个输入出现双侧 split**；trace 共记录 {total} 次实际 split，
其中 **{interior} 次为双侧 split**，较小一侧的最大值为 **{largest}**。
这里的“出现”只针对下述随机通道多边形族，不代表任意简单多边形的分布。

| 交点数 n | 预定输入 | oracle 不合法 | checked 通过 | 至少一次双侧 split 的输入 | split 总数 | 双侧 split 数 | 双侧占比 | 较小侧 min / median / max |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

“split 总数”只计 `performed=true`，双侧要求左右大小都大于零。较小侧是
`min(left_size, right_size)`，单位为兄弟列表中的 **pair 条目数**，不是几何顶点数。
中位数及下表按 split 事件汇总；同一输入的多次事件互相关联，不视为独立样本。

## 较小侧规模分布

| 较小侧大小 | {" | ".join(str(g['target_n']) for g in groups)} | 合计 |
|---|{"---:|" * (len(groups) + 1)}
{chr(10).join(hist_rows)}

完整逐值频数在原始 JSON 的 `summary[].smaller_side_histogram` 中。
每组最大较小侧的一个实例（仅作事后结果定位，不用于选择输入）：

| n | 输入 | 迭代 | 切分前大小 | 左侧 | 右侧 | 较小侧 |
|---:|---|---:|---:|---:|---:|---:|
{chr(10).join(examples) if examples else '| — | 未观察到双侧 split | — | — | — | — | — |'}

## 几何方法及选择理由

1. 对每个目标 n，取宽 n、高 {payload['parameters']['height']} 的矩形网格。
   在中间两行之间均匀抽取 n/2 列，保留对应跨线边；这些互不相接的边构成森林。
   排除该行切口的其他跨线边，将其余所有网格边随机排列，用 Kruskal 的连通分量
   检查补成一棵生成树。两半网格各自连通且存在保留的跨线边，因此能完成生成树。
   这里只规定交点数，没有预设 Jordan 排列、目标 split 位置或较小侧大小。
2. 将每个网格点变为单位方块，点距为 3；沿树边补上宽 1 的通道。未连接的
   方块和通道之间留有空隙。树的加宽不会产生孔洞或自交。程序额外核对细网格
   方块邻接边数，并将公共边抵消，检查剩余单位边构成唯一闭环、边界顶点不重复、
   每个顶点入度出度都为 1，且多边形面积等于方块总面积。单位网格边不会在
   非网格顶点处交叉，所以这些检查也排除了角点相接和多条边界。
3. 合并连续共线边得到简单正交多边形。水平线位于中间两行通道内部，其 y
   为半整数，所有顶点坐标为整数，因此没有顶点在线上。每个跨线通道贡献两条
   不同 x 的边界交点，不同通道之间也不重合，交点数恰为 n。求交使用
   `fractions.Fraction` 的精确有理数，不使用浮点容差。
4. 对每个多边形随机选择遍历方向，再均匀选择一个简化后的边界顶点作为起点。
   起点不在线上。沿整个闭合边界按边的先后记录交点，再按交点 x 的排序秩生成
   1 到 n 的序列；包括最后一条回到起点的边。

选择这种构造是因为它同时提供可核查的简单性和可控的交点数，避免为取得
512 个交点而反复筛选大量多边形。随机性来自跨线列、其余边的排列、起点和方向。
它不是对所有简单多边形或生成树的均匀采样。每个规模预先固定
{payload['parameters']['per_size']} 个种子；不按 oracle 或 split 结果补抽、替换或删样本。

## 认证、执行和原始记录

- 主种子：`{payload['parameters']['master_seed']}`。每例种子为字符串
  `geometric-grid-tree-v1/主种子/n/序号` 的 SHA-256 前 8 字节大端整数。
  全部派生种子及具体序列保存在 JSON 中。
- 每个成功生成的输入先调用 `src/oracle.py`。无效输入会保留记录、计入失败，
  并跳过树调用；不会被有效输入替换。
- 使用插桩树 `instrumented=True, detailed_work=False`，通过
  `paper_jordan_diagnostics_valid` 固定执行 checked 策略及审计。关闭详细工作计数
  不会移除插桩。统计仅读取 `step3b_split_sibling_list` trace 事件，未使用返回的
  operation metrics，也未采集时钟、批次或任何运行时长。
- 基线 Git 版本：`{payload['base_commit']}`；实际脚本及全部 src 文件的 SHA-256
  位于 `source_sha256`。新增脚本未伪装成基线提交的一部分。
- 原始统计 JSON：`{raw_label}`。每例包含几何证书、种子、顶点序列摘要、
  交点及所在边、完整秩序列、oracle 结果、全部 split trace 事件和逐次较小侧大小。
  完整多边形顶点不重复存储，可用 `generate_polygon(n, seed, height)` 重建并核对
  `polygon_sha256`；完整 trace 保存摘要，split 统计所需事件全部保存。

```sh
PYTHONPATH=src python3 experiments/probe_geometric_inputs.py --self-check
PYTHONPATH=src python3 experiments/probe_geometric_inputs.py \\
  --seed {payload['parameters']['master_seed']} --per-size {payload['parameters']['per_size']} --height {payload['parameters']['height']} \\
  --output /新的目录/geometric_probe.json --report /新的目录/geometric_probe.md
```

程序拒绝覆盖已存在的输出。复现应使用 JSON 中记录的 Python 版本及同一源码。

## 局限与本轮边界

- 固定交点数、网格高度、通道宽度及随机生成树方法都会影响序列分布；只说明
  这个几何构造族能否出现双侧 split，不能推断其他多边形生成器或应用数据的频率。
- 起点和方向会影响算法的插入顺序。本次每个多边形只取一个预定随机起点/方向，
  没有穷举重切或镜像，也没有按结果选择较有利的遍历。
- 每规模只有 {payload['parameters']['per_size']} 个输入；没有置信区间、渐近分布或代表性声明。
  大尺寸组的多边形更宽，而高度固定，长宽比变化也是构造偏差的一部分。
- oracle 认证的是项目的 Jordan 序列模型；多边形简单性由几何构造及独立边界条件
  检查保证。checked 测试和 trace 观察不构成一般正确性或复杂度证明。
- 没有更改论文、已有生成器、已有协议、旧档案或旧 PDF；没有计时、校准或正式实验，
  本轮到生成器试探和报告为止。
"""
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def self_check():
    rectangle, _ = polygon_boundary({(0, 0), (1, 0)})
    require(len(rectangle) == 4, "rectangle simplification")
    for bad in ({(0, 0), (1, 1)}, {(0, 0), (3, 0)},
                {(x, y) for x in range(3) for y in range(3)} - {(1, 1)}):
        try:
            polygon_boundary(bad)
        except ValueError:
            pass
        else:
            raise ValueError("invalid boundary accepted")
    for size in (4, 8, 16):
        for seed in (0, 1, 2):
            first = generate_polygon(size, seed, 4)
            require(first == generate_polygon(size, seed, 4), "generation not reproducible")
            values, _ = intersection_sequence(first[0], first[1])
            require(len(values) == size and oracle(values)["valid"], "small geometry certification")
    try:
        intersection_sequence(rectangle, 0)
    except ValueError:
        pass
    else:
        raise ValueError("vertex-on-line degeneracy accepted")
    events = [dict(step="step3b_split_sibling_list", performed=True,
                   input_size=10, left_size=left, right_size=10-left) for left in (0, 1, 4, 10)]
    stats = split_statistics(events)
    require(stats["total_splits"] == 4 and stats["interior_smaller_side_sizes"] == [1, 4],
            "trace-only aggregation")
    print("Geometry self-check passed: degeneracies, holes, reproducibility, crossings, oracle and trace aggregation.")


def source_snapshot():
    paths = [Path(__file__).resolve(), *sorted((ROOT / "src").glob("*.py"))]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def run(output, report, master_seed, per_size, height):
    require(per_size >= 20, "at least 20 inputs per size are required")
    require(not output.exists() and not report.exists(), "refusing to replace existing output")
    require(output.resolve() != report.resolve(), "JSON and report paths must differ")
    require(output.parent.is_dir() and report.parent.is_dir(), "output parents must already exist")
    payload = dict(schema=SCHEMA, scope="exploratory_geometry_and_split_structure_only",
                   timing_collected=False, python_version=sys.version,
                   base_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   source_sha256=source_snapshot(),
                   parameters=dict(sizes=SIZES, per_size=per_size, master_seed=master_seed, height=height),
                   backend_options=dict(BACKEND.options), execution_policy="checked", cases=[])
    # Flush each complete case: an interrupted probe retains its recorded prefix.
    with output.open("x", encoding="utf-8") as stream:
        header = {key: value for key, value in payload.items() if key != "cases"}
        stream.write(json.dumps(header, indent=2)[:-2] + ',\n  "cases": [\n')
        for size in SIZES:
            for index in range(per_size):
                record = evaluate(size, index, case_seed(master_seed, size, index), height)
                if payload["cases"]:
                    stream.write(",\n")
                stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
                stream.flush()
                payload["cases"].append(record)
            passed = sum(case["status"] == "pass" for case in payload["cases"] if case["target_n"] == size)
            print(f"n={size}: {per_size} fixed inputs recorded; {passed} checked passes", flush=True)
        payload["summary"] = summarize(payload["cases"])
        payload["source_unchanged"] = source_snapshot() == payload["source_sha256"]
        payload["complete"] = True
        for key in ("summary", "source_unchanged", "complete"):
            stream.write(("\n  ],\n" if key == "summary" else ",\n") + f'  "{key}": ' + json.dumps(payload[key], indent=2))
        stream.write("\n}\n")
    require(payload["source_unchanged"], "source changed during probe")
    write_report(report, output, payload)
    return all(case["status"] == "pass" for case in payload["cases"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--seed", type=int, default=MASTER_SEED)
    parser.add_argument("--per-size", type=int, default=PER_SIZE)
    parser.add_argument("--height", type=int, default=HEIGHT)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/development/geometric_generator_probe_20261101.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/development/geometric_generator_probe_20261101.md")
    args = parser.parse_args()
    if args.self_check:
        self_check()
    else:
        raise SystemExit(0 if run(args.output.resolve(), args.report.resolve(), args.seed, args.per_size, args.height) else 2)
