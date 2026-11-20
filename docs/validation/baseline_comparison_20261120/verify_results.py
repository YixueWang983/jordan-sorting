"""Recompute the supplemental summaries from raw JSONL, independent of the runner."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import random
from statistics import median

METHODS = ("ordinary_list", "heterogeneous_finger_uninstrumented", "merge_sort", "quick_sort", "sorted")
BANDS = ((32, 33), (64, 70), (128, 129), (256, 257), (512, 513), (32, 513))


def require(condition, description):
    if not condition:
        raise ValueError(description)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def records(directory):
    manifest = json.loads((directory / "complete.json").read_bytes())
    for name, sha in manifest["files"].items():
        with (directory / name).open("rb") as f:
            require(hashlib.file_digest(f, "sha256").hexdigest() == sha, name)
    with (directory / "records.jsonl").open() as f:
        for line in f:
            yield json.loads(line)


def audit(base, suite_path, table):
    suite = json.loads(suite_path.read_bytes())
    require(suite.pop("suite_sha256") == digest(suite), "registered inputs")
    cases = {c["case_id"]: c for c in suite["entries"]}
    order = list(cases)
    random.Random(20261120).shuffle(order)
    expected = {cid: sorted(c["values"]) for cid, c in cases.items()}
    hashes = {cid: digest(values) for cid, values in expected.items()}
    counts, correct = {}, set()
    trials = defaultdict(lambda: defaultdict(list))
    powers = Counter()
    samples, warmups, slots = defaultdict(list), Counter(), defaultdict(Counter)
    calls = Counter()
    for phase in ("preparation", "formal"):
        path = base / phase
        for r in records(path):
            cid = r["case"]
            c = cases[cid]
            require(order[r["index"]] == cid and r["n"] == c["n"] and
                    c["input_sha256"] == r["input_sha256"], "case identity")
            kind = r["kind"]
            if kind == "power":
                require(r["power_source"] == "AC Power" and r["lowpowermode"] == "0", "power gate")
                powers[phase, cid, r["side"]] += 1
                continue
            method = r["method"]
            key = (cid, method)
            require(method in METHODS, "method")
            if kind == "candidate_summary":
                continue
            require(r["output_sha256"] == hashes[cid], "output digest")
            if kind == "output":
                require(r["output"] == expected[cid] and key not in correct, "qualification")
                correct.add(key)
            elif kind == "counts":
                v = r["counts"]
                require(sum(v[k] for k in ("lt", "le", "gt", "ge")) == v["total"] and key not in counts, "key count")
                counts[key] = v["total"]
            else:
                b = r["B"]
                dt = r["end_ns"] - r["start_ns"]
                require(dt == r["elapsed_ns"] and dt > 0 and b == r["verified_calls"], "batch")
                calls[kind] += b
                if kind == "candidate":
                    trials[key][b].append(dt)
                else:
                    require(method == METHODS[(r["index"] + r["round"] + r["position"]) % 5], "rotation")
                    if kind == "sample":
                        selected = min(size for size, raw in trials[key].items() if median(raw) >= 10_000_000)
                        require(b == selected, "selected B")
                        samples[key].append(dt / b)
                        slots[key][r["position"]] += 1
                    else:
                        require(kind == "warmup" and b == 1, "warmup")
                        warmups[key] += 1

    all_keys = {(cid, m) for cid in cases for m in METHODS}
    require(correct == set(counts) == set(trials) == set(samples) == all_keys, "coverage")
    for key in all_keys:
        require(len(samples[key]) == 20 and warmups[key] == 5 and all(slots[key][j] == 4 for j in range(5)), "schedule")
        sizes = sorted(trials[key])
        require(sizes == [1 << j for j in range(len(sizes))] and
                all(len(trials[key][size]) == 3 for size in sizes), "calibration series")
    require(all(powers[p, cid, side] == 1 for p in ("preparation", "formal")
                for cid in cases for side in ("before", "after")), "power coverage")
    t = {key: median(batch) for key, batch in samples.items()}
    with table.open() as f:
        rows = list(csv.DictReader(f))
    require(len(rows) == len(BANDS), "table bands")
    for row, (lo, hi) in zip(rows, BANDS):
        ids = [cid for cid,c in cases.items() if lo <= c["n"] <= hi]
        require(len(ids) == int(row["inputs"]), "band size")
        for m in METHODS:
            ratio = median(t[cid,m]/t[cid,METHODS[0]] for cid in ids)
            require(ratio == float(row[m+"_ratio"]), "table median ratio")
        for j in METHODS[:2]:
            for m in METHODS[2:4]:
                require(sum(t[i,j] < t[i,m] for i in ids) == int(row[j+"_faster_than_"+m]), "table wins")

    by_n = {}
    for n in sorted({c["n"] for c in cases.values()}):
        ids = [cid for cid,c in cases.items() if c["n"] == n]
        by_n[n] = {m: dict(us=median(t[i,m] for i in ids)/1000, comparisons_per_key=median(counts[i,m]/n for i in ids))
                   for m in METHODS}
    paired = {}
    for j in METHODS[:2]:
        paired[j] = {}
        for m in METHODS[2:]:
            ratios = [t[i,j]/t[i,m] for i in cases]
            paired[j][m] = [min(ratios), median(ratios), max(ratios)]
    return dict(by_n=by_n, paired_slowdown_min_median_max=paired, sorted_calls_checked=dict(calls),
                tree_faster_than_list=sum(t[i,METHODS[1]] < t[i,METHODS[0]] for i in cases))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raw", type=Path, help="directory containing preparation/ and formal/")
    p.add_argument("suite", type=Path)
    p.add_argument("table", type=Path)
    args = p.parse_args()
    print(json.dumps(audit(args.raw, args.suite, args.table), indent=2))
