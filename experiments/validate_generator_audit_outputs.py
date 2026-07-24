"""Validate generated coverage-audit outputs before thesis use."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

from audit_generator_coverage import FIELDS, SUMMARY_FIELDS, summarize_audit_rows  # noqa: E402


DEFAULT_RUN_DIR = PROJECT_ROOT / "results" / "runs" / "week8_generator_audit_dry_run"


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


def _require(condition, message, errors):
    if not condition:
        errors.append(message)


def _parse_float(value, field, errors, allow_empty=False):
    if value in {"", None}:
        if allow_empty:
            return None
        errors.append(f"{field} is empty")
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{field} is not numeric: {value}")
        return None


def _stringify(value):
    if value is None:
        return ""
    return str(value)


def _rows_equal(left_rows, right_rows, fields):
    if len(left_rows) != len(right_rows):
        return False
    normalized_left = [
        {field: _stringify(row.get(field, "")) for field in fields}
        for row in left_rows
    ]
    normalized_right = [
        {field: _stringify(row.get(field, "")) for field in fields}
        for row in right_rows
    ]
    sort_key = lambda row: json.dumps(row, sort_keys=True)
    return sorted(normalized_left, key=sort_key) == sorted(
        normalized_right,
        key=sort_key,
    )


def _expected_audit_row_count(config):
    randomized_families = {
        "incremental_valid",
        "random_invalid",
        "mutation_based_invalid",
    }
    total = 0
    for family in config["families"]:
        repetitions = (
            config["randomized_repetitions"]
            if family in randomized_families
            else 1
        )
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


def _validate_manifest(manifest, config, run_root, errors):
    _require(
        manifest.get("run_id") == config.get("run_id"),
        "run_id mismatch between audit config and manifest",
        errors,
    )
    expected_labels = {
        "audit_config_json",
        "coverage_audit_csv",
        "coverage_summary_csv",
    }
    missing_labels = expected_labels - set(manifest.get("files", {}))
    _require(
        not missing_labels,
        f"audit manifest missing file entries: {sorted(missing_labels)}",
        errors,
    )
    expected_paths = {
        "audit_config_json": run_root / "audit_config.json",
        "coverage_audit_csv": run_root / "coverage_audit.csv",
        "coverage_summary_csv": run_root / "coverage_summary.csv",
    }
    for label, expected_path in expected_paths.items():
        file_info = manifest.get("files", {}).get(label, {})
        path = Path(file_info.get("path", ""))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        _require(
            path.resolve() == expected_path.resolve(),
            f"audit manifest path mismatch for {label}",
            errors,
        )
        if not path.exists():
            errors.append(f"audit manifest file is missing: {label} -> {path}")
            continue
        _require(
            file_sha256(path) == file_info.get("sha256"),
            f"audit manifest hash mismatch for {label}",
            errors,
        )


def _validate_audit_rows(rows, config, errors):
    expected_rows = _expected_audit_row_count(config)
    _require(
        len(rows) == expected_rows,
        f"coverage audit row count {len(rows)} != expected {expected_rows}",
        errors,
    )
    expected_families = set(config["families"])
    expected_sizes = set(str(size) for size in config["sizes"])
    _require(
        {row["family"] for row in rows} == expected_families,
        "coverage audit families do not match config",
        errors,
    )
    _require(
        {row["n"] for row in rows} == expected_sizes,
        "coverage audit sizes do not match config",
        errors,
    )
    for row in rows:
        _require(len(row["sequence_hash"]) == 64, "invalid sequence_hash length", errors)
        for field in [
            "parented_interval_ratio",
            "containment_pair_density",
            "crossing_pair_density",
        ]:
            value = _parse_float(row[field], field, errors, allow_empty=True)
            if value is not None:
                _require(0.0 <= value <= 1.0, f"{field} out of range: {value}", errors)


def _validate_summary_rows(summary_rows, config, errors):
    expected_rows = len(config["families"]) * len(config["sizes"])
    _require(
        len(summary_rows) == expected_rows,
        f"coverage summary row count {len(summary_rows)} != expected {expected_rows}",
        errors,
    )
    for row in summary_rows:
        for field in [
            "duplicate_case_rate",
            "avg_crossing_pair_density",
            "min_containment_pair_density",
            "median_containment_pair_density",
            "max_containment_pair_density",
            "min_crossing_pair_density",
            "median_crossing_pair_density",
            "max_crossing_pair_density",
        ]:
            value = _parse_float(row[field], field, errors, allow_empty=True)
            if value is not None:
                _require(0.0 <= value <= 1.0, f"{field} out of range: {value}", errors)


def validate_audit_outputs(run_dir=None, report_json=None):
    run_root = Path(run_dir or DEFAULT_RUN_DIR)
    config_path = run_root / "audit_config.json"
    manifest_path = run_root / "audit_manifest.json"
    audit_path = run_root / "coverage_audit.csv"
    summary_path = run_root / "coverage_summary.csv"

    errors = []
    for path in [config_path, manifest_path, audit_path, summary_path]:
        _require(path.exists(), f"missing required file: {path}", errors)

    if errors:
        report = {"valid": False, "errors": errors}
    else:
        config = read_json(config_path)
        manifest = read_json(manifest_path)
        audit_rows = read_csv(audit_path)
        summary_rows = read_csv(summary_path)

        _validate_schema(audit_rows, FIELDS, "coverage-audit", errors)
        _validate_schema(summary_rows, SUMMARY_FIELDS, "coverage-summary", errors)
        _validate_manifest(manifest, config, run_root, errors)
        _validate_audit_rows(audit_rows, config, errors)
        _validate_summary_rows(summary_rows, config, errors)
        try:
            expected_summary_rows = summarize_audit_rows(audit_rows)
        except (TypeError, ValueError) as exc:
            errors.append(
                f"failed to recompute audit summary: {type(exc).__name__}: {exc}"
            )
        else:
            _require(
                _rows_equal(summary_rows, expected_summary_rows, SUMMARY_FIELDS),
                "coverage summary does not match recomputed audit summary",
                errors,
            )
        _require(
            manifest.get("row_counts", {}).get("coverage_audit") == len(audit_rows),
            "audit manifest row count does not match coverage audit CSV",
            errors,
        )
        _require(
            manifest.get("row_counts", {}).get("coverage_summary")
            == len(summary_rows),
            "audit manifest row count does not match coverage summary CSV",
            errors,
        )

        report = {
            "valid": not errors,
            "errors": errors,
            "run_dir": str(run_root),
            "row_counts": {
                "coverage_audit": len(audit_rows),
                "coverage_summary": len(summary_rows),
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
    report = validate_audit_outputs(args.run_dir, report_json=args.report_json)
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
