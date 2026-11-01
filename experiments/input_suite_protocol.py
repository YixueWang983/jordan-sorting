"""Immutable rules and input identities for the five-source rerun."""
from datetime import datetime, timezone
from pathlib import Path

from input_suite_registry import ROOT, SOURCE_ORDER, load_suite, canonical_cases
from common_input_protocol import measurement_protocol, digest
from committed_records import read_records
from uninstrumented_protocol import BACKENDS

SCHEMA = "unified_input_suite_run_v1"
STAGES = ("equivalence", "qualification", "calibration", "formal")
DEADLINE = "2026-11-14T23:00:00+00:00"  # 15 November 00:00 Europe/Berlin.
COUNTED_ORIGINAL_CASE = "split-n128-k3"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def stamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("timestamp must have timezone")
    return result.astimezone(timezone.utc)


def selected_sources(source):
    if source == "all":
        return list(SOURCE_ORDER)
    if source not in SOURCE_ORDER:
        raise ValueError("unknown source")
    return [source]


def limits(stage):
    if stage == "equivalence":
        return dict(input_seconds=600, source_seconds=None, total_seconds=7200)
    if stage == "qualification":
        return dict(input_seconds=180, source_seconds=1800, total_seconds=None)
    if stage == "calibration":
        return dict(input_seconds=None, source_seconds=600, total_seconds=None)
    if stage == "formal":
        return dict(input_seconds=120, source_seconds=1800, total_seconds=None)
    raise ValueError("unknown stage")


def profile(suite, stage, source):
    return dict(schema=SCHEMA, stage=stage, suite_sha256=suite["suite_sha256"],
                registration=suite["registration"], selected_sources=selected_sources(source),
                source_order=list(SOURCE_ORDER), rules=measurement_protocol(), limits=limits(stage),
                deadline=DEADLINE, backends=list(BACKENDS),
                counted_case=next((e["case_id"] for e in suite["entries"]
                                   if e["source"] == "targeted_split"
                                   and e["original_case_id"] == COUNTED_ORIGINAL_CASE), None))


def case_payload(entry):
    return dict(case=entry["case_id"], values=entry["values"], input_sha256=entry["input_sha256"])


def old_trace_digest(entry):
    """Read fixed old evidence; do not execute any old generator/controller."""
    import json
    from validate_uninstrumented_equivalence import legacy_trace
    source, cid = entry["source"], entry["original_case_id"]
    if source in ("common", "targeted_split", "seeded"):
        return digest(legacy_trace(dict(group=source, original_case=cid)))
    if source == "structural":
        job = ROOT / "docs/validation/structural_split_formal_20261101/qualification/jobs" / cid
        return digest(next(r["final"]["trace"] for r in read_records(job)
                           if r["backend"] == "heterogeneous_finger" and r["mode"] == "synchronous_v2"))
    from input_suite_registry import GEO_PATH
    record = json.loads((ROOT / GEO_PATH).read_text())["cases"][entry["source_index"]]
    if record["case"] != cid:
        raise ValueError("old geometric record identity")
    return record["full_trace_sha256"]


def environment_equal(left, right):
    from uninstrumented_protocol import hardware_binding
    for key in ("source_sha256", "python", "executable", "platform", "machine",
                "python_optimize", "gc_enabled", "gc_thresholds"):
        if left[key] != right[key]:
            raise ValueError("prerequisite environment/source mismatch: " + key)
    if hardware_binding(left["hardware"]) != hardware_binding(right["hardware"]):
        raise ValueError("prerequisite hardware mismatch")


def require_workload(entry, coverage):
    if entry["source"] == "targeted_split":
        if not any(s["left_size"] > 0 and s["right_size"] > 0
                   and s["smaller_side"] == entry["smaller_side_k"] for s in coverage["splits"]):
            raise ValueError("missing targeted split workload")
    elif entry["source"] == "structural":
        from structural_split_protocol import require_structural_coverage
        require_structural_coverage(dict(n=entry["n"], shape=entry["shape"]), coverage)


def prerequisite_stages(stage):
    return {"equivalence": (), "qualification": ("equivalence",),
            "calibration": ("equivalence", "qualification"),
            "formal": ("equivalence", "qualification", "calibration")}[stage]


def make_request(cfg, env, entry, index, batch=None):
    """Pure input/config adaptation; does not execute or choose experimental rules."""
    stage = cfg["stage"]
    request = dict(schema=SCHEMA, stage=stage, suite_sha256=cfg["suite_sha256"],
                   source_sha256=env["execution"]["source_sha256"], entry=entry,
                   counted=entry["case_id"] == cfg["counted_case"],
                   review=cfg.get("review"))
    if stage == "qualification":
        order = list(BACKENDS if index % 2 == 0 else BACKENDS[::-1])
        request["qualification"] = dict(case=entry["case_id"], values=entry["values"], backends=order)
    if stage in ("calibration", "formal"):
        request["measurement"] = dict(stage=stage, case=case_payload(entry), index=index,
                                      rules=cfg["rules"], batch_size=batch, configuration="uninstrumented",
                                      gc_thresholds=env["execution"]["gc_thresholds"])
    return request
