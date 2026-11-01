"""Unified source-ordered entry point. Creating a run never overwrites evidence.

Single-source preparation runs may be supplied together as prerequisite paths.
A formal invocation is one session; separate formal invocations are never merged.
"""
import argparse
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]

from common_input_protocol import source_identity
from committed_records import atomic_json, commit_record, read_records, run_bounded
from input_suite_registry import load_suite, canonical_cases, SOURCE_ORDER
from input_suite_protocol import (
    STAGES, DEADLINE, profile, make_request, prerequisite_stages, utc_now, stamp,
)
from matched_measurement import capture_environment
from matched_backend_fixture import error_details
from qualify_common_inputs import read, seal
from uninstrumented_protocol import require_machine
from validate_input_suite_run import dependencies, file_hash, availability, inspect_job
from validate_matched_measurement import check_review


def run_stage(output, stage, source="all", *, equivalence=(), qualification=(), calibration=(), review=None):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError("use a new run directory; existing attempts cannot be replaced")
    suite = load_suite()
    cfg = profile(suite, stage, source)
    env = capture_environment(configuration="uninstrumented")
    require_machine(env["execution"])
    if env["execution"]["dirty"]:
        raise RuntimeError("freeze and commit the final implementation before any run")
    provided = dict(equivalence=equivalence, qualification=qualification, calibration=calibration)
    bindings = {}
    for prior in prerequisite_stages(stage):
        bindings[prior] = [dict(path=str(Path(p).resolve()), manifest_sha256=file_hash(Path(p) / "manifest.json"))
                           for p in provided[prior]]
    deps = dependencies(stage, bindings, env)
    for required, refs in bindings.items():
        if not refs:
            raise ValueError("missing prerequisite archive: " + required)
    if stage == "formal":
        if review is None:
            raise ValueError("formal sampling requires the author's existing receipt")
        check_review(review, env["execution"]["source_sha256"])
    elif review is not None:
        raise ValueError("receipt is only used for formal sampling")
    cfg.update(source_filter=source, started_utc=utc_now(), prerequisites=bindings, review=review)
    if stage == "formal" and not any(
            availability(s, stage, cfg["selected_sources"], canonical_cases(suite, s), deps, cfg["started_utc"])[0] == "READY"
            for s in SOURCE_ORDER):
        raise ValueError("no source has complete in-deadline preparation; no formal session started")
    output.mkdir(parents=True, exist_ok=False)
    atomic_json(output / "config.json", cfg)
    atomic_json(output / "environment.json", env)
    (output / "sources").mkdir()
    total_start = time.monotonic()
    halt = False
    outcomes = {}
    for name in SOURCE_ORDER:
        folder = output / "sources" / name
        folder.mkdir()
        (folder / "requests").mkdir()
        (folder / "jobs").mkdir()
        source_start, source_stamp = time.monotonic(), utc_now()
        entries = canonical_cases(suite, name)
        if stage == "formal":
            random.Random(cfg["rules"]["order"]["case_shuffle_seed"]).shuffle(entries)
        initial, reason = availability(name, stage, cfg["selected_sources"], entries, deps, source_stamp)
        if halt and name in cfg["selected_sources"]:
            initial, reason = "NOT_RUN", "previous_source_stopped"
        stop = reason if initial != "READY" else None
        statuses = []
        for index, entry in enumerate(entries):
            case_start = utc_now()
            row = dict(case=entry["case_id"], status="NOT_RUN", reason=stop,
                       budget_seconds=0, started_utc=case_start, finished_utc=case_start, worker_wall_seconds=0,
                       source_elapsed_seconds=time.monotonic() - source_start,
                       campaign_elapsed_seconds=time.monotonic() - total_start)
            if stop is None:
                if stage != "formal" and stamp(case_start) >= stamp(DEADLINE):
                    stop = "preparation_deadline"
                remaining = ((cfg["limits"]["total_seconds"] - row["campaign_elapsed_seconds"])
                             if stage == "equivalence" else
                             cfg["limits"]["source_seconds"] - row["source_elapsed_seconds"])
                if remaining <= 0 and stop is None:
                    stop = "equivalence_budget" if stage == "equivalence" else "source_budget"
                if stop is None:
                    budget = min(remaining, cfg["limits"]["input_seconds"] or remaining)
                    batch = deps["calibration"][name]["batch_sizes"][entry["case_id"]] if stage == "formal" else None
                    request = make_request(cfg, env, entry, index, batch)
                    request_path = folder / "requests" / (entry["case_id"] + ".json")
                    atomic_json(request_path, request)
                    job = folder / "jobs" / entry["case_id"]
                    tick = time.monotonic()
                    code = run_bounded([sys.executable, "-B", str(ROOT / "experiments/input_suite_worker.py"),
                                        "--request", str(request_path), "--output", str(job)], job, budget)
                    row["worker_wall_seconds"] = time.monotonic() - tick
                    row["budget_seconds"] = budget
                    if code == 0:
                        try:
                            inspect_job(job, request, True)
                        except (ValueError, RuntimeError, KeyError, TypeError, OSError) as exc:
                            code = 2
                            atomic_json(job / "failure.json", dict(
                                status="INVALID_WORKER_EVIDENCE", accepted=False, performance_eligible=False,
                                error=error_details(exc), committed_records=len(read_records(job))))
                    if code:
                        failure = read(job / "failure.json")
                        row["status"] = "TIMEOUT" if failure["status"] == "RESOURCE_TIMEOUT" else "ERROR"
                        stop = "case_timeout" if row["status"] == "TIMEOUT" else "case_error"
                    else:
                        row["status"] = "PASS"
            row["reason"] = None if row["status"] == "PASS" else stop
            row["finished_utc"] = utc_now()
            commit_record(folder, index, row)
            statuses.append(row)
        finish, wall = utc_now(), time.monotonic() - source_start
        atomic_json(folder / "interval.json", dict(started_utc=source_stamp, finished_utc=finish, wall_seconds=wall, campaign_elapsed_seconds=time.monotonic() - total_start))
        if initial != "READY":
            status = initial
        elif any(r["status"] == "ERROR" for r in statuses):
            status = "ERROR"
        elif any(r["status"] != "PASS" for r in statuses) or (
                stage != "formal" and stamp(finish) >= stamp(DEADLINE)) or (
                cfg["limits"]["source_seconds"] is not None and wall >= cfg["limits"]["source_seconds"]) or (
                stage == "equivalence" and time.monotonic() - total_start >= cfg["limits"]["total_seconds"]):
            status = "INCOMPLETE"
        else:
            status = "COMPLETE"
        if initial == "READY" and (status == "ERROR" or (status == "INCOMPLETE" and stage in ("formal", "equivalence"))):
            halt = True
        outcomes[name] = status
        print(f"{stage}: {name}: {status}", flush=True)
    if source_identity() != env["execution"]["source_sha256"]:
        atomic_json(output / "source_failure.json", dict(reason="source_changed_during_run", accepted=False))
        halt = True
    # A journal and immutable file manifest, deliberately no runner summary.
    seal(output)
    return dict(stage=stage, sources=outcomes,
                complete=not halt and all(outcomes[s] in ("COMPLETE", "DUPLICATE_ONLY") for s in cfg["selected_sources"]))


if __name__ == "__main__":
    import json
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", choices=STAGES, required=True)
    p.add_argument("--source", choices=("all", *SOURCE_ORDER), default="all")
    p.add_argument("--output", type=Path, required=True)
    for stage in ("equivalence", "qualification", "calibration"):
        p.add_argument("--" + stage, type=Path, nargs="+", default=[])
    p.add_argument("--review", type=Path)
    a = p.parse_args()
    result = run_stage(a.output, a.stage, a.source, equivalence=a.equivalence, qualification=a.qualification,
                       calibration=a.calibration, review=read(a.review) if a.review else None)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["complete"] else 2)
