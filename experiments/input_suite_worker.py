"""Internal bounded workers; production entry is run_input_suite.py."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "experiments")]

from common_input_protocol import source_identity, digest
from committed_records import atomic_json, commit_record, canonical
from input_suite_registry import load_suite, canonical_cases
from input_suite_protocol import STAGES, BACKENDS, old_trace_digest
from uninstrumented_protocol import power_observation, require_power


def equivalence(entry, counted):
    from validate_uninstrumented_equivalence import checked, NAMES
    from matched_backend_fixture import backend_spec
    from paper_jordan_sort import paper_jordan_sort_valid
    from sibling_backend_contract import SiblingBackendSpec
    from heterogeneous_finger_backend import HeterogeneousFingerBackend
    values = entry["values"]
    reports, minimal = {}, {}
    for name in NAMES:
        reports[name], _ = checked(values, backend_spec(name))
        minimal[name] = paper_jordan_sort_valid(values, "minimal", backend=backend_spec(name))
    left, right = (reports[name] for name in NAMES)
    fields = ("output", "trace", "metrics", "prefixes", "qualification_report")
    if any(canonical(left[k]) != canonical(right[k]) for k in fields):
        raise ValueError("instrumented/uninstrumented divergence")
    if left["output"] != sorted(values) or any(v != sorted(values) for v in minimal.values()):
        raise ValueError("equivalence output")
    legacy = old_trace_digest(entry)
    if digest(left["trace"]) != legacy:
        raise ValueError("original instrumented trace changed")
    detailed = None
    if counted:
        detailed, state = checked(values, SiblingBackendSpec(HeterogeneousFingerBackend))
        if any(canonical(left[k]) != canonical(detailed[k]) for k in fields):
            raise ValueError("detailed collection divergence")
        detailed["work"] = state.sibling_backend.work.snapshot()
    return dict(case=entry["case_id"], input_sha256=entry["input_sha256"],
                checked=reports, minimal=minimal, counted=detailed, legacy_trace_sha256=legacy)


def execute(request, output):
    from input_suite_protocol import SCHEMA, COUNTED_ORIGINAL_CASE
    if sys.flags.optimize != 0 or request["schema"] != SCHEMA or request["stage"] not in STAGES:
        raise ValueError("worker schema/stage/optimization")
    suite = load_suite()
    entry = next((e for e in canonical_cases(suite) if e["case_id"] == request["entry"]["case_id"]), None)
    if entry != request["entry"] or request["suite_sha256"] != suite["suite_sha256"]:
        raise ValueError("worker input binding")
    if source_identity() != request["source_sha256"]:
        raise ValueError("worker source binding")
    stage = request["stage"]
    if request["counted"] != (entry["source"] == "targeted_split" and entry["original_case_id"] == COUNTED_ORIGINAL_CASE):
        raise ValueError("worker counted identity")
    if stage == "qualification":
        q = request["qualification"]
        if (q["case"] != entry["case_id"] or q["values"] != entry["values"]
                or q["backends"] not in (list(BACKENDS), list(BACKENDS[::-1]))):
            raise ValueError("worker qualification binding")
    if stage in ("calibration", "formal"):
        from input_suite_protocol import case_payload
        from common_input_protocol import measurement_protocol
        if (request["measurement"]["case"] != case_payload(entry)
                or request["measurement"]["stage"] != stage
                or request["measurement"]["configuration"] != "uninstrumented"
                or request["measurement"]["rules"] != measurement_protocol()):
            raise ValueError("worker measurement binding")
        if stage == "formal":
            from validate_matched_measurement import check_review
            check_review(request["review"], request["source_sha256"])
        from matched_measurement import execute_case
        return execute_case(request["measurement"], output)
    from oracle import oracle
    if oracle(entry["values"])["valid"] is not True:
        raise ValueError("invalid registered Jordan input")
    power = {"before": power_observation()}
    require_power(power["before"])
    if stage == "equivalence":
        output.mkdir(parents=True, exist_ok=False)
        atomic_json(output / "power.json", power)
        atomic_json(output / "progress.json", dict(stage=stage, case=entry["case_id"], status="RUNNING"))
        result = equivalence(entry, request["counted"])
        commit_record(output, 0, result)
        code = 0
        atomic_json(output / "progress.json", dict(status="COMPLETE", committed_records=1))
    else:
        from qualify_common_inputs_v2 import qualify_case
        code = qualify_case(request["qualification"], output,
                            on_start=lambda: atomic_json(output / "power.json", power))
    power["after"] = power_observation()
    atomic_json(output / "power.json", power)
    require_power(power["after"])
    if source_identity() != request["source_sha256"]:
        raise ValueError("source changed during worker")
    return code


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    raise SystemExit(execute(json.loads(a.request.read_text()), a.output))
