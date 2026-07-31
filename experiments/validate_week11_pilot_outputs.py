"""Fail closed when Week 11 pilot evidence differs from the frozen protocol."""

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import sys
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from generators import (  # noqa: E402
    INCREMENTAL_VALID,
    generate_sequence,
    make_case_id,
)
from oracle import oracle  # noqa: E402
from paper_jordan_sort import paper_jordan_diagnostics_valid  # noqa: E402
from stats import structure_profile  # noqa: E402
from week11_execution_context import (  # noqa: E402
    BENCHMARK_ENVIRONMENT_FIELDS,
    Week11ExecutionContext,
    output_dir_for_execution,
    validate_execution_context,
)
from week11_experiment_protocol import (  # noqa: E402
    WEEK11_EXPERIMENT_PROTOCOL,
    protocol_to_dict,
    validate_week11_experiment_protocol,
)


MANIFEST_FILE_LABELS = {
    "raw": "raw.csv",
    "case_summary": "case_summary.csv",
    "group_summary": "group_summary.csv",
    "case_audit": "case_audit.csv",
    "config": "config.json",
    "environment": "environment.json",
}
POWER_STATUS_FIELDS = {
    "source",
    "status",
    "on_ac_power",
    "battery_state",
}
PAPER_METRIC_NAMES = (
    "predecessor_accesses",
    "successor_accesses",
    "boundary_pair_checks",
    "sibling_scan_checks",
    "sibling_lists_created",
    "sibling_list_insertions",
    "sibling_list_splits",
    "split_items_scanned",
    "split_items_copied",
    "split_items_transferred",
    "output_insertions",
    "z1_boundary_adjustments",
    "z1_output_anchor_adjustments",
    "invariant_checks",
    "trace_event_count",
)
STRUCTURAL_FIELDS = (
    "category",
    "upper_interval_count",
    "lower_interval_count",
    "total_interval_count",
    "upper_root_count",
    "lower_root_count",
    "upper_nesting_count",
    "lower_nesting_count",
    "nesting_count",
    "nesting_density",
    "parented_interval_ratio",
    "upper_max_depth",
    "lower_max_depth",
    "max_depth",
    "upper_containment_pair_count",
    "lower_containment_pair_count",
    "containment_pair_count",
    "containment_pair_density",
    "upper_crossing_pair_count",
    "lower_crossing_pair_count",
    "total_crossing_pair_count",
)
PAPER_AUDIT_FIELDS = tuple(
    f"paper_{metric_name}" for metric_name in PAPER_METRIC_NAMES
)
RAW_FIELDS = (
    "protocol_version",
    "execution_id",
    "case_id",
    "case_index",
    "family",
    "n",
    "seed",
    "sequence_sha256",
    "case_execution_position",
    *STRUCTURAL_FIELDS,
    "algorithm",
    "paper_execution_mode",
    "audit_execution_mode",
    "run_index",
    "measured_round",
    "algorithm_position",
    "time_ns",
    "oracle_valid",
    "oracle_reason",
    "output_correct",
    "audit_passed",
    "error",
)
CASE_SUMMARY_FIELDS = (
    "case_id",
    "family",
    "n",
    "algorithm",
    "measured_run_count",
    "median_time_ns",
    "q1_time_ns",
    "q3_time_ns",
    "iqr_time_ns",
    "mean_time_ns",
    "stdev_time_ns",
    "all_correct",
    "error_count",
)
GROUP_SUMMARY_FIELDS = (
    "family",
    "n",
    "algorithm",
    "case_count",
    "median_case_time_ns",
    "q1_case_time_ns",
    "q3_case_time_ns",
    "iqr_case_time_ns",
    "mean_case_time_ns",
    "all_cases_correct",
    "total_error_count",
)
CASE_AUDIT_FIELDS = (
    "protocol_version",
    "execution_id",
    "case_id",
    "case_index",
    "family",
    "n",
    "seed",
    "sequence_sha256",
    "oracle_valid",
    "oracle_reason",
    *STRUCTURAL_FIELDS,
    "audit_execution_mode",
    "audit_passed",
    "diagnostic_output_sha256",
    "diagnostic_processed_count",
    "diagnostic_trace_event_count",
    *PAPER_AUDIT_FIELDS,
)
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
    "load_command_success",
    "load_snapshot",
    "paper_execution_mode",
    "audit_execution_mode",
}


def _require(condition, message, errors):
    if not condition:
        errors.append(message)


def _parse_int(value, field, errors, minimum=None):
    if value in {"", None}:
        errors.append(f"{field} is empty")
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        errors.append(f"{field} is not an integer: {value}")
        return None
    if minimum is not None and parsed < minimum:
        errors.append(f"{field} is below {minimum}: {parsed}")
        return None
    return parsed


def _parse_float(value, field, errors, minimum=None):
    if value in {"", None}:
        errors.append(f"{field} is empty")
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        errors.append(f"{field} is not numeric: {value}")
        return None
    if not math.isfinite(parsed):
        errors.append(f"{field} is not finite: {value}")
        return None
    if minimum is not None and parsed < minimum:
        errors.append(f"{field} is below {minimum}: {parsed}")
        return None
    return parsed


def _parse_bool(value, field, errors):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "false"}:
            return normalized == "true"
    errors.append(f"{field} is not a boolean: {value}")
    return None


def _safe_read_json(path, label, errors):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError) as exc:
        errors.append(f"failed to read {label} JSON: {type(exc).__name__}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} JSON must contain an object")
        return None
    return value


def _safe_read_csv(path, label, errors):
    try:
        with Path(path).open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames
            if fieldnames is None:
                errors.append(f"{label} CSV has no header")
                return None
            if len(fieldnames) != len(set(fieldnames)):
                errors.append(f"{label} CSV has duplicate fields")
                return None
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error, TypeError) as exc:
        errors.append(f"failed to read {label} CSV: {type(exc).__name__}: {exc}")
        return None
    if not rows:
        errors.append(f"{label} CSV is empty")
        return None
    return rows


def _validate_schema(rows, expected_fields, label, errors):
    if rows is None:
        return False
    actual = set(rows[0])
    expected = set(expected_fields)
    missing = expected - actual
    extra = actual - expected
    _require(not missing, f"{label} CSV missing fields: {sorted(missing)}", errors)
    _require(not extra, f"{label} CSV has unexpected fields: {sorted(extra)}", errors)
    return not missing and not extra


def _sequence_sha256(sequence):
    payload = json.dumps(
        list(sequence),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seed_for_case(family, n, case_number, base_seed):
    if family == INCREMENTAL_VALID:
        return base_seed + n * 1000 + case_number
    return None


@lru_cache(maxsize=1)
def rebuild_expected_cases():
    """Regenerate protocol cases without using runner-produced metadata."""
    protocol = validate_week11_experiment_protocol()
    cases = []
    hashes_by_group = {}
    for family in protocol.valid_families:
        repetitions = protocol.repetitions_for_family(family)
        for n in protocol.sizes:
            for case_number in range(1, repetitions + 1):
                case_seed = _seed_for_case(
                    family,
                    n,
                    case_number,
                    protocol.seed,
                )
                sequence = generate_sequence(family, n, seed=case_seed)
                if len(sequence) != n:
                    raise RuntimeError("Week 11 generator length changed")
                oracle_result = oracle(sequence)
                if not oracle_result["valid"]:
                    raise RuntimeError("Week 11 expected case is no longer valid")
                sequence_hash = _sequence_sha256(sequence)
                group_hashes = hashes_by_group.setdefault((family, n), set())
                if sequence_hash in group_hashes:
                    raise RuntimeError("Week 11 expected cases contain duplicates")
                group_hashes.add(sequence_hash)
                profile = structure_profile(
                    sequence,
                    oracle_result=oracle_result,
                )
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
                    raise RuntimeError(
                        "Week 11 checked diagnostic reconstruction failed"
                    )
                cases.append(
                    {
                        "case_id": make_case_id(family, n, case_number),
                        "case_index": len(cases) + 1,
                        "family": family,
                        "n": n,
                        "seed": case_seed,
                        "sequence_sha256": sequence_hash,
                        "oracle": oracle_result,
                        "profile": profile,
                        "audit": {
                            "audit_passed": True,
                            "diagnostic_output_sha256": _sequence_sha256(
                                diagnostics["output"]
                            ),
                            "diagnostic_processed_count": diagnostics[
                                "processed_count"
                            ],
                            "diagnostic_trace_event_count": len(trace),
                            **{
                                f"paper_{name}": metrics[name]
                                for name in PAPER_METRIC_NAMES
                            },
                        },
                    }
                )
    if len(cases) != protocol.case_count:
        raise RuntimeError("Week 11 expected case count changed")

    ordered = list(cases)
    random.Random(protocol.case_order_seed).shuffle(ordered)
    positions = {
        case["case_id"]: position
        for position, case in enumerate(ordered, start=1)
    }
    return {
        case["case_id"]: {**case, "case_execution_position": positions[case["case_id"]]}
        for case in cases
    }


def _algorithm_order(protocol, case_index, measured_round):
    ordered = list(protocol.algorithms)
    random.Random(
        protocol.algorithm_order_seed + case_index * 1009
    ).shuffle(ordered)
    shift = (measured_round - 1) % len(ordered)
    return ordered[shift:] + ordered[:shift]


def _matches_expected(row, field, expected, label, errors):
    value = row.get(field)
    full_label = f"{label} {field}"
    if expected is None:
        _require(value in {"", None}, f"{full_label} must be empty", errors)
    elif isinstance(expected, bool):
        parsed = _parse_bool(value, full_label, errors)
        if parsed is not None:
            _require(parsed is expected, f"{full_label} mismatch", errors)
    elif isinstance(expected, int):
        parsed = _parse_int(value, full_label, errors)
        if parsed is not None:
            _require(parsed == expected, f"{full_label} mismatch", errors)
    elif isinstance(expected, float):
        parsed = _parse_float(value, full_label, errors)
        if parsed is not None:
            _require(
                math.isclose(parsed, expected, rel_tol=1e-12, abs_tol=1e-12),
                f"{full_label} mismatch",
                errors,
            )
    else:
        _require(value == str(expected), f"{full_label} mismatch", errors)


def _validate_case_metadata(row, expected, label, errors):
    for field in (
        "case_id",
        "case_index",
        "family",
        "n",
        "seed",
        "sequence_sha256",
    ):
        _matches_expected(row, field, expected[field], label, errors)
    for field in STRUCTURAL_FIELDS:
        _matches_expected(row, field, expected["profile"][field], label, errors)


def _validate_environment(environment, run_dir, errors):
    if set(environment) != ENVIRONMENT_FIELDS:
        errors.append("environment fields do not match the Week 11 contract")
        return None
    try:
        context = Week11ExecutionContext(
            execution_id=environment["execution_id"],
            output_dir=environment["output_dir"],
            benchmark_environment=environment["benchmark_environment"],
            source_commit=environment["source_commit"],
        )
        validate_execution_context(context)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(f"environment execution context is invalid: {exc}")
        return None
    protocol = WEEK11_EXPERIMENT_PROTOCOL
    _require(
        run_dir.name == context.execution_id,
        "run directory/execution ID mismatch",
        errors,
    )
    _require(
        environment["protocol_version"] == protocol.protocol_version,
        "environment protocol version mismatch",
        errors,
    )
    _require(
        environment["paper_execution_mode"] == protocol.paper_execution_mode,
        "environment paper mode mismatch",
        errors,
    )
    _require(
        environment["audit_execution_mode"] == protocol.audit_execution_mode,
        "environment audit mode mismatch",
        errors,
    )
    for field in (
        "captured_before_timing",
        "head_matches_origin_main",
        "load_command_success",
    ):
        _require(
            environment[field] is True,
            f"environment {field} must be true",
            errors,
        )
    _require(
        environment["git_dirty"] is False,
        "environment git_dirty must be false",
        errors,
    )
    _require(
        isinstance(environment["timestamp_utc"], str)
        and bool(environment["timestamp_utc"]),
        "environment timestamp is invalid",
        errors,
    )
    _require(
        isinstance(environment["available_disk_bytes"], int)
        and not isinstance(environment["available_disk_bytes"], bool)
        and environment["available_disk_bytes"] >= 0,
        "environment available disk is invalid",
        errors,
    )
    resolution = environment["perf_counter_resolution"]
    _require(
        isinstance(resolution, (int, float))
        and not isinstance(resolution, bool)
        and math.isfinite(resolution)
        and resolution > 0,
        "environment clock resolution is invalid",
        errors,
    )
    _validate_power_status(environment["power_status"], errors)
    _require(
        isinstance(environment["load_snapshot"], str)
        and bool(environment["load_snapshot"]),
        "environment load_snapshot is invalid",
        errors,
    )
    return context


def _validate_power_status(power_status, errors):
    if not isinstance(power_status, dict):
        errors.append("environment power_status must be an object")
        return
    _require(
        set(power_status) == POWER_STATUS_FIELDS,
        "environment power_status fields changed",
        errors,
    )
    if set(power_status) != POWER_STATUS_FIELDS:
        return
    source = power_status["source"]
    status = power_status["status"]
    on_ac_power = power_status["on_ac_power"]
    battery_state = power_status["battery_state"]
    _require(
        isinstance(source, str) and bool(source),
        "environment power_status source is invalid",
        errors,
    )
    _require(
        status in {"available", "not_applicable"},
        "environment power_status is unavailable or invalid",
        errors,
    )
    _require(
        on_ac_power is None or isinstance(on_ac_power, bool),
        "environment power_status on_ac_power is invalid",
        errors,
    )
    _require(
        battery_state
        in {
            "charging",
            "discharging",
            "full",
            "not_applicable",
            "unknown",
        },
        "environment power_status battery_state is invalid",
        errors,
    )
    if status == "not_applicable":
        _require(
            on_ac_power is None and battery_state == "not_applicable",
            "not-applicable power status is inconsistent",
            errors,
        )
    if status == "available":
        _require(
            isinstance(on_ac_power, bool)
            and battery_state
            in {"charging", "discharging", "full", "unknown"},
            "available power status is inconsistent",
            errors,
        )
    if status == "unavailable":
        _require(
            on_ac_power is None and battery_state == "unknown",
            "unavailable power status is inconsistent",
            errors,
        )


def _validate_raw_rows(rows, context, expected_cases, errors):
    protocol = WEEK11_EXPERIMENT_PROTOCOL
    _require(len(rows) == protocol.raw_row_count, "raw row count mismatch", errors)
    seen = set()
    for row_number, row in enumerate(rows, start=2):
        label = f"raw row {row_number}"
        case_id = row.get("case_id")
        expected = expected_cases.get(case_id)
        if expected is None:
            errors.append(f"{label} has unknown case_id: {case_id}")
            continue
        _matches_expected(
            row,
            "protocol_version",
            protocol.protocol_version,
            label,
            errors,
        )
        _matches_expected(row, "execution_id", context.execution_id, label, errors)
        _validate_case_metadata(row, expected, label, errors)
        _matches_expected(
            row,
            "case_execution_position",
            expected["case_execution_position"],
            label,
            errors,
        )
        algorithm = row.get("algorithm")
        _require(
            algorithm in protocol.algorithms,
            f"{label} algorithm is invalid",
            errors,
        )
        _matches_expected(
            row,
            "paper_execution_mode",
            protocol.paper_execution_mode,
            label,
            errors,
        )
        _matches_expected(
            row,
            "audit_execution_mode",
            protocol.audit_execution_mode,
            label,
            errors,
        )
        run_index = _parse_int(row.get("run_index"), f"{label} run_index", errors, 1)
        measured_round = _parse_int(
            row.get("measured_round"),
            f"{label} measured_round",
            errors,
            1,
        )
        position = _parse_int(
            row.get("algorithm_position"),
            f"{label} algorithm_position",
            errors,
            1,
        )
        if run_index is not None:
            _require(
                run_index <= protocol.measured_runs,
                f"{label} run_index out of range",
                errors,
            )
        if run_index is not None and measured_round is not None:
            _require(
                run_index == measured_round,
                f"{label} measured round mismatch",
                errors,
            )
        if position is not None:
            _require(
                position <= len(protocol.algorithms),
                f"{label} algorithm position out of range",
                errors,
            )
        if (
            run_index is not None
            and 1 <= run_index <= protocol.measured_runs
            and position is not None
            and 1 <= position <= len(protocol.algorithms)
            and algorithm in protocol.algorithms
        ):
            expected_order = _algorithm_order(
                protocol,
                expected["case_index"],
                run_index,
            )
            _require(
                expected_order[position - 1] == algorithm,
                f"{label} algorithm order mismatch",
                errors,
            )
            key = (case_id, run_index, algorithm)
            _require(key not in seen, f"duplicate raw row: {key}", errors)
            seen.add(key)
        _parse_int(row.get("time_ns"), f"{label} time_ns", errors, 0)
        for field in ("oracle_valid", "output_correct", "audit_passed"):
            parsed = _parse_bool(row.get(field), f"{label} {field}", errors)
            if parsed is not None:
                _require(parsed is True, f"{label} {field} must be true", errors)
        _require(
            row.get("oracle_reason") in {"", None},
            f"{label} oracle_reason must be empty",
            errors,
        )
        _require(row.get("error") in {"", None}, f"{label} error must be empty", errors)

    expected_keys = {
        (case_id, run_index, algorithm)
        for case_id in expected_cases
        for run_index in range(1, protocol.measured_runs + 1)
        for algorithm in protocol.algorithms
    }
    _require(
        seen == expected_keys,
        "raw row product is incomplete or contains extras",
        errors,
    )


def _validate_audit_rows(rows, context, expected_cases, errors):
    protocol = WEEK11_EXPERIMENT_PROTOCOL
    _require(len(rows) == protocol.case_count, "case-audit row count mismatch", errors)
    seen = set()
    for row_number, row in enumerate(rows, start=2):
        label = f"case-audit row {row_number}"
        case_id = row.get("case_id")
        expected = expected_cases.get(case_id)
        if expected is None:
            errors.append(f"{label} has unknown case_id: {case_id}")
            continue
        _require(case_id not in seen, f"duplicate case-audit row: {case_id}", errors)
        seen.add(case_id)
        _matches_expected(
            row,
            "protocol_version",
            protocol.protocol_version,
            label,
            errors,
        )
        _matches_expected(row, "execution_id", context.execution_id, label, errors)
        _validate_case_metadata(row, expected, label, errors)
        _matches_expected(row, "oracle_valid", True, label, errors)
        _matches_expected(row, "oracle_reason", None, label, errors)
        _matches_expected(
            row,
            "audit_execution_mode",
            protocol.audit_execution_mode,
            label,
            errors,
        )
        for field, expected_value in expected["audit"].items():
            _matches_expected(
                row,
                field,
                expected_value,
                label,
                errors,
            )
    _require(seen == set(expected_cases), "case-audit product is incomplete", errors)


def _quartiles(values):
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0], ordered[0], 0
    midpoint = len(ordered) // 2
    lower = ordered[:midpoint]
    upper = ordered[midpoint:] if len(ordered) % 2 == 0 else ordered[midpoint + 1 :]
    q1 = statistics.median(lower) if lower else ordered[0]
    q3 = statistics.median(upper) if upper else ordered[-1]
    return q1, q3, q3 - q1


def _expected_case_summaries(raw_rows, errors):
    grouped = {}
    for row in raw_rows:
        grouped.setdefault((row.get("case_id"), row.get("algorithm")), []).append(row)
    result = {}
    for key, rows in grouped.items():
        times = []
        for row in rows:
            parsed = _parse_int(
                row.get("time_ns"),
                f"summary source {key} time_ns",
                errors,
                0,
            )
            if parsed is not None:
                times.append(parsed)
        if not times:
            continue
        q1, q3, iqr = _quartiles(times)
        first = rows[0]
        result[key] = {
            "case_id": key[0],
            "family": first.get("family"),
            "n": int(first.get("n")),
            "algorithm": key[1],
            "measured_run_count": len(times),
            "median_time_ns": statistics.median(times),
            "q1_time_ns": q1,
            "q3_time_ns": q3,
            "iqr_time_ns": iqr,
            "mean_time_ns": statistics.mean(times),
            "stdev_time_ns": statistics.stdev(times) if len(times) > 1 else 0,
            "all_correct": True,
            "error_count": 0,
        }
    return result


def _expected_group_summaries(case_summaries):
    grouped = {}
    for row in case_summaries.values():
        key = (row["family"], row["n"], row["algorithm"])
        grouped.setdefault(key, []).append(row)
    result = {}
    for key, rows in grouped.items():
        medians = [float(row["median_time_ns"]) for row in rows]
        q1, q3, iqr = _quartiles(medians)
        result[key] = {
            "family": key[0],
            "n": key[1],
            "algorithm": key[2],
            "case_count": len(rows),
            "median_case_time_ns": statistics.median(medians),
            "q1_case_time_ns": q1,
            "q3_case_time_ns": q3,
            "iqr_case_time_ns": iqr,
            "mean_case_time_ns": statistics.mean(medians),
            "all_cases_correct": True,
            "total_error_count": 0,
        }
    return result


def _validate_summary_rows(rows, expected, key_fields, label, errors):
    _require(len(rows) == len(expected), f"{label} row count mismatch", errors)
    seen = set()
    bool_fields = {"all_correct", "all_cases_correct"}
    int_fields = {
        "n",
        "measured_run_count",
        "error_count",
        "case_count",
        "total_error_count",
    }
    for row_number, row in enumerate(rows, start=2):
        key = tuple(
            int(row[field])
            if field == "n" and str(row.get(field, "")).isdigit()
            else row.get(field)
            for field in key_fields
        )
        expected_row = expected.get(key)
        if expected_row is None:
            errors.append(f"{label} row {row_number} has unknown key: {key}")
            continue
        _require(key not in seen, f"duplicate {label} row: {key}", errors)
        seen.add(key)
        for field, expected_value in expected_row.items():
            field_label = f"{label} row {row_number} {field}"
            if field in bool_fields:
                parsed = _parse_bool(row.get(field), field_label, errors)
                if parsed is not None:
                    _require(
                        parsed is expected_value,
                        f"{field_label} mismatch",
                        errors,
                    )
            elif field in int_fields:
                parsed = _parse_int(row.get(field), field_label, errors, 0)
                if parsed is not None:
                    _require(
                        parsed == expected_value,
                        f"{field_label} mismatch",
                        errors,
                    )
            elif isinstance(expected_value, (int, float)):
                parsed = _parse_float(row.get(field), field_label, errors, 0)
                if parsed is not None:
                    _require(
                        math.isclose(
                            float(parsed),
                            float(expected_value),
                            rel_tol=1e-12,
                            abs_tol=1e-9,
                        ),
                        f"{field_label} mismatch",
                        errors,
                    )
            else:
                _require(
                    row.get(field) == str(expected_value),
                    f"{field_label} mismatch",
                    errors,
                )
    _require(seen == set(expected), f"{label} product is incomplete", errors)


def _validate_manifest(manifest, config, environment, run_dir, row_counts, errors):
    expected_manifest_fields = {
        "protocol_version",
        "execution_id",
        "source_commit",
        "row_counts",
        "files",
    }
    _require(
        set(manifest) == expected_manifest_fields,
        "manifest fields do not match the Week 11 contract",
        errors,
    )
    _require(
        manifest.get("protocol_version") == config.get("protocol_version"),
        "manifest protocol version mismatch",
        errors,
    )
    _require(
        manifest.get("execution_id") == environment.get("execution_id"),
        "manifest execution ID mismatch",
        errors,
    )
    _require(
        manifest.get("source_commit") == environment.get("source_commit"),
        "manifest source commit mismatch",
        errors,
    )
    _require(
        manifest.get("row_counts") == row_counts,
        "manifest row counts mismatch",
        errors,
    )
    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("manifest files must be an object")
        return
    _require(
        set(files) == set(MANIFEST_FILE_LABELS),
        "manifest file labels mismatch",
        errors,
    )
    for label, filename in MANIFEST_FILE_LABELS.items():
        info = files.get(label)
        if not isinstance(info, dict):
            errors.append(f"manifest file entry is invalid: {label}")
            continue
        _require(
            set(info) == {"path", "sha256"},
            f"manifest file entry fields changed: {label}",
            errors,
        )
        _require(
            info.get("path") == filename,
            f"manifest path mismatch: {label}",
            errors,
        )
        path = run_dir / filename
        if not path.is_file():
            errors.append(f"manifest file is missing: {label}")
            continue
        try:
            actual_hash = _file_sha256(path)
        except OSError as exc:
            errors.append(f"could not hash manifest file {label}: {exc}")
            continue
        _require(
            info.get("sha256") == actual_hash,
            f"manifest hash mismatch: {label}",
            errors,
        )


def _validate_outputs(run_dir, report_json=None):
    """Run the Week 11 checks after the public fail-closed boundary."""
    validate_week11_experiment_protocol()
    root = Path(run_dir)
    paths = {
        label: root / filename for label, filename in MANIFEST_FILE_LABELS.items()
    }
    paths["manifest"] = root / "manifest.json"
    errors = []
    for label, path in paths.items():
        _require(path.is_file(), f"missing required file: {label} -> {path}", errors)

    raw_rows = case_rows = group_rows = audit_rows = None
    if not errors:
        config = _safe_read_json(paths["config"], "config", errors)
        environment = _safe_read_json(paths["environment"], "environment", errors)
        manifest = _safe_read_json(paths["manifest"], "manifest", errors)
        raw_rows = _safe_read_csv(paths["raw"], "raw", errors)
        case_rows = _safe_read_csv(paths["case_summary"], "case-summary", errors)
        group_rows = _safe_read_csv(paths["group_summary"], "group-summary", errors)
        audit_rows = _safe_read_csv(paths["case_audit"], "case-audit", errors)

        raw_schema = _validate_schema(raw_rows, RAW_FIELDS, "raw", errors)
        case_schema = _validate_schema(
            case_rows,
            CASE_SUMMARY_FIELDS,
            "case-summary",
            errors,
        )
        group_schema = _validate_schema(
            group_rows,
            GROUP_SUMMARY_FIELDS,
            "group-summary",
            errors,
        )
        audit_schema = _validate_schema(
            audit_rows,
            CASE_AUDIT_FIELDS,
            "case-audit",
            errors,
        )

        config_valid = config == protocol_to_dict() if config is not None else False
        _require(
            config_valid,
            "config does not match the frozen Week 11 protocol",
            errors,
        )
        context = (
            _validate_environment(environment, root, errors)
            if environment is not None
            else None
        )
        expected_cases = {}
        try:
            expected_cases = rebuild_expected_cases()
        except Exception as exc:
            errors.append(
                "failed to rebuild expected cases: "
                f"{type(exc).__name__}: {exc}"
            )

        if raw_schema and context is not None and expected_cases:
            _validate_raw_rows(raw_rows, context, expected_cases, errors)
        if audit_schema and context is not None and expected_cases:
            _validate_audit_rows(audit_rows, context, expected_cases, errors)

        expected_case_rows = {}
        expected_group_rows = {}
        if raw_schema:
            try:
                expected_case_rows = _expected_case_summaries(raw_rows, errors)
                expected_group_rows = _expected_group_summaries(expected_case_rows)
            except (KeyError, TypeError, ValueError, statistics.StatisticsError) as exc:
                errors.append(
                    "failed to recompute summaries: "
                    f"{type(exc).__name__}: {exc}"
                )
        if case_schema and expected_case_rows:
            _validate_summary_rows(
                case_rows,
                expected_case_rows,
                ("case_id", "algorithm"),
                "case-summary",
                errors,
            )
        if group_schema and expected_group_rows:
            _validate_summary_rows(
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
                    errors,
                )
            except (AttributeError, KeyError, OSError, TypeError, ValueError) as exc:
                errors.append(
                    "failed to validate manifest: "
                    f"{type(exc).__name__}: {exc}"
                )

    report = {
        "valid": not errors,
        "errors": errors,
        "run_dir": str(root),
    }
    if not errors:
        report["row_counts"] = {
            "raw": len(raw_rows),
            "case_summary": len(case_rows),
            "group_summary": len(group_rows),
            "case_audit": len(audit_rows),
        }
    output_path = Path(report_json) if report_json else root / "validation_report.json"
    try:
        output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        report["valid"] = False
        report["errors"].append(f"could not write validation report: {exc}")
    return report


def validate_outputs(run_dir, report_json=None):
    """Validate one Week 11 execution and always return a report."""
    try:
        return _validate_outputs(run_dir, report_json)
    except Exception as exc:
        root = Path(run_dir)
        report = {
            "valid": False,
            "errors": [
                "unexpected validation failure: "
                f"{type(exc).__name__}: {exc}"
            ],
            "run_dir": str(root),
        }
        output_path = (
            Path(report_json)
            if report_json
            else root / "validation_report.json"
        )
        try:
            output_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as write_error:
            report["errors"].append(
                f"could not write validation report: {write_error}"
            )
        return report


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
