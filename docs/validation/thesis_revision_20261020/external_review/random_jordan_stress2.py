"""Independent randomized differential stress test (correctness only, not timing).

Generator: build an open simple curve point by point. From x=z_{i-1}, the new arc
(family = parity of i) may end in any axis gap such that no same-family arc has
exactly one endpoint strictly between x and the new point. Gaps adjacent to x are
always legal, so generation never gets stuck. Values are the final ranks.
The repository oracle independently re-checks laminarity of every generated input.
"""
import json, random, sys
from collections import Counter
from pathlib import Path

REPO = Path(sys.argv[1])
sys.path.insert(0, str(REPO / "src"))
from oracle import oracle
from paper_jordan_sort import paper_jordan_sort_valid, paper_jordan_diagnostics_valid
from paper_jordan import _run_paper_jordan_state_values
from paper_execution_policy import TRACE_ONLY_POLICY
from sibling_backend_contract import SiblingBackendSpec
from heterogeneous_finger_backend import HeterogeneousFingerBackend

TREE = SiblingBackendSpec(HeterogeneousFingerBackend, (("detailed_work", False),))


def generate(n, rng, far_bias):
    state_dir = [1]
    order = [0]            # point ids in axis order
    partner = {}           # point id -> same-family partner (each point has <=1 per family)
    family_partner = ({}, {})  # family parity -> {point: partner}
    for i in range(1, n):
        fam = i % 2         # arc (i-1, i) has family parity of its end index
        fp = family_partner[fam]
        pos = {p: k for k, p in enumerate(order)}
        x = i - 1
        px = pos[x]
        legal = []
        for direction in (1, -1):
            open_count = 0
            k = px
            # gap index g means "insert before order[g]"; right gap of px is px+1
            while True:
                gap = k + 1 if direction == 1 else k
                if open_count == 0:
                    legal.append(gap)
                k += direction
                if k < 0 or k >= len(order):
                    break
                p = order[k]
                q = fp.get(p)
                if q is not None:
                    pq = pos[q]
                    inside = (px < pq < k) if direction == 1 else (k < pq < px)
                    if inside:
                        open_count -= 1
                    else:
                        open_count += 1
                        if not ((direction == 1 and pq > k) or (direction == -1 and pq < k)):
                            break  # enclosing arc: cannot close it on this side
        legal = sorted(set(legal))
        # comb phase: keep walking in one direction, placing the point just past the
        # nearest legal gap beyond the current extreme; wrap phase: random legal gap.
        if rng.random() < far_bias:
            gap = rng.choice(legal)
        else:
            if rng.random() < 0.08:
                state_dir[0] = -state_dir[0]
            side = [g for g in legal if (g > px) == (state_dir[0] == 1)]
            if not side:
                side = legal
            # go to the farthest legal gap on that side with prob .5, else the nearest
            gap = (max(side) if state_dir[0] == 1 else min(side)) if rng.random() < .5 else (min(side) if state_dir[0] == 1 else max(side))
        order.insert(gap, i)
        fp[x] = i
        fp[i] = x
    rank = {p: r for r, p in enumerate(order)}
    return [rank[i] for i in range(n)]


def two_sided_splits(values):
    state = _run_paper_jordan_state_values(list(values), execution_policy=TRACE_ONLY_POLICY, backend=TREE)
    hist = Counter()
    for ev in state.trace:
        if ev["step"] == "step3b_split_sibling_list" and ev["performed"]:
            hist["split"] += 1
            if ev["left_size"] and ev["right_size"]:
                hist["two_sided"] += 1
                hist["min_side_max"] = max(hist["min_side_max"], min(ev["left_size"], ev["right_size"]))
    return hist, state.partial_order.to_list()


def main():
    seed = int(sys.argv[2]); count = int(sys.argv[3]); nmin, nmax = int(sys.argv[4]), int(sys.argv[5])
    checked_limit = int(sys.argv[6])
    rng = random.Random(seed)
    totals = Counter(); failures = []
    for t in range(count):
        n = rng.randint(nmin, nmax)
        values = generate(n, rng, far_bias=rng.choice([0.02, 0.05, 0.1, 0.25]))
        assert sorted(values) == list(range(n))
        if not oracle(values)["valid"]:
            failures.append(("generator_invalid", values)); continue
        expected = list(range(n))
        try:
            hist, trace_out = two_sided_splits(values)
            outs = {
                "list_min": paper_jordan_sort_valid(values, "minimal", backend="ordinary_list"),
                "tree_min": paper_jordan_sort_valid(values, "minimal", backend=TREE),
                "tree_trace": trace_out,
            }
            if n <= checked_limit:
                outs["tree_checked"] = paper_jordan_diagnostics_valid(values, backend=TREE)["output"]
                totals["checked_runs"] += 1
        except Exception as exc:  # noqa: BLE001
            failures.append((f"exception:{type(exc).__name__}:{exc}", values)); continue
        for name, out in outs.items():
            if out != expected:
                failures.append((f"wrong_output:{name}", values))
        totals["inputs"] += 1
        totals["splits"] += hist["split"]
        totals["two_sided"] += hist["two_sided"]
        totals["inputs_with_two_sided"] += hist["two_sided"] > 0
        totals["max_min_side"] = max(totals["max_min_side"], hist["min_side_max"])
    print(json.dumps({"seed": seed, "totals": totals, "failures": len(failures),
                      "first_failures": [(f, v[:60], len(v)) for f, v in failures[:3]]}))


if __name__ == "__main__":
    main()
