"""Shared fail-closed parsing and aggregation helpers for experiment validators."""

import csv
import json
import math
import statistics
from pathlib import Path


def require(condition, message, errors):
    if not condition:
        errors.append(message)


def parse_int(value, field, errors, minimum=None):
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


def parse_float(value, field, errors, minimum=None):
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


def parse_bool(value, field, errors):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "false"}:
            return normalized == "true"
    errors.append(f"{field} is not a boolean: {value}")
    return None


def safe_read_json(path, label, errors):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError) as exc:
        errors.append(f"failed to read {label} JSON: {type(exc).__name__}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} JSON must contain an object")
        return None
    return value


def safe_read_csv(path, label, errors):
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


def validate_schema(rows, expected_fields, label, errors):
    if rows is None:
        return False
    actual = set(rows[0])
    expected = set(expected_fields)
    missing = expected - actual
    extra = actual - expected
    require(not missing, f"{label} CSV missing fields: {sorted(missing)}", errors)
    require(not extra, f"{label} CSV has unexpected fields: {sorted(extra)}", errors)
    return not missing and not extra


def matches_expected(row, field, expected, label, errors):
    value = row.get(field)
    full_label = f"{label} {field}"
    if expected is None:
        require(value in {"", None}, f"{full_label} must be empty", errors)
    elif isinstance(expected, bool):
        parsed = parse_bool(value, full_label, errors)
        if parsed is not None:
            require(parsed is expected, f"{full_label} mismatch", errors)
    elif isinstance(expected, int):
        parsed = parse_int(value, full_label, errors)
        if parsed is not None:
            require(parsed == expected, f"{full_label} mismatch", errors)
    elif isinstance(expected, float):
        parsed = parse_float(value, full_label, errors)
        if parsed is not None:
            require(
                math.isclose(parsed, expected, rel_tol=1e-12, abs_tol=1e-12),
                f"{full_label} mismatch",
                errors,
            )
    else:
        require(value == str(expected), f"{full_label} mismatch", errors)


def validate_case_metadata(row, expected, structural_fields, label, errors):
    for field in (
        "case_id",
        "case_index",
        "family",
        "n",
        "seed",
        "sequence_sha256",
    ):
        matches_expected(row, field, expected[field], label, errors)
    for field in structural_fields:
        matches_expected(row, field, expected["profile"][field], label, errors)


def quartiles(values):
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0], ordered[0], 0
    midpoint = len(ordered) // 2
    lower = ordered[:midpoint]
    upper = ordered[midpoint:] if len(ordered) % 2 == 0 else ordered[midpoint + 1 :]
    q1 = statistics.median(lower) if lower else ordered[0]
    q3 = statistics.median(upper) if upper else ordered[-1]
    return q1, q3, q3 - q1


def expected_case_summaries(raw_rows, errors):
    grouped = {}
    for row in raw_rows:
        grouped.setdefault((row.get("case_id"), row.get("algorithm")), []).append(row)
    result = {}
    for key, rows in grouped.items():
        times = []
        for row in rows:
            parsed = parse_int(
                row.get("time_ns"),
                f"summary source {key} time_ns",
                errors,
                0,
            )
            if parsed is not None:
                times.append(parsed)
        if not times:
            continue
        q1, q3, iqr = quartiles(times)
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


def expected_group_summaries(case_summaries):
    grouped = {}
    for row in case_summaries.values():
        key = (row["family"], row["n"], row["algorithm"])
        grouped.setdefault(key, []).append(row)
    result = {}
    for key, rows in grouped.items():
        medians = [float(row["median_time_ns"]) for row in rows]
        q1, q3, iqr = quartiles(medians)
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


def validate_summary_rows(rows, expected, key_fields, label, errors):
    require(len(rows) == len(expected), f"{label} row count mismatch", errors)
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
        require(key not in seen, f"duplicate {label} row: {key}", errors)
        seen.add(key)
        for field, expected_value in expected_row.items():
            field_label = f"{label} row {row_number} {field}"
            if field in bool_fields:
                parsed = parse_bool(row.get(field), field_label, errors)
                if parsed is not None:
                    require(parsed is expected_value, f"{field_label} mismatch", errors)
            elif field in int_fields:
                parsed = parse_int(row.get(field), field_label, errors, 0)
                if parsed is not None:
                    require(parsed == expected_value, f"{field_label} mismatch", errors)
            elif isinstance(expected_value, (int, float)):
                parsed = parse_float(row.get(field), field_label, errors, 0)
                if parsed is not None:
                    require(
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
                require(
                    row.get(field) == str(expected_value),
                    f"{field_label} mismatch",
                    errors,
                )
    require(seen == set(expected), f"{label} product is incomplete", errors)
