"""Build, preflight, and eventually execute the frozen Week 12 experiment."""

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from formal_execution_support import (  # noqa: E402
    build_formal_environment_record,
    build_formal_run_paths,
    file_sha256,
    read_json_object,
    require_unused_formal_output,
    reserve_formal_run_directory,
    validate_formal_environment_record,
    write_csv_exclusive,
    write_json_exclusive,
)
from generators import INCREMENTAL_VALID, generate_sequence, make_case_id  # noqa: E402
from oracle import oracle  # noqa: E402
from paper_jordan import METRIC_NAMES as PAPER_METRIC_NAMES  # noqa: E402
from paper_jordan_sort import paper_jordan_diagnostics_valid  # noqa: E402
from run_week11_pilot import (  # noqa: E402
    CASE_AUDIT_FIELDS,
    CASE_SUMMARY_FIELDS,
    GROUP_SUMMARY_FIELDS,
    PAPER_AUDIT_FIELDS,
    RAW_FIELDS,
    STRUCTURAL_FIELDS,
    algorithm_order_for_round,
    order_cases,
    run_timed_algorithm,
    summarize_by_case,
    summarize_by_group,
)
from stats import structure_profile  # noqa: E402
from week11_execution_context import validate_execution_id  # noqa: E402
from week12_experiment_gate import (  # noqa: E402
    PAPER_ALGORITHM_NAME,
    WEEK12_EXPERIMENT_GATE,
    Week12ExperimentGate,
    gate_to_dict,
    validate_week12_experiment_gate,
)


FORMAL_EXECUTION_ENABLED = False
EXPERIMENT_ELAPSED_SCOPE = (
    "From formal evidence-directory reservation through config/environment "
    "writes, case generation, oracle certification, checked diagnostics, "
    "warm-ups, measured calls, summary construction, and CSV writes; "
    "excludes manifest writing and output validation."
)
MANIFEST_FILE_ATTRIBUTES = {
    "raw": "raw_csv",
    "case_summary": "case_summary_csv",
    "group_summary": "group_summary_csv",
    "case_audit": "case_audit_csv",
    "config": "config_json",
    "environment": "environment_json",
}


@dataclass(frozen=True)
class Week12ExecutionConfig:
    """Internal executable view derived from the complete frozen gate."""

    protocol_version: str
    sizes: tuple[int, ...]
    valid_families: tuple[str, ...]
    randomized_cases: int
    warmup_runs: int
    measured_runs: int
    algorithms: tuple[str, ...]
    paper_execution_mode: str
    audit_execution_mode: str
    seed: int
    algorithm_order_seed: int
    case_order_seed: int

    def repetitions_for_family(self, family):
        if family not in self.valid_families:
            raise ValueError(f"family is not part of this execution: {family}")
        return self.randomized_cases if family == INCREMENTAL_VALID else 1

    @property
    def case_count(self):
        return len(self.sizes) * sum(
            self.repetitions_for_family(family)
            for family in self.valid_families
        )

    @property
    def raw_row_count(self):
        return self.case_count * len(self.algorithms) * self.measured_runs

    @property
    def case_summary_row_count(self):
        return self.case_count * len(self.algorithms)

    @property
    def group_summary_row_count(self):
        return len(self.valid_families) * len(self.sizes) * len(self.algorithms)


def build_execution_config(gate=WEEK12_EXPERIMENT_GATE):
    validate_week12_experiment_gate(gate)
    return Week12ExecutionConfig(
        protocol_version=gate.protocol_version,
        sizes=tuple(gate.sizes),
        valid_families=tuple(gate.valid_families),
        randomized_cases=gate.randomized_cases,
        warmup_runs=gate.warmup_runs,
        measured_runs=gate.measured_runs,
        algorithms=tuple(gate.algorithms),
        paper_execution_mode=gate.paper_execution_mode,
        audit_execution_mode=gate.audit_execution_mode,
        seed=gate.seed,
        algorithm_order_seed=gate.algorithm_order_seed,
        case_order_seed=gate.case_order_seed,
    )


def validate_execution_config(config, *, require_frozen=False):
    if not isinstance(config, Week12ExecutionConfig):
        raise TypeError("config must be a Week12ExecutionConfig")
    if config.protocol_version != WEEK12_EXPERIMENT_GATE.protocol_version:
        raise ValueError("protocol_version does not match the frozen gate")
    if not config.sizes or len(set(config.sizes)) != len(config.sizes):
        raise ValueError("sizes must be non-empty and unique")
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in config.sizes):
        raise ValueError("sizes must contain positive integers")
    if tuple(config.valid_families) != tuple(WEEK12_EXPERIMENT_GATE.valid_families):
        raise ValueError("valid families changed")
    if (
        isinstance(config.randomized_cases, bool)
        or not isinstance(config.randomized_cases, int)
        or config.randomized_cases < 1
    ):
        raise ValueError("randomized_cases must be positive")
    if (
        isinstance(config.warmup_runs, bool)
        or not isinstance(config.warmup_runs, int)
        or config.warmup_runs < 0
        or isinstance(config.measured_runs, bool)
        or not isinstance(config.measured_runs, int)
        or config.measured_runs < 1
    ):
        raise ValueError("run counts are invalid")
    if tuple(config.algorithms) != tuple(WEEK12_EXPERIMENT_GATE.algorithms):
        raise ValueError("algorithms changed")
    if config.paper_execution_mode != "minimal":
        raise ValueError("paper execution mode must be minimal")
    if config.audit_execution_mode != "checked":
        raise ValueError("audit execution mode must be checked")
    for name in ("seed", "algorithm_order_seed", "case_order_seed"):
        value = getattr(config, name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
    if require_frozen and config != build_execution_config():
        raise ValueError("formal execution config does not match the frozen gate")
    return config


def seed_for_case(family, n, case_number, base_seed):
    if family == INCREMENTAL_VALID:
        return base_seed + n * 1000 + case_number
    return None


def sequence_sha256(sequence):
    payload = json.dumps(
        list(sequence),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _csv_value(value):
    return "" if value is None else value


def _case_audit_row(config, execution_id, case, diagnostics):
    output_hash = sequence_sha256(diagnostics["output"])
    row = {
        "protocol_version": config.protocol_version,
        "execution_id": execution_id,
        "case_id": case["case_id"],
        "case_index": case["case_index"],
        "family": case["family"],
        "n": case["n"],
        "seed": _csv_value(case["seed"]),
        "sequence_sha256": case["sequence_sha256"],
        "oracle_valid": case["oracle"]["valid"],
        "oracle_reason": _csv_value(case["oracle"]["reason"]),
        **{
            field: _csv_value(case["profile"][field])
            for field in STRUCTURAL_FIELDS
        },
        "audit_execution_mode": config.audit_execution_mode,
        "audit_passed": case["audit_passed"],
        "diagnostic_output_sha256": output_hash,
        "diagnostic_processed_count": diagnostics["processed_count"],
        "diagnostic_trace_event_count": len(diagnostics["trace"]),
        **{
            f"paper_{name}": diagnostics["metrics"][name]
            for name in PAPER_METRIC_NAMES
        },
    }
    return {field: _csv_value(row.get(field)) for field in CASE_AUDIT_FIELDS}


def build_cases_and_audits(config, execution_id):
    """Certify and audit every exact case before warm-up or timing."""
    validate_execution_config(config)
    validate_execution_id(execution_id)
    cases = []
    audit_rows = []
    hashes_by_group = {}
    for family in config.valid_families:
        for n in config.sizes:
            for case_number in range(1, config.repetitions_for_family(family) + 1):
                case_seed = seed_for_case(family, n, case_number, config.seed)
                sequence = generate_sequence(family, n, seed=case_seed)
                if len(sequence) != n:
                    raise RuntimeError("Week 12 generator returned the wrong length")
                result = oracle(sequence)
                if not result["valid"] or not result["distinct_values"]:
                    raise RuntimeError("Week 12 requires oracle-certified valid input")
                digest = sequence_sha256(sequence)
                group_hashes = hashes_by_group.setdefault((family, n), set())
                if digest in group_hashes:
                    raise RuntimeError("Week 12 generator returned a duplicate case")
                group_hashes.add(digest)
                profile = structure_profile(sequence, oracle_result=result)

                # The diagnostics API is deliberately fixed to CHECKED_POLICY.
                diagnostics = paper_jordan_diagnostics_valid(sequence)
                audit_passed = (
                    diagnostics["invariants_valid"]
                    and diagnostics["output"] == result["sorted"]
                    and diagnostics["processed_count"] == n
                )
                if not audit_passed:
                    raise RuntimeError("Week 12 checked diagnostics failed")
                case = {
                    "case_id": make_case_id(family, n, case_number),
                    "case_index": len(cases) + 1,
                    "family": family,
                    "n": n,
                    "seed": case_seed,
                    "sequence_sha256": digest,
                    "sequence": sequence,
                    "oracle": result,
                    "profile": profile,
                    "audit_passed": True,
                }
                cases.append(case)
                audit_rows.append(
                    _case_audit_row(config, execution_id, case, diagnostics)
                )
    if len(cases) != config.case_count:
        raise RuntimeError("Week 12 generated an unexpected case count")
    return cases, audit_rows


def _raw_metadata(config, execution_id, case, algorithm_name):
    return {
        "protocol_version": config.protocol_version,
        "execution_id": execution_id,
        "case_id": case["case_id"],
        "case_index": case["case_index"],
        "family": case["family"],
        "n": case["n"],
        "seed": _csv_value(case["seed"]),
        "sequence_sha256": case["sequence_sha256"],
        "case_execution_position": case["case_execution_position"],
        **{
            field: _csv_value(case["profile"][field])
            for field in STRUCTURAL_FIELDS
        },
        "algorithm": algorithm_name,
        "paper_execution_mode": config.paper_execution_mode,
        "audit_execution_mode": config.audit_execution_mode,
        "oracle_valid": case["oracle"]["valid"],
        "oracle_reason": _csv_value(case["oracle"]["reason"]),
        "audit_passed": case["audit_passed"],
    }


def make_raw_rows(config, certified_cases, execution_id):
    validate_execution_config(config)
    if len(certified_cases) != config.case_count:
        raise ValueError("certified case count does not match config")
    rows = []
    for case in order_cases(certified_cases, config.case_order_seed):
        warmup_order = algorithm_order_for_round(
            config.algorithms,
            config.algorithm_order_seed,
            case["case_index"],
            1,
        )
        for algorithm_name in warmup_order:
            for _ in range(config.warmup_runs):
                warmup = run_timed_algorithm(
                    algorithm_name,
                    case["sequence"],
                    case["oracle"],
                    config.paper_execution_mode,
                    run_index=0,
                )
                if warmup["error"] or not warmup["output_correct"]:
                    raise RuntimeError("Week 12 warm-up failed")
        for run_index in range(1, config.measured_runs + 1):
            order = algorithm_order_for_round(
                config.algorithms,
                config.algorithm_order_seed,
                case["case_index"],
                run_index,
            )
            for position, algorithm_name in enumerate(order, start=1):
                row = {
                    **_raw_metadata(config, execution_id, case, algorithm_name),
                    **run_timed_algorithm(
                        algorithm_name,
                        case["sequence"],
                        case["oracle"],
                        config.paper_execution_mode,
                        run_index,
                        position,
                    ),
                }
                rows.append({field: _csv_value(row.get(field)) for field in RAW_FIELDS})
    return rows


def run_formal_in_memory(config, execution_id):
    """Run a supplied test or frozen contract without writing evidence."""
    validate_execution_config(config)
    validate_execution_id(execution_id)
    cases, audit_rows = build_cases_and_audits(config, execution_id)
    raw_rows = make_raw_rows(config, cases, execution_id)
    case_rows = summarize_by_case(raw_rows)
    group_rows = summarize_by_group(case_rows)
    actual = (len(raw_rows), len(case_rows), len(group_rows), len(audit_rows))
    expected = (
        config.raw_row_count,
        config.case_summary_row_count,
        config.group_summary_row_count,
        config.case_count,
    )
    if actual != expected:
        raise RuntimeError(f"Week 12 row counts changed: {actual} != {expected}")
    return {
        "raw_rows": raw_rows,
        "case_summary_rows": case_rows,
        "group_summary_rows": group_rows,
        "case_audit_rows": audit_rows,
    }


def initialize_formal_evidence(project_root, execution_id):
    """Recapture formal readiness, reserve the directory, and prewrite JSON."""
    gate = validate_week12_experiment_gate()
    validate_execution_id(execution_id)
    paths = require_unused_formal_output(
        build_formal_run_paths(project_root, execution_id)
    )
    environment = build_formal_environment_record(
        project_root,
        execution_id=execution_id,
        protocol_version=gate.protocol_version,
        paper_execution_mode=gate.paper_execution_mode,
        audit_execution_mode=gate.audit_execution_mode,
    )
    validate_formal_environment_record(
        environment,
        execution_id=execution_id,
        protocol_version=gate.protocol_version,
        paper_execution_mode=gate.paper_execution_mode,
        audit_execution_mode=gate.audit_execution_mode,
    )
    reserve_formal_run_directory(paths)
    started_at = datetime.now(timezone.utc)
    started_ns = time.perf_counter_ns()
    config_record = gate_to_dict(gate)
    write_json_exclusive(paths.config_json, config_record)
    write_json_exclusive(paths.environment_json, environment)
    if read_json_object(paths.config_json) != config_record:
        raise RuntimeError("Week 12 config.json verification failed")
    if read_json_object(paths.environment_json) != environment:
        raise RuntimeError("Week 12 environment.json verification failed")
    return paths, environment, started_at, started_ns


def write_formal_products(
    paths,
    products,
    environment,
    *,
    started_at,
    started_ns,
    gate=WEEK12_EXPERIMENT_GATE,
):
    """Write four CSVs and a manifest with a precise elapsed-time boundary."""
    validate_week12_experiment_gate(gate)
    rows = {
        "raw": products["raw_rows"],
        "case_summary": products["case_summary_rows"],
        "group_summary": products["group_summary_rows"],
        "case_audit": products["case_audit_rows"],
    }
    expected_counts = {
        "raw": gate.raw_row_count,
        "case_summary": gate.case_summary_row_count,
        "group_summary": gate.group_summary_row_count,
        "case_audit": gate.case_audit_row_count,
    }
    if {key: len(value) for key, value in rows.items()} != expected_counts:
        raise RuntimeError("Week 12 evidence row counts changed")
    fieldnames = {
        "raw": RAW_FIELDS,
        "case_summary": CASE_SUMMARY_FIELDS,
        "group_summary": GROUP_SUMMARY_FIELDS,
        "case_audit": CASE_AUDIT_FIELDS,
    }
    for label in ("raw", "case_summary", "group_summary", "case_audit"):
        write_csv_exclusive(
            getattr(paths, MANIFEST_FILE_ATTRIBUTES[label]),
            fieldnames[label],
            rows[label],
        )
    completed_ns = time.perf_counter_ns()
    completed_at = datetime.now(timezone.utc)
    measured_total_ns = sum(int(row["time_ns"]) for row in rows["raw"])
    files = {}
    for label, attribute in MANIFEST_FILE_ATTRIBUTES.items():
        path = getattr(paths, attribute)
        files[label] = {"path": path.name, "sha256": file_sha256(path)}
    manifest = {
        "protocol_version": gate.protocol_version,
        "execution_id": environment["execution_id"],
        "source_commit": environment["source_commit"],
        "row_counts": expected_counts,
        "experiment_started_at_utc": started_at.isoformat(),
        "experiment_completed_at_utc": completed_at.isoformat(),
        "experiment_elapsed_ns": completed_ns - started_ns,
        "experiment_elapsed_scope": EXPERIMENT_ELAPSED_SCOPE,
        "measured_call_total_ns": measured_total_ns,
        "files": files,
    }
    write_json_exclusive(paths.manifest_json, manifest)
    return manifest


def _execute_week12_formal(project_root=PROJECT_ROOT, *, execution_id):
    """Run the reviewed control flow after the public execution gate opens."""
    config = validate_execution_config(build_execution_config(), require_frozen=True)
    paths, environment, started_at, started_ns = initialize_formal_evidence(
        project_root,
        execution_id,
    )
    products = run_formal_in_memory(config, execution_id)
    manifest = write_formal_products(
        paths,
        products,
        environment,
        started_at=started_at,
        started_ns=started_ns,
    )
    from validate_week12_formal_sorting_outputs import validate_outputs

    report = validate_outputs(paths.run_dir)
    if report.get("valid") is not True:
        raise RuntimeError("Week 12 formal evidence failed validation")
    return {
        "status": "validated_formal_complete",
        "execution_id": execution_id,
        "run_dir": str(paths.run_dir),
        "row_counts": manifest["row_counts"],
        "validation_valid": True,
    }


def execute_week12_formal(project_root=PROJECT_ROOT, *, execution_id):
    """Refuse formal execution until Checkpoint 1 has been reviewed."""
    if not FORMAL_EXECUTION_ENABLED:
        raise RuntimeError(
            "formal Week 12 execution is disabled until checkpoint review"
        )
    return _execute_week12_formal(project_root, execution_id=execution_id)


def run_preflight(project_root=PROJECT_ROOT, *, execution_id):
    gate = validate_week12_experiment_gate()
    paths = require_unused_formal_output(
        build_formal_run_paths(project_root, execution_id)
    )
    environment = build_formal_environment_record(
        project_root,
        execution_id=execution_id,
        protocol_version=gate.protocol_version,
        paper_execution_mode=gate.paper_execution_mode,
        audit_execution_mode=gate.audit_execution_mode,
    )
    return {
        "status": "ready_not_executed",
        "execution_id": execution_id,
        "run_dir": str(paths.run_dir),
        "timing_readiness": environment["timing_readiness"],
        "formal_execution_enabled": False,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.preflight_only:
        result = run_preflight(execution_id=args.execution_id)
    else:
        result = execute_week12_formal(execution_id=args.execution_id)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
