"""Read-only reconstruction of the bounded local supplement; no sorter calls."""
import sys
if sys.flags.optimize:
    raise RuntimeError("Run evidence checks without Python optimization")

import gzip
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

D = Path(__file__).resolve().parent
R = D.parents[2]
OLD = D.parent / "thesis_revision_20261020"
A = OLD / "local_supplement"
def read(path):
    return json.loads(path.read_text())
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
def records(directory, count):
    paths = sorted((directory / "records").iterdir())
    assert [p.name for p in paths] == [f"{i:06d}.json.gz" for i in range(count)]
    assert set(p.name for p in directory.iterdir()) == {"identity.json", "records"}
    assert all(p.is_file() and not p.is_symlink() for p in paths)
    return [json.loads(gzip.decompress(p.read_bytes())) for p in paths]

p = read(A / "protocol.json")
s = read(A / "summary.json")
values = read(A / "inputs.json")
assert p["formal"] is False and p["python_optimize"] == 0
assert p["script_sha256"] == sha(OLD / "run_supplement.py")
assert p["inputs_sha256"] == sha(A / "inputs.json")
assert p["generator_sha256"] == sha(OLD / "external_review/random_jordan_stress2.py")
assert p["producing_source"] == "19a553fb9a089fae726c4ba49c5412a9e4bd12d3"
for path, digest in p["source_sha256"].items():
    assert sha(R / path) == digest
    bound = subprocess.check_output(["git", "show", p["producing_source"] + ":" + path], cwd=R)
    assert hashlib.sha256(bound).hexdigest() == digest
assert len(p["diagnostic_cases"]) == 15 and len(p["stress"]) == 40
assert len({hashlib.sha256(canon(values[c["case"]])).hexdigest() for c in p["stress"]}) == 40
assert p["variants"] == ["list", "tree", "tree_nofa", "tree_nowr"]
assert (p["warmups"], p["batches"], p["calls_below_256"], p["calls_at_least_256"]) == (3, 15, 25, 7)

timing = {}
batches = calls = warmups = 0
jobs = []
for ci, case in enumerate(p["diagnostic_cases"]):
    order = p["variants"][ci % 4:] + p["variants"][:ci % 4]
    jobs.extend(("wrapper", case, v) for v in order)
    timing[case] = {}
    for variant in p["variants"]:
        directory = A / ("wrapper-" + case + "-" + variant)
        identity = read(directory / "identity.json")
        assert (identity["case"], identity["kind"], identity["variant"]) == (case, "wrapper", variant)
        assert identity["input_sha256"] == hashlib.sha256(canon(values[case])).hexdigest()
        assert identity["protocol_sha256"] == sha(A / "protocol.json")
        mods = identity["modifications"]
        if variant in ("list", "tree"):
            assert mods == []
        else:
            assert mods[:2] == ["_Tracked.__getattribute__", "_Tracked.__setattr__"]
            assert len(mods) == 2 if variant == "tree_nofa" else len(mods) > 2
        rows = records(directory, 18)
        durations = []
        for i, row in enumerate(rows):
            expected_calls = 1 if i < 3 else (25 if len(values[case]) < 256 else 7)
            assert len(row["outputs"]) == expected_calls
            assert all(output == sorted(values[case]) for output in row["outputs"])
            if i < 3:
                assert row["phase"] == "warmup" and row["index"] == i
                warmups += 1
            else:
                assert row["phase"] == "batch" and row["index"] == i - 3
                assert type(row["calls"]) is int and row["calls"] == expected_calls
                assert type(row["elapsed_ns"]) is int and row["elapsed_ns"] > 0
                durations.append(row["elapsed_ns"] / expected_calls / 1e6)
                batches += 1
                calls += expected_calls
        timing[case][variant] = statistics.median(durations)
    t = timing[case]
    t["nofa_reduction_fraction"] = 1 - t["tree_nofa"] / t["tree"]
    t["nofa_list_ratio"] = t["tree_nofa"] / t["list"]
    t["instrumented_list_ratio"] = t["tree"] / t["list"]
assert timing == s["diagnostic"]

stress = []
event_names = ["step1_find_predecessor", "step1_select_boundary_pair",
               "step2_find_successor", "step2_select_boundary_pair",
               "step3a_insert_pair", "step3b_split_sibling_list", "step3c_insert_output_point"]
for spec in p["stress"]:
    case, n = spec["case"], spec["n"]
    jobs.append(("stress", case, "tree"))
    directory = A / ("stress-" + case)
    identity = read(directory / "identity.json")
    assert identity == dict(case=case, kind="stress", variant="tree", modifications=[],
                           input_sha256=hashlib.sha256(canon(values[case])).hexdigest(),
                           protocol_sha256=sha(A / "protocol.json"))
    row, = records(directory, 1)
    assert sorted(values[case]) == list(range(n))
    assert row["case"] == case and row["processed_count"] == n
    modes = {"tree_minimal", "list_minimal", "tree_trace"}
    if spec["checked"]:
        modes.add("tree_checked_fresh_prefix_replay")
    assert set(row["outputs"]) == modes
    assert all(output == list(range(n)) for output in row["outputs"].values())
    trace = row["trace"]
    assert len(trace) == 2 + 7 * (n - 3)
    splits = []
    both = []
    for i in range(4, n + 1):
        iteration = trace[2+7*(i-4):2+7*(i-3)]
        assert [e["step"] for e in iteration] == event_names
        assert all(e["iteration"] == i for e in iteration)
        e = iteration[5]
        assert type(e["performed"]) is bool
        if e["performed"]:
            assert e["input_size"] == e["left_size"] + e["right_size"] > 0
            assert all(type(e[k]) is int and e[k] >= 0
                       for k in ("input_size", "left_size", "right_size"))
            assert type(e["input_list_id"]) is int and e["input_list_id"] > 0
            for side in ("left", "right"):
                lid = e[side + "_list_id"]
                if e[side + "_size"]:
                    assert type(lid) is int and lid > 0 and lid != e["input_list_id"]
                else:
                    assert lid is None
            splits.append(e)
            if e["left_size"] and e["right_size"]:
                assert e["left_list_id"] != e["right_list_id"]
                both.append(e)
        else:
            assert all(e[k] == 0 for k in ("input_size", "left_size", "right_size"))
            assert all(e[k] is None for k in ("input_list_id", "left_list_id", "right_list_id"))
    stress.append(dict(**spec, splits=len(splits), two_sided=len(both),
                       max_smaller_side=max([min(e["left_size"], e["right_size"]) for e in both], default=0)))
assert stress == s["stress"]
assert (batches, calls, warmups) == (s["batches"], s["timed_calls"], s["warmup_calls"]) == (900, 11700, 180)
assert sum(c["two_sided"] for c in stress) == s["stress_two_sided"] == 678
assert sum(c["two_sided"] > 0 for c in stress) == s["stress_inputs_with_two_sided"] == 38
assert sum(c["checked"] for c in stress) == s["stress_checked_inputs"] == 8
assert max(c["max_smaller_side"] for c in stress) == s["stress_max_smaller_side"] == 13
assert s["stress_inputs"] == 40 and s["formal"] is False and s["all_saved_outputs_checked"] is True
for i, (kind, case, variant) in enumerate(jobs):
    process = read(A / f"process-{i:03d}.json")
    assert process["returncode"] == 0 and not process["stdout"] and not process["stderr"]
    assert process["command"][-3:] == [kind, case, variant]
assert read(A / "completion.json")["complete"] is True
assert not (A / "failure.json").exists()


import re
tex = (R / "thesis/chapters/results.tex").read_text()
body = tex.split(r"\label{tab:results-hooks}", 1)[1].split(r"\end{table}", 1)[0]
actual_rows = [line for line in body.splitlines() if re.match(r"^\d+ & ", line)]
table = []
details = []
for case in p["diagnostic_cases"]:
    n = len(values[case])
    label = next(label for category, label in (
        ("low_nesting_valid", "Low"), ("medium_nesting_valid", "Medium"),
        ("nested_heavy_valid", "Heavy"), ("strict_flat", "Strict-flat")
    ) if category in case)
    direction = "Mirror" if case.endswith("-mirror") else "Original"
    t = timing[case]
    tr = t["tree"] / t["list"]
    hr = t["tree_nofa"] / t["list"]
    ur = t["tree_nowr"] / t["list"]
    drop = 100 * (1 - t["tree_nofa"] / t["tree"])
    line = f"{n} & {label} & {direction} & {tr:.3f} & {hr:.3f} & {ur:.3f} & {drop:.1f}" + r"\\"
    table.append(line)
    details.append(dict(case=case, n=n, T_over_L=tr, H_over_L=hr,
                        U_over_L=ur, drop_percent=drop))
assert len(actual_rows) == len(table) == 15
assert actual_rows == table, "Diagnostic rows differ from raw-record reconstruction"
faster = [r for r in details if r["H_over_L"] < 1]
slower = [r for r in details if r["H_over_L"] > 1]
assert len(faster) == 4 and len(slower) == 11
assert all(r["n"] in (512, 513) and "nested_heavy" in r["case"] for r in faster)
slow_range = [min(r["H_over_L"] for r in slower), max(r["H_over_L"] for r in slower)]
assert [f"{v:.2f}" for v in slow_range] == ["1.09", "1.68"]
for path in ("chapters/results.tex", "chapters/conclusion.tex", "frontmatter/abstract.tex"):
    prose = (R / "thesis" / path).read_text().lower()
    assert "four of fifteen" in prose and "eleven" in prose and "1.09--1.68" in prose
print(json.dumps(dict(scope="read_only_all_local_records_and_all_15_diagnostic_rows",
    formal=False, sorter_executed=False, source_binding=p["producing_source"],
    raw_archive_revision="2da8b662bf3c50c1bd51ee85ed2215a72a34f7c7",
    checker_sha256=sha(Path(__file__)),
    batches=batches, timed_outputs=calls, warmup_outputs=warmups,
    stress_inputs=40, stress_two_sided=678, checked_inputs=8,
    protocol_sha256=sha(A / "protocol.json"), summary_sha256=sha(A / "summary.json"),
    diagnostic_table_rows=table, diagnostic_cases=details,
    hook_free_faster_cases=len(faster), hook_free_slower_cases=len(slower),
    slower_ratio_range=slow_range,
    limits="Output/record reconstruction; no independent decoding of large-case physical trees or general proof."),
    indent=2))
