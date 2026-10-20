"""Bounded post-review diagnostics; never a formal campaign or qualification."""
import sys
if sys.flags.optimize:
    raise RuntimeError("Run evidence checks without Python optimization")

import argparse
import ast
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = "19a553fb9a089fae726c4ba49c5412a9e4bd12d3"
sys.path[:0] = [str(REPO / "src"), str(REPO / "experiments")]
from committed_records import atomic_json, canonical, commit_record, read_records


def sha(data):
    return hashlib.sha256(data).hexdigest()


def command(*args):
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


def freeze(out):
    """Fix all inputs/configuration before any diagnostic sorting or timing."""
    out.mkdir()
    log = (HERE / "external_review/wrapper.log").read_text()
    cases = list(json.loads(log.splitlines()[0].split(" ", 1)[1]))
    assert len(cases) == 15
    requests = REPO / "docs/validation/common_qualification_v2_20261015/qualification/requests"
    inputs = {}
    for case in cases:
        inputs[case] = json.loads((requests / (case + ".json")).read_text())["values"]
    original = (HERE / "external_review/random_jordan_stress2.py").read_text()
    function = next(n for n in ast.parse(original).body
                    if isinstance(n, ast.FunctionDef) and n.name == "generate")
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<supplied-generate>", "exec"),
         namespace)
    stress = []
    # Bounded, predetermined cells. Not a reproduction of the reviewer's 1,900 cases.
    for seed in (11, 12, 13, 14):
        rng = random.Random(seed)
        for n in (128, 512, 513, 1500):
            for bias in (.05, .25):
                name = f"stress-{seed}-{n}-{bias}"
                inputs[name] = namespace["generate"](n, rng, bias)
                stress.append(dict(case=name, seed=seed, n=n, bias=bias, checked=False))
    for seed in (21, 22):
        rng = random.Random(seed)
        for n in (32, 33, 64, 70):
            name = f"checked-{seed}-{n}"
            inputs[name] = namespace["generate"](n, rng, .1)
            stress.append(dict(case=name, seed=seed, n=n, bias=.1, checked=True))
    assert not command("git", "diff", BASE, "--", "src", "experiments", "tests")
    source = {str(p.relative_to(REPO)): sha(p.read_bytes())
              for p in sorted((REPO / "src").glob("*.py"))}
    atomic_json(out / "inputs.json", inputs)
    protocol = dict(
        purpose="post_review_exploratory_diagnostic_and_bounded_correctness",
        producing_source=BASE, formal=False, script_sha256=sha(Path(__file__).read_bytes()),
        inputs_sha256=sha((out / "inputs.json").read_bytes()), source_sha256=source,
        diagnostic_cases=cases, variants=["list", "tree", "tree_nofa", "tree_nowr"],
        warmups=3, batches=15, calls_below_256=25, calls_at_least_256=7,
        ordering="case order from supplied log; variant order rotated by case index",
        scope="fresh public minimal calls plus output append; check EVERY output after timer",
        gc="enabled; gc.collect before each batch; no collection inside timer requested",
        worker_budget_seconds=180, campaign_budget_seconds=900,
        stress=stress, generator_sha256=sha(original.encode()),
        generator_rule="same supplied generate function; fixed sequential RNG per seed",
        failure_rule="stop campaign; preserve completed records, current case and failure",
        python=sys.version, executable=sys.executable, machine=platform.machine(),
        platform=platform.platform(), python_optimize=sys.flags.optimize,
        cpu=command("sysctl", "-n", "machdep.cpu.brand_string"),
        memory_bytes=command("sysctl", "-n", "hw.memsize"),
        power=command("pmset", "-g", "batt"), started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        gc_thresholds=list(gc.get_threshold()), gc_enabled=gc.isenabled(),
        checkout_dirty=bool(command("git", "status", "--porcelain")),
    )
    atomic_json(out / "protocol.json", protocol)


def worker(out, kind, case, variant):
    protocol = json.loads((out / "protocol.json").read_text())
    assert protocol["script_sha256"] == sha(Path(__file__).read_bytes())
    assert protocol["inputs_sha256"] == sha((out / "inputs.json").read_bytes())
    for path, digest in protocol["source_sha256"].items():
        assert sha((REPO / path).read_bytes()) == digest
    from oracle import oracle
    from paper_jordan_sort import paper_jordan_sort_valid, paper_jordan_diagnostics_valid
    from paper_jordan import _run_paper_jordan_state_values
    from paper_execution_policy import TRACE_ONLY_POLICY
    from sibling_backend_contract import SiblingBackendSpec
    import heterogeneous_finger_backend as hfb
    import heterogeneous_finger_split as hfs
    values = json.loads((out / "inputs.json").read_text())[case]
    expected = sorted(values)
    assert oracle(values)["valid"]
    modifications = []
    if variant in ("tree_nofa", "tree_nowr"):
        for name in ("__getattribute__", "__setattr__"):
            delattr(hfb._Tracked, name)
            modifications.append("_Tracked." + name)
    if variant == "tree_nowr":
        for cls in (hfb.HeterogeneousFingerBackend, hfs.TreeOperations):
            for name, value in list(vars(cls).items()):
                inner = getattr(value, "__wrapped__", None)
                if inner is not None and not isinstance(value, (staticmethod, classmethod, property)):
                    setattr(cls, name, inner)
                    modifications.append(cls.__name__ + "." + name)
    backend = ("ordinary_list" if variant == "list" else
               SiblingBackendSpec(hfb.HeterogeneousFingerBackend, (("detailed_work", False),)))
    job = out / (kind + "-" + case + ("-" + variant if kind == "wrapper" else ""))
    job.mkdir()
    atomic_json(job / "identity.json", dict(case=case, kind=kind, variant=variant,
                modifications=modifications, input_sha256=sha(canonical(values)),
                protocol_sha256=sha((out / "protocol.json").read_bytes())))
    if kind == "wrapper":
        for i in range(protocol["warmups"]):
            result = paper_jordan_sort_valid(values, "minimal", backend=backend)
            commit_record(job, i, dict(phase="warmup", index=i, outputs=[result]))
            assert result == expected
        calls = protocol["calls_below_256"] if len(values) < 256 else protocol["calls_at_least_256"]
        for i in range(protocol["batches"]):
            atomic_json(out / "progress.json", dict(kind=kind, case=case, variant=variant, batch=i))
            gc.collect()
            outputs = []
            start = time.perf_counter_ns()
            for _ in range(calls):
                outputs.append(paper_jordan_sort_valid(values, "minimal", backend=backend))
            elapsed = time.perf_counter_ns() - start
            commit_record(job, protocol["warmups"] + i,
                          dict(phase="batch", index=i, calls=calls, elapsed_ns=elapsed, outputs=outputs))
            assert all(result == expected for result in outputs)
    else:
        spec = next(c for c in protocol["stress"] if c["case"] == case)
        state = _run_paper_jordan_state_values(values, execution_policy=TRACE_ONLY_POLICY, backend=backend)
        outputs = {
            "tree_trace": state.partial_order.to_list(),
            "tree_minimal": paper_jordan_sort_valid(values, "minimal", backend=backend),
            "list_minimal": paper_jordan_sort_valid(values, "minimal", backend="ordinary_list"),
        }
        if spec["checked"]:
            outputs["tree_checked_fresh_prefix_replay"] = paper_jordan_diagnostics_valid(values, backend=backend)["output"]
        commit_record(job, 0, dict(case=case, outputs=outputs, trace=state.trace,
                                  processed_count=state.processed_count))
        assert state.processed_count == len(values)
        assert all(result == expected for result in outputs.values())


def rebuild(out):
    """Rebuild every summary from saved individual outputs/times and split traces."""
    p = json.loads((out / "protocol.json").read_text())
    values = json.loads((out / "inputs.json").read_text())
    assert sha((out / "inputs.json").read_bytes()) == p["inputs_sha256"]
    timing = {}
    total_batches = total_calls = warmups = 0
    for case in p["diagnostic_cases"]:
        timing[case] = {}
        for variant in p["variants"]:
            rows = read_records(out / ("wrapper-" + case + "-" + variant))
            assert len(rows) == p["warmups"] + p["batches"]
            samples = []
            for index, row in enumerate(rows):
                assert all(x == sorted(values[case]) for x in row["outputs"])
                if index < p["warmups"]:
                    assert row["phase"] == "warmup" and row["index"] == index
                    assert len(row["outputs"]) == 1
                    warmups += 1
                else:
                    calls = p["calls_below_256"] if len(values[case]) < 256 else p["calls_at_least_256"]
                    assert row["phase"] == "batch" and row["index"] == index - p["warmups"]
                    assert row["calls"] == len(row["outputs"]) == calls
                    assert type(row["elapsed_ns"]) is int and row["elapsed_ns"] > 0
                    samples.append(row["elapsed_ns"] / calls / 1e6)
                    total_calls += calls
                    total_batches += 1
            timing[case][variant] = statistics.median(samples)
        t = timing[case]
        t["nofa_reduction_fraction"] = 1 - t["tree_nofa"] / t["tree"]
        t["nofa_list_ratio"] = t["tree_nofa"] / t["list"]
        t["instrumented_list_ratio"] = t["tree"] / t["list"]
    stress = []
    for spec in p["stress"]:
        case = spec["case"]
        rows = read_records(out / ("stress-" + case))
        assert len(rows) == 1
        row = rows[0]
        assert row["processed_count"] == len(values[case]) == spec["n"]
        modes = {"tree_trace", "tree_minimal", "list_minimal"}
        if spec["checked"]:
            modes.add("tree_checked_fresh_prefix_replay")
        assert set(row["outputs"]) == modes
        assert all(x == list(range(spec["n"])) for x in row["outputs"].values())
        events = [e for e in row["trace"] if e["step"] == "step3b_split_sibling_list" and e["performed"]]
        both = [e for e in events if e["left_size"] and e["right_size"]]
        stress.append(dict(**spec, splits=len(events), two_sided=len(both),
                           max_smaller_side=max([min(e["left_size"], e["right_size"]) for e in both], default=0)))
    result = dict(formal=False, all_saved_outputs_checked=True, diagnostic=timing,
                  batches=total_batches, timed_calls=total_calls, warmup_calls=warmups,
                  stress=stress, stress_inputs=len(stress),
                  stress_two_sided=sum(c["two_sided"] for c in stress),
                  stress_inputs_with_two_sided=sum(c["two_sided"] > 0 for c in stress),
                  stress_checked_inputs=sum(c["checked"] for c in stress),
                  stress_max_smaller_side=max(c["max_smaller_side"] for c in stress))
    return result


def run(out):
    p = json.loads((out / "protocol.json").read_text())
    start = time.monotonic()
    jobs = []
    for i, case in enumerate(p["diagnostic_cases"]):
        order = p["variants"][i % 4:] + p["variants"][:i % 4]
        jobs.extend(("wrapper", case, v) for v in order)
    jobs.extend(("stress", c["case"], "tree") for c in p["stress"])
    for index, (kind, case, variant) in enumerate(jobs):
        atomic_json(out / "progress.json", dict(job=index, kind=kind, case=case, variant=variant))
        cmd = [sys.executable, str(Path(__file__).resolve()), "worker", str(out), kind, case, variant]
        remaining = p["campaign_budget_seconds"] - (time.monotonic() - start)
        try:
            assert remaining > 0, "campaign budget exhausted"
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=min(p["worker_budget_seconds"], remaining))
            atomic_json(out / f"process-{index:03d}.json",
                        dict(command=cmd, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
            assert result.returncode == 0, result.stderr
        except Exception as exc:
            atomic_json(out / "failure.json", dict(complete=False, job=index,
                        kind=kind, case=case, variant=variant, error=str(exc), type=type(exc).__name__))
            raise
        print(f"{index+1}/{len(jobs)} {kind} {case} {variant}", flush=True)
    atomic_json(out / "summary.json", rebuild(out))
    atomic_json(out / "completion.json", dict(complete=True, formal=False, jobs=len(jobs),
                elapsed_seconds=time.monotonic()-start, completed_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "run", "check", "worker"))
    parser.add_argument("output", type=Path)
    parser.add_argument("job", nargs="*")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze(args.output.resolve())
    elif args.action == "run":
        run(args.output.resolve())
    elif args.action == "check":
        result = rebuild(args.output.resolve())
        assert result == json.loads((args.output / "summary.json").read_text())
        print(json.dumps(result, indent=2))
    else:
        worker(args.output.resolve(), *args.job)
