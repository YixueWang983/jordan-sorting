"""Prepare the five-method comparison or run a separately requested formal session."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

from baseline_comparison import (CANDIDATES, FROZEN, METHODS, ROOT, SUITE, TARGET_NS,
                                 count_call, digest, inputs, reference, require, rotation, sort_methods)
from committed_records import atomic_json
from uninstrumented_protocol import parsed_power, require_power


def utc():
    return datetime.now(timezone.utc).isoformat()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identity():
    require(not git("status", "--porcelain"), "run from a clean worktree; use an external output path")
    require(not git("diff", FROZEN, "--", "src"), "production sources differ from freeze")
    files = sorted((ROOT / "src").glob("*.py"))
    require({str(p.relative_to(ROOT)) for p in files} ==
            set(git("ls-tree", "-r", "--name-only", FROZEN, "src").splitlines()), "production source inventory")
    require(platform.python_implementation() == "CPython" and gc.isenabled(), "requires CPython with automatic GC")
    return dict(commit=git("rev-parse", "HEAD"), frozen=FROZEN, suite=SUITE,
                production={p.name: file_hash(p) for p in files},
                protocol=file_hash(ROOT / "docs/plan/baseline_comparison_protocol_20261120.md"),
                python=sys.version, executable=sys.executable, flags=repr(sys.flags), os=platform.platform(),
                machine=platform.machine(), host=platform.node(), gc_thresholds=list(gc.get_threshold()),
                hardware=subprocess.check_output(["sysctl", "hw.memsize", "hw.logicalcpu", "machdep.cpu.brand_string"], text=True).strip(),
                clock=vars(time.get_clock_info("perf_counter")))


class Journal:
    def __init__(self, output, stream):
        self.output = output
        self.stream = stream
        self.location = {}

    def row(self, **fields):
        record = {**self.location, **fields}
        self.stream.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.stream.flush()

    def power(self, side):
        raw = {}
        try:
            for key, cmd in (("power", ["pmset", "-g", "batt"]), ("power_settings", ["pmset", "-g"])):
                raw[key] = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
            source, mode = parsed_power(raw["power"], raw["power_settings"])
            raw.update(power_source=source, lowpowermode=mode)
        finally:
            self.row(kind="power", side=side, time=utc(), **raw)
        require_power(raw)


def batch(sort, values, expected, size, output_hash):
    """Only the fresh sort calls, batch loop and retention lie inside the interval."""
    wall = time.perf_counter_ns()
    gc.collect()
    outputs = []
    start = time.perf_counter_ns()
    for _ in range(size):
        outputs.append(sort(values))
    end = time.perf_counter_ns()
    for index, output in enumerate(outputs):
        if output != expected:
            raise ValueError(f"output mismatch at batch call {index}: {output!r}")
    del outputs
    return dict(B=size, start_ns=start, end_ns=end, elapsed_ns=end-start,
                verified_calls=size, output_sha256=output_hash, wall_ns=time.perf_counter_ns()-wall)


def calibration(log, method, sort, case, expected, output_hash):
    for size in CANDIDATES:
        elapsed, walls = [], []
        for rep in range(3):
            log.location.update(method=method, B=size, round=rep)
            row = batch(sort, case["values"], expected, size, output_hash)
            require(digest(case["values"]) == case["input_sha256"], "input mutation")
            log.row(kind="candidate", **row)
            elapsed.append(row["elapsed_ns"])
            walls.append(row["wall_ns"])
        median = statistics.median(elapsed)
        log.row(kind="candidate_summary", median_ns=median, target_ns=TARGET_NS, selected=median >= TARGET_NS)
        if median >= TARGET_NS:
            return dict(B=size, median_ns=median, median_wall_ns=statistics.median(walls))
    raise ValueError("no qualifying B through 2^20")


def stages(mode, cases, methods, log, selected):
    phases = ("correctness", "comparisons", "calibration") if mode == "prepare" else ("formal",)
    for phase in phases:
        for i, case in enumerate(cases):
            cid = case["case_id"]
            values = case["values"]
            expected = reference(values)
            output_hash = digest(expected)
            base = dict(phase=phase, case=cid, input_sha256=case["input_sha256"], n=case["n"], index=i)
            log.location = base.copy()
            if phase in ("calibration", "formal"):
                log.power("before")
            if phase == "formal":
                for kind, rounds in (("warmup", 5), ("sample", 20)):
                    for rep in range(rounds):
                        for position, m in enumerate(rotation(i, rep)):
                            size = 1 if kind == "warmup" else selected[cid][m]["B"]
                            log.location = dict(base, method=m, round=rep, position=position, B=size, kind=kind)
                            row = batch(methods[m], values, expected, size, output_hash)
                            require(digest(values) == case["input_sha256"], "input mutation")
                            log.row(**row)
            else:
                for position, (m, sort) in enumerate(methods.items()):
                    log.location = dict(base, method=m, position=position)
                    if phase == "correctness":
                        result = sort(values)
                        require(result == expected, f"incorrect result: {result!r}")
                        log.row(kind="output", output=result, output_sha256=output_hash)
                    elif phase == "comparisons":
                        counts = count_call(sort, values, expected)
                        log.row(kind="counts", counts=counts, output_sha256=output_hash)
                    else:
                        selected[cid][m] = calibration(log, m, sort, case, expected, output_hash)
                    require(digest(values) == case["input_sha256"], "input mutation")
            if phase in ("calibration", "formal"):
                log.location = base.copy()
                log.power("after")
            if (i+1) % 25 == 0 or i+1 == len(cases):
                print(f"{utc()} {phase} {i+1}/{len(cases)}", flush=True)


def read_json(path):
    return json.loads(path.read_bytes())


def load_completed(path):
    manifest = read_json(path / "complete.json")
    for name, sha in manifest["files"].items():
        require(file_hash(path / name) == sha, f"archive file changed: {name}")
    return manifest


def execute(mode, output, preparation):
    output = output.resolve()
    require(not output.is_relative_to(ROOT), "choose an output directory outside the worktree")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "records.jsonl").open("x") as stream:
        log = Journal(output, stream)
        try:
            env = identity()
            cases = inputs()
            methods = sort_methods()
            config = dict(mode=mode, identity=env, start_utc=utc(), command=sys.orig_argv,
                          case_order=[c["case_id"] for c in cases], methods=list(METHODS))
            selected = defaultdict(dict)
            if mode == "formal":
                require(preparation is not None, "formal session needs a completed preparation directory")
                manifest = load_completed(preparation)
                prep_config = read_json(preparation / "config.json")
                require(prep_config["mode"] == "prepare" and prep_config["identity"] == env
                        and prep_config["case_order"] == config["case_order"], "preparation identity mismatch")
                selected = read_json(preparation / "calibration.json")
                config.update(preparation_manifest=digest(manifest))
            atomic_json(output / "config.json", config)
            stages(mode, cases, methods, log, selected)
            require(identity() == env, "execution identity changed")
            files = ["config.json", "records.jsonl"]
            if mode == "prepare":
                atomic_json(output / "calibration.json", selected)
                files.append("calibration.json")
            atomic_json(output / "complete.json", dict(end_utc=utc(), files={n:file_hash(output/n) for n in files}))
        except BaseException as exc:
            atomic_json(output / "failure.json", dict(time=utc(), location=log.location, error=repr(exc)))
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "formal"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preparation", type=Path)
    args = parser.parse_args()
    execute(args.mode, args.output, args.preparation)
