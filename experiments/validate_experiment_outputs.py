"""Validate generated benchmark output files before thesis use."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from run_week7_pilot import (  # noqa: E402
    GROUP_FIELDS,
    RAW_FIELDS,
    SUMMARY_FIELDS,
    summarize_by_case,
    summarize_by_group,
)


DEFAULT_RUN_DIR = PROJECT_ROOT / "results" / "runs" / "week8_timing_dry_run"


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return bool(value)


def _require(condition, message, errors):
    if not condition:
        errors.append(message)


def _stringify_csv_value(value):
    if value is None:
        return ""
    return str(value)


def _rows_equal(left_rows, right_rows, fields):
    if len(left_rows) != len(right_rows):
        return False
    normalized_left = [
        {field: _stringify_csv_value(row.get(field, "")) for field in fields}
        for row in left_rows
    ]
    normalized_right = [
        {field: _stringify_csv_value(row.get(field, "")) for field in fields}
        for row in right_rows
    ]
    sort_key = lambda row: json.dumps(row, sort_keys=True)
    return sorted(normalized_left, key=sort_key) == sorted(normalized_right, key=sort_key)


def _expected_case_count(config):
    randomized_families = {
        "incremental_valid",
        "random_invalid",
        "mutation_based_invalid",
    }
    total = 0
    for family in config["families"]:
        repetitions = config["randomized_cases"] if family in randomized_families else 1
        total += len(config["sizes"]) * repetitions
    return total


def _validate_schema(rows, expected_fields, label, errors):
    if not rows:
        errors.append(f"{label} CSV is empty")
        return
    missing = set(expected_fields) - set(rows[0].keys())
    extra = set(rows[0].keys()) - set(expected_fields)
    _require(not missing, f"{label} CSV missing fields: {sorted(missing)}", errors)
    _require(not extra, f"{label} CSV has unexpected fields: {sorted(extra)}", errors)


def _validate_raw_rows(raw_rows, config, errors):
    expected_cases = _expected_case_count(config)
    expected_raw = expected_cases * len(config["algorithms"]) * config["measured_runs"]
    _require(
        len(raw_rows) == expected_raw,
        f"raw row count {len(raw_rows)} != expected {expected_raw}",
        errors,
    )

    algorithms = {row["algorithm"] for row in raw_rows}
    _require(
        algorithms == set(config["algorithms"]),
        f"raw algorithms {sorted(algorithms)} != config algorithms {config['algorithms']}",
        errors,
    )

    errors_with_messages = sum(1 for row in raw_rows if row["error"])
    incorrect = sum(1 for row in raw_rows if not _as_bool(row["overall_correct"]))
    _require(errors_with_messages == 0, f"raw rows contain {errors_with_messages} errors", errors)
    _require(incorrect == 0, f"raw rows contain {incorrect} incorrect outputs", errors)

    for row in raw_rows:
        if not row["error"]:
            _require(row["time_ns"] != "", f"missing time_ns for {row['case_id']}", errors)
        for field in ["containment_pair_density", "parented_interval_ratio"]:
            value = row[field]
            if value != "":
                try:
                    numeric = float(value)
                except ValueError:
                    errors.append(f"{field} is not numeric: {value}")
                    continue
                _require(
                    0.0 <= numeric <= 1.0,
                    f"{field} out of range: {value}",
                    errors,
                )

    grouped = {}
    for row in raw_rows:
        grouped.setdefault((row["case_id"], row["run_index"]), []).append(row["algorithm"])
    for (case_id, run_index), algorithms_for_round in grouped.items():
        _require(
            len(algorithms_for_round) == len(config["algorithms"]),
            f"{case_id} round {run_index} has duplicate or missing algorithm rows",
            errors,
        )
        _require(
            set(algorithms_for_round) == set(config["algorithms"]),
            f"{case_id} round {run_index} missing algorithms",
            errors,
        )


def _validate_summaries(case_rows, group_rows, config, errors):
    expected_cases = _expected_case_count(config)
    expected_case_rows = expected_cases * len(config["algorithms"])
    expected_group_rows = len(config["families"]) * len(config["sizes"]) * len(
        config["algorithms"]
    )
    _require(
        len(case_rows) == expected_case_rows,
        f"case-summary row count {len(case_rows)} != expected {expected_case_rows}",
        errors,
    )
    _require(
        len(group_rows) == expected_group_rows,
        f"group-summary row count {len(group_rows)} != expected {expected_group_rows}",
        errors,
    )
    _require(
        all(_as_bool(row["all_correct"]) for row in case_rows),
        "case summary contains all_correct=False",
        errors,
    )
    _require(
        all(_as_bool(row["all_cases_correct"]) for row in group_rows),
        "group summary contains all_cases_correct=False",
        errors,
    )
    _require(
        sum(int(row["error_count"]) for row in case_rows) == 0,
        "case summary contains errors",
        errors,
    )
    _require(
        sum(int(row["total_error_count"]) for row in group_rows) == 0,
        "group summary contains errors",
        errors,
    )


def _validate_manifest(manifest, config, environment, run_root, errors):
    _require(
        manifest.get("run_id") == config.get("run_id") == environment.get("run_id"),
        "run_id mismatch across manifest/config/environment",
        errors,
    )
    _require(
        manifest.get("git_commit_sha") == environment.get("git_commit_sha"),
        "manifest/environment git_commit_sha mismatch",
        errors,
    )

    for file_label, file_info in manifest.get("files", {}).items():
        path = Path(file_info.get("path", ""))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.exists():
            errors.append(f"manifest file is missing: {file_label} -> {path}")
            continue
        actual_hash = file_sha256(path)
        expected_hash = file_info.get("sha256")
        _require(
            actual_hash == expected_hash,
            f"manifest hash mismatch for {file_label}",
            errors,
        )

    expected_labels = {
        "raw_csv",
        "case_summary_csv",
        "group_summary_csv",
        "environment_json",
        "config_json",
        "auto_report_md",
    }
    missing_labels = expected_labels - set(manifest.get("files", {}))
    _require(
        not missing_labels,
        f"manifest missing file entries: {sorted(missing_labels)}",
        errors,
    )

    for field_name, expected_path in [
        ("raw_csv", run_root / "raw.csv"),
        ("case_summary_csv", run_root / "case_summary.csv"),
        ("group_summary_csv", run_root / "group_summary.csv"),
        ("environment_json", run_root / "environment.json"),
        ("config_json", run_root / "config.json"),
        ("auto_report_md", run_root / "auto_report.md"),
    ]:
        manifest_path = Path(manifest.get("files", {}).get(field_name, {}).get("path", ""))
        if not manifest_path.is_absolute():
            manifest_path = PROJECT_ROOT / manifest_path
        _require(
            manifest_path.resolve() == expected_path.resolve(),
            f"manifest path mismatch for {field_name}",
            errors,
        )


def _validate_summary_consistency(raw_rows, case_rows, group_rows, errors):
    try:
        expected_case_rows = summarize_by_case(raw_rows)
        expected_group_rows = summarize_by_group(expected_case_rows)
    except (TypeError, ValueError) as exc:
        errors.append(f"failed to recompute summaries: {type(exc).__name__}: {exc}")
        return
    _require(
        _rows_equal(case_rows, expected_case_rows, SUMMARY_FIELDS),
        "case summary does not match recomputed raw summary",
        errors,
    )
    _require(
        _rows_equal(group_rows, expected_group_rows, GROUP_FIELDS),
        "group summary does not match recomputed case summary",
        errors,
    )


def validate_outputs(run_dir=None, report_json=None):
    run_root = Path(run_dir or DEFAULT_RUN_DIR)
    config_path = run_root / "config.json"
    manifest_path = run_root / "manifest.json"
    environment_path = run_root / "environment.json"
    raw_path = run_root / "raw.csv"
    case_path = run_root / "case_summary.csv"
    group_path = run_root / "group_summary.csv"

    errors = []
    required_files = [
        config_path,
        manifest_path,
        environment_path,
        raw_path,
        case_path,
        group_path,
    ]
    for path in required_files:
        _require(path.exists(), f"missing required file: {path}", errors)

    if errors:
        report = {"valid": False, "errors": errors}
    else:
        config = read_json(config_path)
        environment = read_json(environment_path)
        manifest = read_json(manifest_path)
        raw_rows = read_csv(raw_path)
        case_rows = read_csv(case_path)
        group_rows = read_csv(group_path)

        _validate_schema(raw_rows, RAW_FIELDS, "raw", errors)
        _validate_schema(case_rows, SUMMARY_FIELDS, "case-summary", errors)
        _validate_schema(group_rows, GROUP_FIELDS, "group-summary", errors)
        _validate_raw_rows(raw_rows, config, errors)
        _validate_summaries(case_rows, group_rows, config, errors)
        _validate_manifest(manifest, config, environment, run_root, errors)
        _validate_summary_consistency(raw_rows, case_rows, group_rows, errors)
        _require(
            manifest.get("row_counts", {}).get("raw") == len(raw_rows),
            "manifest raw row count does not match raw CSV",
            errors,
        )
        _require(
            manifest.get("row_counts", {}).get("case_summary") == len(case_rows),
            "manifest case-summary row count does not match case-summary CSV",
            errors,
        )
        _require(
            manifest.get("row_counts", {}).get("group_summary") == len(group_rows),
            "manifest group-summary row count does not match group-summary CSV",
            errors,
        )

        report = {
            "valid": not errors,
            "errors": errors,
            "run_dir": str(run_root),
            "row_counts": {
                "raw": len(raw_rows),
                "case_summary": len(case_rows),
                "group_summary": len(group_rows),
            },
        }

    output_path = Path(report_json or (run_root / "validation_report.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--report-json", type=Path, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    report = validate_outputs(run_dir=args.run_dir, report_json=args.report_json)
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
