"""Fixed, constructor-only follow-up. Never invokes a sorting entry point."""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from types import MethodType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]
from committed_records import atomic_json, commit_record, read_records
from common_input_protocol import source_identity
from heterogeneous_finger_backend import HeterogeneousFingerBackend
from input_suite_protocol import environment_equal
from matched_measurement import capture_environment
from paper_execution_policy import MINIMAL_POLICY
from uninstrumented_finger import prepare_uninstrumented
from uninstrumented_protocol import power_observation, require_power, require_machine


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_manifest(output):
    atomic_json(output / "manifest.json", {
        str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*"))
        if p.is_file() and p != output / "manifest.json"})


def audit(instances, instrumented, callback, family):
    for obj in instances:
        assert type(obj) is HeterogeneousFingerBackend
        assert obj.execution_policy is MINIMAL_POLICY and obj._point_value is callback
        assert obj.instrumented is instrumented and obj.detailed_work is False
        assert all(getattr(obj, k) == {} for k in ("_pairs", "_lists", "_nodes", "_dummies"))
        assert obj._next_list_id == obj._next_node_id == 1
        assert obj._pending_split is None and obj._pending_transfer is None
        if instrumented:
            assert obj.work.enabled is False and "_uninstrumented_family" not in vars(obj)
        else:
            assert obj.work is None and obj._uninstrumented_family is family
            for name, method in family.methods.items():
                bound = vars(obj)[name]
                if isinstance(method, staticmethod):
                    assert bound is method.__func__
                else:
                    assert isinstance(bound, MethodType) and bound.__self__ is obj
                    assert bound.__func__ is method


def measure(instrumented, count, callback, family):
    instances = [None] * count
    indices = range(count)
    collected_before = gc.collect()
    counts_before, stats_before = gc.get_count(), gc.get_stats()
    start = time.perf_counter_ns()
    for i in indices:
        instances[i] = HeterogeneousFingerBackend(
            callback, execution_policy=MINIMAL_POLICY,
            detailed_work=False, instrumented=instrumented)
    finish = time.perf_counter_ns()
    counts_after, stats_after = gc.get_count(), gc.get_stats()
    assert finish > start
    audit(instances, instrumented, callback, family)
    instances.clear()
    collected_after = gc.collect()
    return dict(start_ns=start, finish_ns=finish, elapsed_ns=finish-start,
                constructors=count, instance_audit_passed=True,
                gc_counts_before=counts_before, gc_counts_after=counts_after,
                gc_stats_before=stats_before, gc_stats_after=stats_after,
                explicit_gc_collected_before=collected_before,
                explicit_gc_collected_after=collected_after)


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    index = 0
    try:
        protocol = json.loads((HERE / "protocol.json").read_text())
        cfg = protocol["constructor"]
        assert cfg["warmup_paired_rounds"] == 5 and cfg["sample_paired_rounds"] == 50
        assert cfg["constructors_per_batch"] == 256
        assert sys.flags.optimize == 0 and gc.isenabled()
        assert list(gc.get_threshold()) == cfg["gc_thresholds"] == [700, 10, 10]
        bound_files = [HERE / name for name in ("protocol.json", "PLAN.md", "benchmark.py", "analyze.py", "verify.py")]
        bound_hashes = {p.name: sha(p) for p in bound_files}
        environment = capture_environment(configuration="uninstrumented")
        environment["execution"]["purpose"] = "post-formal constructor-only microbenchmark"
        execution = environment["execution"]
        atomic_json(output / "environment.json", environment)
        require_machine(execution)
        assert not execution["dirty"]
        reference = json.loads((ROOT / protocol["stability"]["second"] / "environment.json").read_text())
        environment_equal(execution, reference["execution"])
        family = prepare_uninstrumented()
        assert prepare_uninstrumented() is family and len(family.methods) == 54
        values = {int(k): v for k, v in cfg["point_values"].items()}
        callback = values.__getitem__
        atomic_json(output / "config.json", dict(
            schema="constructor_microbenchmark_v1", plan=protocol,
            plan_sources_sha256=bound_hashes, preparation_outside_timer=True,
            generated_methods=len(family.methods), projection=family.projection,
            started_at=datetime.now(timezone.utc).isoformat(),
            first_formal_manifest_sha256=sha(ROOT / protocol["stability"]["first"] / "manifest.json"),
            second_formal_manifest_sha256=sha(ROOT / protocol["stability"]["second"] / "manifest.json")))
        atomic_json(output / "processes_before.json", dict(
            command="ps -axo pid,ppid,%cpu,comm",
            output=subprocess.check_output(["ps", "-axo", "pid,ppid,%cpu,comm"], text=True)))
        start_wall = time.monotonic()
        for kind, rounds in (("warmup", cfg["warmup_paired_rounds"]), ("sample", cfg["sample_paired_rounds"])):
            for round_index in range(rounds):
                order = (True, False) if round_index % 2 == 0 else (False, True)
                for position, instrumented in enumerate(order):
                    if time.monotonic() - start_wall > cfg["wall_budget_seconds"]:
                        raise TimeoutError("fixed follow-up wall budget exceeded")
                    assert gc.isenabled() and list(gc.get_threshold()) == cfg["gc_thresholds"]
                    before = power_observation()
                    atomic_json(output / "power_checkpoint.json", dict(record_index=index, when="before", observation=before))
                    require_power(before)
                    record = measure(instrumented, cfg["constructors_per_batch"], callback, family)
                    after = power_observation()
                    atomic_json(output / "power_checkpoint.json", dict(record_index=index, when="after", observation=after))
                    try:
                        require_power(after)
                        power_ok = True
                    except (ValueError, RuntimeError):
                        power_ok = False
                    record.update(index=index, kind=kind, round=round_index, position=position,
                                  configuration="instrumented" if instrumented else "uninstrumented",
                                  power_before=before, power_after=after, power_passed=power_ok,
                                  status="PASS" if power_ok else "ERROR")
                    commit_record(output, index, record)
                    index += 1
                    if not power_ok:
                        raise RuntimeError("post-batch power gate failed")
                if kind == "warmup" or (round_index+1) % 10 == 0:
                    print(f"{kind}: paired rounds completed {round_index+1}/{rounds}", flush=True)
        assert source_identity() == execution["source_sha256"]
        assert {p.name: sha(p) for p in bound_files} == bound_hashes
        atomic_json(output / "processes_after.json", dict(
            command="ps -axo pid,ppid,%cpu,comm",
            output=subprocess.check_output(["ps", "-axo", "pid,ppid,%cpu,comm"], text=True)))
        atomic_json(output / "completion.json", dict(
            complete=True, records=index, sample_records=100, warmup_records=10,
            wall_seconds=time.monotonic()-start_wall, finished_at=datetime.now(timezone.utc).isoformat(),
            source_unchanged=True, plan_and_scripts_unchanged=True, sorting_executed=False))
    except BaseException as exc:
        atomic_json(output / "failure.json", dict(
            complete=False, accepted=False, error_type=type(exc).__name__, message=str(exc),
            committed_records=len(read_records(output))))
        write_manifest(output)
        raise
    write_manifest(output)
    print("constructor microbenchmark COMPLETE", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
