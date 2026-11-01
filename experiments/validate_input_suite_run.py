"""Read-only verification of unified run records; runner summaries are not parsed."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

from committed_records import canonical, read_records
from common_input_protocol import digest
from input_suite_registry import load_suite, canonical_cases, SOURCE_ORDER
from input_suite_protocol import (
    SCHEMA, LEGACY_SCHEMA, STAGES, BACKENDS, DEADLINE, profile, stamp, limits, prerequisite_stages,
    environment_equal, require_workload, old_trace_digest,
)
from matched_backend_fixture import identity
from qualify_common_inputs import read
from qualification_trace_semantics import check_trace
from validate_common_qualification_v2 import validate_job
from validate_matched_measurement import check_job, check_environment, check_review
from uninstrumented_protocol import require_power


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_manifest(path):
    require(not any(p.is_symlink() for p in path.rglob("*")), "symlink in run evidence")
    actual = {p.relative_to(path).as_posix(): file_hash(p) for p in path.rglob("*")
              if p.is_file() and p != path / "manifest.json"}
    require(read(path / "manifest.json") == actual, "run file manifest")


def check_equivalence(job, entry, counted):
    rows = read_records(job)
    require(len(rows) == 1, "equivalence record count")
    require(read(job / "progress.json") == dict(status="COMPLETE", committed_records=1), "equivalence completion cursor")
    row = rows[0]
    names = ("heterogeneous_finger", "heterogeneous_finger_uninstrumented")
    require(row["case"] == entry["case_id"] and row["input_sha256"] == entry["input_sha256"],
            "equivalence input")
    require(set(row["checked"]) == set(names) == set(row["minimal"]), "equivalence backends")
    for name in names:
        r = row["checked"][name]
        require(canonical(r["backend_identity"]) == canonical(identity(name)), "equivalence configuration")
        require(r["output"] == sorted(entry["values"]) == row["minimal"][name], "equivalence output")
        require([p["prefix"] for p in r["prefixes"]] == list(range(3, entry["n"] + 1)), "prefix coverage")
        for p in r["prefixes"]:
            require(p["output_sha256"] == digest(sorted(entry["values"][:p["prefix"]]))
                    and isinstance(p["state_sha256"], str) and len(p["state_sha256"]) == 64, "prefix evidence")
        report = r["qualification_report"]
        require(report["prefix_comparisons"] == entry["n"] - 2 and report["initialized_instances"] == 3
                and report["fresh_final_replays"] == 1 and report["same_backend_same_config"] is True
                and report["performance_eligible"] is False, "equivalence audit coverage")
        coverage = check_trace(entry["values"], r["trace"], r["metrics"], name)
        require_workload(entry, coverage)
    left, right = (row["checked"][n] for n in names)
    for field in ("output", "trace", "metrics", "prefixes", "qualification_report"):
        require(canonical(left[field]) == canonical(right[field]), "configuration divergence")
    require(row["legacy_trace_sha256"] == old_trace_digest(entry) == digest(left["trace"]), "legacy trace")
    require((row["counted"] is not None) == counted, "counted example identity")
    if counted:
        for field in ("output", "trace", "metrics", "prefixes", "qualification_report"):
            require(canonical(left[field]) == canonical(row["counted"][field]), "counted divergence")
        require(row["counted"]["work"]["operations"]["node_visits"] > 0, "counted work missing")
    return dict(prefixes=entry["n"] - 2)


def inspect_job(job, request, passing):
    stage, entry = request["stage"], request["entry"]
    if stage in ("calibration", "formal"):
        return check_job(job, request["measurement"], passing=passing, verify_summary=False)
    rows = read_records(job)
    if rows or passing:
        power = read(job / "power.json")
        require_power(power["before"])
        if 'power_binding' in request:
            from platform_environment import require_power_binding
            require_power_binding(power['before'], request['power_binding'])
        if passing:
            require_power(power["after"])
            if 'power_binding' in request:
                require_power_binding(power['after'], request['power_binding'])
    if stage == "equivalence":
        return check_equivalence(job, entry, request["counted"]) if passing else dict(records=len(rows))
    records = validate_job(job, request["qualification"], entry["input_sha256"], passing=passing)
    structures = []
    for row in records:
        if row["mode"] == "synchronous_v2" and row["status"] == "PASS":
            coverage = check_trace(entry["values"], row["final"]["trace"], row["final"]["metrics"], row["backend"])
            require_workload(entry, coverage)
            events = coverage["splits"]
            smaller = [min(s["left_size"], s["right_size"]) for s in events
                       if s["left_size"] > 0 and s["right_size"] > 0]
            structures.append(dict(S_i=len(events), I_i=len(smaller), smaller_sides=smaller,
                                   p_i=len(smaller) / len(events) if events else None))
    if passing:
        require(len(structures) == 2 and structures[0] == structures[1], "backend split structures differ")
    return dict(structure=structures[0] if passing else None)


def dependencies(stage, bindings, env, *, historical=False, cache=None, active=None):
    """Merge single-source preparations, rejecting repeated attempts/old schemas."""
    cache = {} if cache is None else cache
    active = set() if active is None else active
    require(set(bindings) == set(prerequisite_stages(stage)), "prerequisite stages")
    result = {}
    for expected_stage in prerequisite_stages(stage):
        refs = bindings[expected_stage]
        result[expected_stage] = {}
        for ref in refs:
            p = Path(ref["path"]).resolve()
            require(file_hash(p / "manifest.json") == ref["manifest_sha256"], "prerequisite archive binding")
            report = validate(p, historical=historical, cache=cache, active=active)
            require(report["stage"] == expected_stage, "prerequisite stage")
            require(not report["hard_error"], "prerequisite correctness/configuration error")
            if expected_stage == "equivalence":
                require(not any(s["resource_failure"] for s in report["sources"].values()),
                        "equivalence resource failure is not a source-level fallback")
            environment_equal(env["execution"], report["environment"]["execution"])
            for name in report["selected_sources"]:
                require(name not in result[expected_stage], "multiple prerequisite attempts for one source")
                result[expected_stage][name] = dict(report["sources"][name], archive=str(p))
    for per_source in result.values():
        for name, source in per_source.items():
            for prior_stage, archive in source["prerequisite_archives"].items():
                require(result[prior_stage].get(name, {}).get("archive") == archive,
                        "inconsistent prerequisite chain for " + name)
    return result


def availability(source, stage, selected, entries, deps, when):
    if source not in selected:
        return "NOT_RUN", "not_requested"
    if not entries:
        return "DUPLICATE_ONLY", "no_canonical_inputs"
    for required in prerequisite_stages(stage):
        prior = deps[required].get(source)
        if prior is None or prior["status"] != "COMPLETE":
            return "INCOMPLETE", "prerequisite_incomplete"
        if stamp(prior["finished_utc"]) >= stamp(DEADLINE):
            return "INCOMPLETE", "preparation_deadline"
    if stage != "formal" and stamp(when) >= stamp(DEADLINE):
        return "INCOMPLETE", "preparation_deadline"
    return "READY", None


def validate(path, *, historical=False, cache=None, active=None):
    path = Path(path).resolve()
    cache = {} if cache is None else cache
    active = set() if active is None else active
    if path in cache:
        return cache[path]
    require(path not in active, "cyclic prerequisite references")
    active.add(path)
    try:
        verify_manifest(path)
        require(not (path / "source_failure.json").exists(), "source changed during run")
        cfg, env = read(path / "config.json"), read(path / "environment.json")
        require(cfg["schema"] in (SCHEMA, LEGACY_SCHEMA) and cfg["stage"] in STAGES, "unified run schema/stage")
        from platform_environment import SCHEMA as environment_schema
        require((env['execution']['hardware'].get('environment_schema') == environment_schema)
                if cfg['schema'] == SCHEMA else 'environment_schema' not in env['execution']['hardware'],
                'run schema/environment protocol mismatch')
        suite = load_suite()
        wanted = profile(suite, cfg["stage"], cfg["source_filter"], schema=cfg['schema'])
        for key, value in wanted.items():
            require(canonical(cfg[key]) == canonical(value), "frozen profile: " + key)
        require(set(cfg) == set(wanted) | {"source_filter", "started_utc", "prerequisites", "review"},
                "configuration fields")
        check_environment(env, uninstrumented=True, historical=historical)
        require(stamp(cfg["started_utc"]) >= stamp(env["execution"]["captured_at"]), "run chronology")
        deps = dependencies(cfg["stage"], cfg["prerequisites"], env,
                            historical=historical, cache=cache, active=active)
        require(set(p.name for p in (path / "sources").iterdir()) == set(SOURCE_ORDER), "source directories")
        for stage_deps in deps.values():
            for prior in stage_deps.values():
                require(stamp(prior["finished_utc"]) <= stamp(cfg["started_utc"]), "prerequisite chronology")
        if cfg["stage"] == "formal":
            check_review(cfg["review"], env["execution"]["source_sha256"])
        else:
            require(cfg["review"] is None, "review only belongs to formal stage")
        sources, halt, hard_error, previous_finish = {}, False, False, stamp(cfg["started_utc"])
        for source in SOURCE_ORDER:
            folder = path / "sources" / source
            meta = read(folder / "interval.json")
            require(set(meta) == {"started_utc", "finished_utc", "wall_seconds", "campaign_elapsed_seconds"}, "source interval fields")
            started, finished = stamp(meta["started_utc"]), stamp(meta["finished_utc"])
            require(previous_finish <= started <= finished and type(meta["wall_seconds"]) in (int, float)
                    and math.isfinite(meta["wall_seconds"]) and meta["wall_seconds"] >= 0
                    and math.isfinite(meta["campaign_elapsed_seconds"])
                    and meta["campaign_elapsed_seconds"] >= meta["wall_seconds"], "source order/interval")
            previous_finish = finished
            entries = canonical_cases(suite, source)
            if cfg["stage"] == "formal":
                random.Random(cfg["rules"]["order"]["case_shuffle_seed"]).shuffle(entries)
            initial, reason = availability(source, cfg["stage"], cfg["selected_sources"], entries, deps,
                                           meta["started_utc"])
            if halt and source in cfg["selected_sources"]:
                initial, reason = "NOT_RUN", "previous_source_stopped"
            rows = read_records(folder)
            require(len(rows) == len(entries), "source case status coverage")
            stopped = initial != "READY"
            batch_sizes, stats, structures = {}, {}, {}
            resource_failure = False
            previous_case_finish = started
            attempted = set()
            for index, (entry, row) in enumerate(zip(entries, rows, strict=True)):
                require(set(row) == {"case", "status", "reason", "budget_seconds", "started_utc",
                                     "finished_utc", "worker_wall_seconds", "source_elapsed_seconds", "campaign_elapsed_seconds"}, "case status fields")
                require(row["case"] == entry["case_id"] and row["status"] in ("PASS", "TIMEOUT", "ERROR", "NOT_RUN"),
                        "case identity/status")
                t0, t1 = stamp(row["started_utc"]), stamp(row["finished_utc"])
                require(previous_case_finish <= t0 <= t1 <= finished, "case interval")
                previous_case_finish = t1
                require(0 <= row["source_elapsed_seconds"] <= meta["wall_seconds"]
                        and row["source_elapsed_seconds"] <= row["campaign_elapsed_seconds"] <= meta["campaign_elapsed_seconds"],
                        "case resource chronology")
                require(type(row["worker_wall_seconds"]) in (int, float)
                        and math.isfinite(row["worker_wall_seconds"]) and row["worker_wall_seconds"] >= 0, "worker resource observation")
                if row["status"] == "NOT_RUN":
                    require(bool(row["reason"]), "missing unexecuted reason")
                    if not stopped:
                        require(row["reason"] in ("source_budget", "equivalence_budget", "preparation_deadline"),
                                "unexpected NOT_RUN")
                        if row["reason"] == "preparation_deadline":
                            require(cfg["stage"] != "formal" and t0 >= stamp(DEADLINE), "early deadline skip")
                        elif row["reason"] == "source_budget":
                            require(cfg["limits"]["source_seconds"] is not None and
                                    row["source_elapsed_seconds"] >= cfg["limits"]["source_seconds"], "early source budget skip")
                        else:
                            require(cfg["stage"] == "equivalence" and row["campaign_elapsed_seconds"] >= 7200,
                                    "early equivalence budget skip")
                        resource_failure = row["reason"] != "preparation_deadline"
                    elif initial != "READY":
                        require(row["reason"] == reason, "source skip reason")
                    stopped = True
                    require(row["budget_seconds"] == 0 and row["worker_wall_seconds"] == 0, "unexecuted resource")
                    continue
                require(not stopped and initial == "READY", "execution after a stop")
                attempted.add(entry["case_id"])
                require(cfg["stage"] == "formal" or t0 < stamp(DEADLINE), "preparation started after deadline")
                remaining = (7200 - row["campaign_elapsed_seconds"] if cfg["stage"] == "equivalence"
                             else cfg["limits"]["source_seconds"] - row["source_elapsed_seconds"])
                maximum = min(remaining, cfg["limits"]["input_seconds"] or remaining)
                require(0 < row["budget_seconds"] <= maximum, "case resource budget")
                request = read(folder / "requests" / (entry["case_id"] + ".json"))
                # Reconstruct request fields independently of the runner's adapter.
                wanted_request = dict(schema=cfg['schema'], stage=cfg["stage"], suite_sha256=suite["suite_sha256"],
                                      source_sha256=env["execution"]["source_sha256"], entry=entry,
                                      counted=entry["case_id"] == cfg["counted_case"], review=cfg["review"])
                if cfg['schema'] == SCHEMA:
                    from platform_environment import power_binding
                    wanted_request['power_binding'] = power_binding(env['execution']['hardware'])
                if cfg["stage"] == "qualification":
                    wanted_request["qualification"] = dict(case=entry["case_id"], values=entry["values"],
                                                          backends=list(BACKENDS if index % 2 == 0 else BACKENDS[::-1]))
                if cfg["stage"] in ("calibration", "formal"):
                    batch = deps["calibration"][source]["batch_sizes"][entry["case_id"]] if cfg["stage"] == "formal" else None
                    wanted_request["measurement"] = dict(stage=cfg["stage"], index=index, rules=cfg["rules"],
                        case=dict(case=entry["case_id"], values=entry["values"], input_sha256=entry["input_sha256"]),
                        batch_size=batch, configuration="uninstrumented",
                        gc_thresholds=env["execution"]["gc_thresholds"])
                    if cfg['schema'] == SCHEMA:
                        wanted_request['measurement']['power_binding'] = wanted_request['power_binding']
                require(canonical(request) == canonical(wanted_request), "worker request binding")
                job = folder / "jobs" / entry["case_id"]
                result = inspect_job(job, request, row["status"] == "PASS")
                if row["status"] == "PASS":
                    require(row["reason"] is None, "passing reason")
                    if cfg["stage"] == "qualification":
                        structures[entry["case_id"]] = result["structure"]
                    elif cfg["stage"] == "calibration":
                        batch_sizes[entry["case_id"]] = result["result"]["chosen_batch"]
                    elif cfg["stage"] == "formal":
                        stats[entry["case_id"]] = result["result"]
                else:
                    stopped = True
                    failure = read(job / "failure.json")
                    require(failure.get("committed_records") == len(read_records(job)), "failure record count")
                    require(failure.get("accepted") is False and failure.get("performance_eligible") is False,
                            "failure evidence")
                    if row["status"] == "TIMEOUT":
                        require(failure["status"] == "RESOURCE_TIMEOUT"
                                and failure["budget_seconds"] == row["budget_seconds"], "resource timeout evidence")
                        resource_failure = True
                    else:
                        require(failure["status"] != "RESOURCE_TIMEOUT", "error reclassified as timeout")
                        hard_error = True
            require({p.stem for p in (folder / "requests").iterdir()} == attempted, "request inventory")
            require({p.name for p in (folder / "jobs").iterdir()} == attempted, "job inventory")
            budget_exceeded = ((cfg["limits"]["source_seconds"] is not None and
                                meta["wall_seconds"] >= cfg["limits"]["source_seconds"]) or
                               (cfg["stage"] == "equivalence" and meta["campaign_elapsed_seconds"] >= 7200))
            resource_failure = resource_failure or (initial == "READY" and budget_exceeded)
            if initial != "READY":
                status = initial
            elif any(r["status"] == "ERROR" for r in rows):
                status = "ERROR"
            elif any(r["status"] != "PASS" for r in rows) or (cfg["stage"] != "formal" and finished >= stamp(DEADLINE)) or budget_exceeded:
                status = "INCOMPLETE"
            else:
                status = "COMPLETE"
            if initial == "READY" and (status == "ERROR" or
                    (status == "INCOMPLETE" and cfg["stage"] in ("formal", "equivalence"))):
                halt = True
            sources[source] = dict(status=status, finished_utc=meta["finished_utc"], reason=reason,
                                   entries=len(entries), passed=sum(r["status"] == "PASS" for r in rows),
                                   resource_failure=resource_failure, cases=rows,
                                   prerequisite_archives={prior: deps[prior].get(source, {}).get("archive")
                                                          for prior in prerequisite_stages(cfg["stage"])},
                                   batch_sizes=batch_sizes,
                                   statistics=stats, structures=structures)
        complete = all(sources[s]["status"] in ("COMPLETE", "DUPLICATE_ONLY") for s in cfg["selected_sources"])
        report = dict(archive_valid=True, stage=cfg["stage"], suite_sha256=suite["suite_sha256"],
                      selected_sources=cfg["selected_sources"], environment=env, sources=sources,
                      complete=complete, hard_error=hard_error,
                      all_sources_complete=all(sources[s]["status"] in ("COMPLETE", "DUPLICATE_ONLY")
                                               for s in SOURCE_ORDER))
        cache[path] = report
        return report
    finally:
        active.remove(path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--historical", action="store_true")
    a = p.parse_args()
    print(json.dumps(validate(a.directory, historical=a.historical), indent=2))
