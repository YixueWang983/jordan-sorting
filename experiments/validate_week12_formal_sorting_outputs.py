"""Fail closed when Week 12 formal evidence differs from the frozen gate."""

import argparse
import json
import math
import random
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from formal_execution_support import (  # noqa: E402
    file_sha256,
    validate_formal_environment_record,
)
from experiment_validation_support import (  # noqa: E402
    expected_case_summaries,
    expected_group_summaries,
    matches_expected,
    parse_bool,
    parse_int,
    require,
    safe_read_csv,
    safe_read_json,
    validate_case_metadata,
    validate_schema,
    validate_summary_rows,
)
from generators import INCREMENTAL_VALID, generate_sequence, make_case_id  # noqa: E402
from oracle import oracle  # noqa: E402
from paper_jordan import METRIC_NAMES as PAPER_METRIC_NAMES  # noqa: E402
from paper_jordan_sort import paper_jordan_diagnostics_valid  # noqa: E402
from run_week11_pilot import (  # noqa: E402
    CASE_AUDIT_FIELDS,
    CASE_SUMMARY_FIELDS,
    GROUP_SUMMARY_FIELDS,
    RAW_FIELDS,
    STRUCTURAL_FIELDS,
)
from stats import structure_profile  # noqa: E402
from week11_execution_context import output_dir_for_execution  # noqa: E402
from week12_experiment_gate import (  # noqa: E402
    WEEK12_EXPERIMENT_GATE,
    gate_to_dict,
    validate_week12_experiment_gate,
)


EXPERIMENT_ELAPSED_SCOPE = (
    "From formal evidence-directory reservation through config/environment "
    "writes, case generation, oracle certification, checked diagnostics, "
    "warm-ups, measured calls, summary construction, and CSV writes; "
    "excludes manifest writing and output validation."
)
MANIFEST_FILES = {
    "raw": "raw.csv",
    "case_summary": "case_summary.csv",
    "group_summary": "group_summary.csv",
    "case_audit": "case_audit.csv",
    "config": "config.json",
    "environment": "environment.json",
}
ENVIRONMENT_FIELDS = {
    "execution_id",
    "output_dir",
    "benchmark_environment",
    "source_commit",
    "protocol_version",
    "captured_before_timing",
    "timestamp_utc",
    "git_dirty",
    "head_matches_origin_main",
    "available_disk_bytes",
    "perf_counter_resolution",
    "power_status",
    "paper_execution_mode",
    "audit_execution_mode",
    "timing_readiness",
}
MANIFEST_FIELDS = {
    "protocol_version",
    "execution_id",
    "source_commit",
    "row_counts",
    "experiment_started_at_utc",
    "experiment_completed_at_utc",
    "experiment_elapsed_ns",
    "experiment_elapsed_scope",
    "measured_call_total_ns",
    "files",
}


def _sequence_sha256(sequence):
    import hashlib

    payload = json.dumps(
        list(sequence),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _seed_for_case(family, n, case_number, base_seed):
    if family == INCREMENTAL_VALID:
        return base_seed + n * 1000 + case_number
    return None


def _algorithm_order(gate, case_index, measured_round):
    ordered = list(gate.algorithms)
    random.Random(gate.algorithm_order_seed + case_index * 1009).shuffle(ordered)
    shift = (measured_round - 1) % len(ordered)
    return ordered[shift:] + ordered[:shift]


def rebuild_expected_cases(gate=WEEK12_EXPERIMENT_GATE):
    """Recreate exact cases and checked diagnostics without runner metadata."""
    validate_week12_experiment_gate(gate)
    cases = []
    hashes_by_group = {}
    for family in gate.valid_families:
        for n in gate.sizes:
            for case_number in range(1, gate.repetitions_for_family(family) + 1):
                seed = _seed_for_case(family, n, case_number, gate.seed)
                sequence = generate_sequence(family, n, seed=seed)
                if len(sequence) != n:
                    raise RuntimeError("Week 12 generator length changed")
                oracle_result = oracle(sequence)
                if not oracle_result["valid"] or not oracle_result["distinct_values"]:
                    raise RuntimeError("Week 12 expected case is no longer valid")
                digest = _sequence_sha256(sequence)
                group_hashes = hashes_by_group.setdefault((family, n), set())
                if digest in group_hashes:
                    raise RuntimeError("Week 12 expected cases contain duplicates")
                group_hashes.add(digest)
                profile = structure_profile(sequence, oracle_result=oracle_result)
                diagnostics = paper_jordan_diagnostics_valid(sequence)
                metrics = diagnostics.get("metrics")
                trace = diagnostics.get("trace")
                if (
                    diagnostics.get("invariants_valid") is not True
                    or diagnostics.get("output") != oracle_result["sorted"]
                    or diagnostics.get("processed_count") != n
                    or not isinstance(trace, list)
                    or not isinstance(metrics, dict)
                    or set(metrics) != set(PAPER_METRIC_NAMES)
                    or any(
                        isinstance(metrics[name], bool)
                        or not isinstance(metrics[name], int)
                        or metrics[name] < 0
                        for name in PAPER_METRIC_NAMES
                    )
                ):
                    raise RuntimeError("Week 12 checked diagnostic reconstruction failed")
                cases.append(
                    {
                        "case_id": make_case_id(family, n, case_number),
                        "case_index": len(cases) + 1,
                        "family": family,
                        "n": n,
                        "seed": seed,
                        "sequence_sha256": digest,
                        "oracle": oracle_result,
                        "profile": profile,
                        "audit": {
                            "audit_passed": True,
                            "diagnostic_output_sha256": _sequence_sha256(
                                diagnostics["output"]
                            ),
                            "diagnostic_processed_count": n,
                            "diagnostic_trace_event_count": len(trace),
                            **{
                                f"paper_{name}": metrics[name]
                                for name in PAPER_METRIC_NAMES
                            },
                        },
                    }
                )
    if len(cases) != gate.case_count:
        raise RuntimeError("Week 12 expected case count changed")
    ordered = list(cases)
    random.Random(gate.case_order_seed).shuffle(ordered)
    positions = {
        case["case_id"]: position
        for position, case in enumerate(ordered, start=1)
    }
    return {
        case["case_id"]: {
            **case,
            "case_execution_position": positions[case["case_id"]],
        }
        for case in cases
    }


def _parse_utc(value, field, errors):
    if not isinstance(value, str) or not value:
        errors.append(f"{field} is not a timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{field} is not an ISO timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        errors.append(f"{field} must use UTC")
        return None
    return parsed


def _validate_environment(environment, run_dir, gate, errors):
    if not isinstance(environment, dict):
        errors.append("environment must be an object")
        return None
    require(
        set(environment) == ENVIRONMENT_FIELDS,
        "environment fields do not match the Week 12 contract",
        errors,
    )
    execution_id = environment.get("execution_id")
    if isinstance(execution_id, str):
        require(run_dir.name == execution_id, "run directory/execution ID mismatch", errors)
    try:
        validate_formal_environment_record(
            environment,
            execution_id=execution_id,
            protocol_version=gate.protocol_version,
            paper_execution_mode=gate.paper_execution_mode,
            audit_execution_mode=gate.audit_execution_mode,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        errors.append(f"environment is invalid: {exc}")
        return None
    require(
        environment["output_dir"] == output_dir_for_execution(execution_id),
        "environment output directory mismatch",
        errors,
    )
    _parse_utc(environment.get("timestamp_utc"), "environment timestamp_utc", errors)
    resolution = environment.get("perf_counter_resolution")
    require(
        isinstance(resolution, (int, float))
        and not isinstance(resolution, bool)
        and math.isfinite(resolution)
        and resolution > 0,
        "environment perf_counter_resolution is invalid",
        errors,
    )
    readiness = environment.get("timing_readiness", {})
    require(readiness.get("execution_stage") == "formal", "formal readiness stage changed", errors)
    require(readiness.get("quality") == "clean", "formal readiness quality is not clean", errors)
    require(readiness.get("warnings") == [], "formal readiness contains warnings", errors)
    require(readiness.get("load_low") is True, "formal load threshold failed", errors)
    require(readiness.get("load_stable") is True, "formal load stability failed", errors)
    return execution_id


def _validate_raw_rows(rows, execution_id, expected_cases, gate, errors):
    require(len(rows) == gate.raw_row_count, "raw row count mismatch", errors)
    seen = set()
    measured_total = 0
    all_times_valid = True
    for row_number, row in enumerate(rows, start=2):
        label = f"raw row {row_number}"
        case_id = row.get("case_id")
        expected = expected_cases.get(case_id)
        if expected is None:
            errors.append(f"{label} has unknown case_id: {case_id}")
            continue
        matches_expected(row, "protocol_version", gate.protocol_version, label, errors)
        matches_expected(row, "execution_id", execution_id, label, errors)
        validate_case_metadata(row, expected, STRUCTURAL_FIELDS, label, errors)
        matches_expected(
            row,
            "case_execution_position",
            expected["case_execution_position"],
            label,
            errors,
        )
        algorithm = row.get("algorithm")
        require(algorithm in gate.algorithms, f"{label} algorithm is invalid", errors)
        matches_expected(row, "paper_execution_mode", gate.paper_execution_mode, label, errors)
        matches_expected(row, "audit_execution_mode", gate.audit_execution_mode, label, errors)
        run_index = parse_int(row.get("run_index"), f"{label} run_index", errors, 1)
        measured_round = parse_int(
            row.get("measured_round"), f"{label} measured_round", errors, 1
        )
        position = parse_int(
            row.get("algorithm_position"), f"{label} algorithm_position", errors, 1
        )
        if run_index is not None:
            require(run_index <= gate.measured_runs, f"{label} run_index out of range", errors)
        if run_index is not None and measured_round is not None:
            require(run_index == measured_round, f"{label} measured round mismatch", errors)
        if position is not None:
            require(position <= len(gate.algorithms), f"{label} algorithm position out of range", errors)
        if (
            run_index is not None
            and 1 <= run_index <= gate.measured_runs
            and position is not None
            and 1 <= position <= len(gate.algorithms)
            and algorithm in gate.algorithms
        ):
            expected_order = _algorithm_order(gate, expected["case_index"], run_index)
            require(
                expected_order[position - 1] == algorithm,
                f"{label} algorithm order mismatch",
                errors,
            )
            key = (case_id, run_index, algorithm)
            require(key not in seen, f"duplicate raw row: {key}", errors)
            seen.add(key)
        time_ns = parse_int(row.get("time_ns"), f"{label} time_ns", errors, 1)
        if time_ns is None:
            all_times_valid = False
        else:
            measured_total += time_ns
        for field in ("oracle_valid", "output_correct", "audit_passed"):
            parsed = parse_bool(row.get(field), f"{label} {field}", errors)
            if parsed is not None:
                require(parsed is True, f"{label} {field} must be true", errors)
        require(row.get("oracle_reason") in {"", None}, f"{label} oracle_reason must be empty", errors)
        require(row.get("error") in {"", None}, f"{label} error must be empty", errors)
    expected_keys = {
        (case_id, run_index, algorithm)
        for case_id in expected_cases
        for run_index in range(1, gate.measured_runs + 1)
        for algorithm in gate.algorithms
    }
    require(seen == expected_keys, "raw row product is incomplete or contains extras", errors)
    return measured_total if all_times_valid else None


def _validate_audit_rows(rows, execution_id, expected_cases, gate, errors):
    require(len(rows) == gate.case_audit_row_count, "case-audit row count mismatch", errors)
    seen = set()
    for row_number, row in enumerate(rows, start=2):
        label = f"case-audit row {row_number}"
        case_id = row.get("case_id")
        expected = expected_cases.get(case_id)
        if expected is None:
            errors.append(f"{label} has unknown case_id: {case_id}")
            continue
        require(case_id not in seen, f"duplicate case-audit row: {case_id}", errors)
        seen.add(case_id)
        matches_expected(row, "protocol_version", gate.protocol_version, label, errors)
        matches_expected(row, "execution_id", execution_id, label, errors)
        validate_case_metadata(row, expected, STRUCTURAL_FIELDS, label, errors)
        matches_expected(row, "oracle_valid", True, label, errors)
        matches_expected(row, "oracle_reason", None, label, errors)
        matches_expected(row, "audit_execution_mode", gate.audit_execution_mode, label, errors)
        for field, expected_value in expected["audit"].items():
            matches_expected(row, field, expected_value, label, errors)
    require(seen == set(expected_cases), "case-audit product is incomplete", errors)


def _validate_manifest(
    manifest,
    config,
    environment,
    run_dir,
    row_counts,
    measured_total_ns,
    errors,
):
    require(set(manifest) == MANIFEST_FIELDS, "manifest fields changed", errors)
    require(
        manifest.get("protocol_version") == config.get("protocol_version"),
        "manifest protocol version mismatch",
        errors,
    )
    require(
        manifest.get("execution_id") == environment.get("execution_id"),
        "manifest execution ID mismatch",
        errors,
    )
    require(
        manifest.get("source_commit") == environment.get("source_commit"),
        "manifest source commit mismatch",
        errors,
    )
    require(manifest.get("row_counts") == row_counts, "manifest row counts mismatch", errors)
    started = _parse_utc(
        manifest.get("experiment_started_at_utc"),
        "manifest experiment_started_at_utc",
        errors,
    )
    completed = _parse_utc(
        manifest.get("experiment_completed_at_utc"),
        "manifest experiment_completed_at_utc",
        errors,
    )
    timestamps_ordered = (
        started is not None and completed is not None and completed >= started
    )
    if started is not None and completed is not None:
        require(timestamps_ordered, "manifest experiment timestamps are reversed", errors)
    elapsed = parse_int(
        manifest.get("experiment_elapsed_ns"),
        "manifest experiment_elapsed_ns",
        errors,
        1,
    )
    require(elapsed is not None, "manifest experiment elapsed time is invalid", errors)
    require(
        manifest.get("experiment_elapsed_scope") == EXPERIMENT_ELAPSED_SCOPE,
        "manifest experiment elapsed scope changed",
        errors,
    )
    stored_measured_total = parse_int(
        manifest.get("measured_call_total_ns"),
        "manifest measured_call_total_ns",
        errors,
        1,
    )
    if stored_measured_total is not None and measured_total_ns is not None:
        require(
            stored_measured_total == measured_total_ns,
            "manifest measured-call total mismatch",
            errors,
        )
    if elapsed is not None and stored_measured_total is not None:
        require(
            elapsed >= stored_measured_total,
            "manifest experiment elapsed time is smaller than measured-call total",
            errors,
        )
    if timestamps_ordered and elapsed is not None:
        timestamp_elapsed_ns = int(
            (completed - started).total_seconds() * 1_000_000_000
        )
        tolerance_ns = max(1_000_000_000, elapsed // 100)
        require(
            abs(timestamp_elapsed_ns - elapsed) <= tolerance_ns,
            "manifest experiment elapsed time does not match UTC timestamps",
            errors,
        )
    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("manifest files must be an object")
        return
    require(set(files) == set(MANIFEST_FILES), "manifest file labels mismatch", errors)
    for label, filename in MANIFEST_FILES.items():
        info = files.get(label)
        if not isinstance(info, dict):
            errors.append(f"manifest file entry is invalid: {label}")
            continue
        require(set(info) == {"path", "sha256"}, f"manifest file fields changed: {label}", errors)
        require(info.get("path") == filename, f"manifest path mismatch: {label}", errors)
        path = run_dir / filename
        if not path.is_file():
            errors.append(f"manifest file is missing: {label}")
            continue
        try:
            actual_hash = file_sha256(path)
        except OSError as exc:
            errors.append(f"could not hash manifest file {label}: {exc}")
            continue
        require(info.get("sha256") == actual_hash, f"manifest hash mismatch: {label}", errors)


def _write_report(report, run_dir, report_json):
    output_path = Path(report_json) if report_json else run_dir / "validation_report.json"
    try:
        if report_json:
            try:
                output_path.resolve().relative_to(run_dir.resolve())
            except ValueError:
                pass
            else:
                raise ValueError("independent validation report must be outside the archived run")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            with output_path.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, sort_keys=True)
                handle.write("\n")
    except (OSError, ValueError) as exc:
        report["valid"] = False
        report["errors"].append(f"could not write validation report: {exc}")
    return report


def _validate_archived_report(run_dir, gate, errors):
    path = run_dir / "validation_report.json"
    require(path.is_file(), "archived validation report is missing", errors)
    if not path.is_file():
        return
    report = safe_read_json(path, "archived validation report", errors)
    if report is None:
        return
    expected_fields = {
        "valid",
        "errors",
        "run_dir",
        "row_counts",
        "validation_started_at_utc",
        "validation_completed_at_utc",
        "validation_elapsed_ns",
    }
    require(set(report) == expected_fields, "archived validation report fields changed", errors)
    require(report.get("valid") is True, "archived validation report is not valid", errors)
    require(report.get("errors") == [], "archived validation report contains errors", errors)
    require(
        report.get("row_counts")
        == {
            "raw": gate.raw_row_count,
            "case_summary": gate.case_summary_row_count,
            "group_summary": gate.group_summary_row_count,
            "case_audit": gate.case_audit_row_count,
        },
        "archived validation report row counts changed",
        errors,
    )
    started = _parse_utc(
        report.get("validation_started_at_utc"),
        "archived validation_started_at_utc",
        errors,
    )
    completed = _parse_utc(
        report.get("validation_completed_at_utc"),
        "archived validation_completed_at_utc",
        errors,
    )
    if started is not None and completed is not None:
        require(completed >= started, "archived validation timestamps are reversed", errors)
    parse_int(
        report.get("validation_elapsed_ns"),
        "archived validation_elapsed_ns",
        errors,
        1,
    )


def _validate_outputs(run_dir, report_json, validation_started_at, validation_started_ns):
    gate = validate_week12_experiment_gate()
    root = Path(run_dir)
    paths = {label: root / filename for label, filename in MANIFEST_FILES.items()}
    paths["manifest"] = root / "manifest.json"
    errors = []
    allowed_entries = {
        *MANIFEST_FILES.values(),
        "manifest.json",
        "validation_report.json",
    }
    try:
        actual_entries = {path.name for path in root.iterdir()}
    except OSError as exc:
        errors.append(f"could not enumerate run directory: {exc}")
    else:
        require(
            actual_entries <= allowed_entries,
            "run directory contains unexpected evidence entries",
            errors,
        )
    for label, path in paths.items():
        require(path.is_file(), f"missing required file: {label} -> {path}", errors)
    if report_json:
        _validate_archived_report(root, gate, errors)

    raw_rows = case_rows = group_rows = audit_rows = None
    if not errors:
        config = safe_read_json(paths["config"], "config", errors)
        environment = safe_read_json(paths["environment"], "environment", errors)
        manifest = safe_read_json(paths["manifest"], "manifest", errors)
        raw_rows = safe_read_csv(paths["raw"], "raw", errors)
        case_rows = safe_read_csv(paths["case_summary"], "case-summary", errors)
        group_rows = safe_read_csv(paths["group_summary"], "group-summary", errors)
        audit_rows = safe_read_csv(paths["case_audit"], "case-audit", errors)

        raw_schema = validate_schema(raw_rows, RAW_FIELDS, "raw", errors)
        case_schema = validate_schema(case_rows, CASE_SUMMARY_FIELDS, "case-summary", errors)
        group_schema = validate_schema(group_rows, GROUP_SUMMARY_FIELDS, "group-summary", errors)
        audit_schema = validate_schema(audit_rows, CASE_AUDIT_FIELDS, "case-audit", errors)
        require(config == gate_to_dict(gate), "config does not match the complete frozen Week 12 gate", errors)
        execution_id = (
            _validate_environment(environment, root, gate, errors)
            if environment is not None
            else None
        )
        expected_cases = {}
        try:
            expected_cases = rebuild_expected_cases(gate)
        except Exception as exc:
            errors.append(f"failed to rebuild expected cases: {type(exc).__name__}: {exc}")

        measured_total_ns = None
        if raw_schema and execution_id is not None and expected_cases:
            measured_total_ns = _validate_raw_rows(
                raw_rows, execution_id, expected_cases, gate, errors
            )
        if audit_schema and execution_id is not None and expected_cases:
            _validate_audit_rows(audit_rows, execution_id, expected_cases, gate, errors)

        expected_case_rows = {}
        expected_group_rows = {}
        if raw_schema:
            try:
                expected_case_rows = expected_case_summaries(raw_rows, errors)
                expected_group_rows = expected_group_summaries(expected_case_rows)
            except (KeyError, TypeError, ValueError, statistics.StatisticsError) as exc:
                errors.append(f"failed to recompute summaries: {type(exc).__name__}: {exc}")
        if case_schema and expected_case_rows:
            validate_summary_rows(
                case_rows,
                expected_case_rows,
                ("case_id", "algorithm"),
                "case-summary",
                errors,
            )
        if group_schema and expected_group_rows:
            validate_summary_rows(
                group_rows,
                expected_group_rows,
                ("family", "n", "algorithm"),
                "group-summary",
                errors,
            )

        row_counts = {
            "raw": len(raw_rows) if raw_rows is not None else None,
            "case_summary": len(case_rows) if case_rows is not None else None,
            "group_summary": len(group_rows) if group_rows is not None else None,
            "case_audit": len(audit_rows) if audit_rows is not None else None,
        }
        if manifest is not None and config is not None and environment is not None:
            try:
                _validate_manifest(
                    manifest,
                    config,
                    environment,
                    root,
                    row_counts,
                    measured_total_ns,
                    errors,
                )
            except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
                errors.append(f"failed to validate manifest: {type(exc).__name__}: {exc}")

    completed_ns = time.perf_counter_ns()
    completed_at = datetime.now(timezone.utc)
    report = {
        "valid": not errors,
        "errors": errors,
        "run_dir": str(root),
        "validation_started_at_utc": validation_started_at.isoformat(),
        "validation_completed_at_utc": completed_at.isoformat(),
        "validation_elapsed_ns": completed_ns - validation_started_ns,
    }
    if not errors:
        report["row_counts"] = {
            "raw": len(raw_rows),
            "case_summary": len(case_rows),
            "group_summary": len(group_rows),
            "case_audit": len(audit_rows),
        }
    return _write_report(report, root, report_json)


def validate_outputs(run_dir, report_json=None):
    """Validate one Week 12 run and return a report instead of crashing."""
    started_at = datetime.now(timezone.utc)
    started_ns = time.perf_counter_ns()
    try:
        return _validate_outputs(run_dir, report_json, started_at, started_ns)
    except Exception as exc:
        completed_at = datetime.now(timezone.utc)
        report = {
            "valid": False,
            "errors": [f"unexpected validation failure: {type(exc).__name__}: {exc}"],
            "run_dir": str(Path(run_dir)),
            "validation_started_at_utc": started_at.isoformat(),
            "validation_completed_at_utc": completed_at.isoformat(),
            "validation_elapsed_ns": time.perf_counter_ns() - started_ns,
        }
        return _write_report(report, Path(run_dir), report_json)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--report-json")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = validate_outputs(args.run_dir, args.report_json)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
