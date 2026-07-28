"""Validate Week 10 timing-contamination outputs before analysis."""

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from paper_execution_policy import PAPER_EXECUTION_POLICIES  # noqa: E402
from generators import (  # noqa: E402
    INCREMENTAL_VALID,
    generate_sequence,
    make_case_id,
)
from oracle import oracle  # noqa: E402
from run_week10_timing_contamination import (  # noqa: E402
    CASE_SUMMARY_FIELDS,
    EXECUTION_MODES,
    GROUP_SUMMARY_FIELDS,
    RAW_FIELDS,
    STRUCTURAL_FIELDS,
    WEEK10_FAMILIES,
    expected_case_count,
    mode_order_for_round,
    summarize_by_case,
    summarize_by_group,
)
from run_week7_pilot import file_sha256  # noqa: E402
from stats import structure_profile  # noqa: E402


DEFAULT_RUN_DIR = (
    PROJECT_ROOT / "results" / "runs" / "week10_contamination_smoke"
)


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require(condition, message, errors):
    if not condition:
        errors.append(message)


def _parse_int(value, field, errors, allow_empty=False):
    if value in {"", None}:
        if allow_empty:
            return None
        errors.append(f"{field} is empty")
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        errors.append(f"{field} is not an integer: {value}")
        return None


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


def _parse_bool(value, field, errors):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "false"}:
            return normalized == "true"
    errors.append(f"{field} is not a boolean: {value}")
    return None


def _validate_schema(rows, expected_fields, label, errors):
    if not rows:
        errors.append(f"{label} CSV is empty")
        return False
    actual = set(rows[0])
    missing = set(expected_fields) - actual
    extra = actual - set(expected_fields)
    _require(
        not missing,
        f"{label} CSV missing fields: {sorted(missing, key=str)}",
        errors,
    )
    _require(
        not extra,
        f"{label} CSV has unexpected fields: {sorted(extra, key=str)}",
        errors,
    )
    return not missing and not extra


def _validate_config_data(config, errors):
    _require(
        isinstance(config.get("run_id"), str) and bool(config.get("run_id")),
        "config run_id must be a non-empty string",
        errors,
    )
    _require(
        config.get("families") == WEEK10_FAMILIES,
        "config families do not match the frozen Week 10 families",
        errors,
    )
    sizes = config.get("sizes")
    _require(
        isinstance(sizes, list)
        and bool(sizes)
        and all(
            isinstance(n, int) and not isinstance(n, bool) and n > 0
            for n in sizes
        ),
        "config sizes must be positive integers",
        errors,
    )
    _require(
        config.get("execution_modes") == EXECUTION_MODES,
        "config execution modes do not match the fixed registry",
        errors,
    )
    for field, minimum in (
        ("randomized_cases", 1),
        ("warmup_runs", 0),
        ("measured_runs", 1),
    ):
        value = config.get(field)
        _require(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value >= minimum,
            f"config {field} is invalid",
            errors,
        )
    for field in ("seed", "mode_order_seed", "case_order_seed"):
        value = config.get(field)
        _require(
            isinstance(value, int) and not isinstance(value, bool),
            f"config {field} must be an integer",
            errors,
        )
    return not errors


def _config_view(config):
    """Build the field subset needed by expected_case_count()."""

    class ConfigView:
        pass

    view = ConfigView()
    view.families = config.get("families", [])
    view.sizes = config.get("sizes", [])
    view.randomized_cases = config.get("randomized_cases", 0)
    return view


def _sequence_sha256(sequence):
    payload = json.dumps(
        list(sequence),
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _rebuild_expected_cases(config, errors):
    """Recreate the frozen cases independently of the experiment outputs."""
    cases = []
    try:
        for family in config["families"]:
            repetitions = (
                config["randomized_cases"]
                if family == INCREMENTAL_VALID
                else 1
            )
            for requested_n in config["sizes"]:
                for index in range(1, repetitions + 1):
                    case_seed = (
                        config["seed"] + requested_n * 1000 + index
                        if family == INCREMENTAL_VALID
                        else None
                    )
                    sequence = generate_sequence(
                        family,
                        requested_n,
                        seed=case_seed,
                    )
                    oracle_result = oracle(sequence)
                    if not oracle_result["valid"]:
                        errors.append(
                            "reconstructed Week 10 case is not oracle-valid: "
                            f"family={family}, n={requested_n}, "
                            f"reason={oracle_result['reason']}"
                        )
                        continue
                    profile = structure_profile(
                        sequence,
                        oracle_result=oracle_result,
                    )
                    cases.append(
                        {
                            "case_id": make_case_id(
                                family,
                                len(sequence),
                                index,
                            ),
                            "case_index": len(cases),
                            "family": family,
                            "n": len(sequence),
                            "seed": case_seed,
                            "sequence_sha256": _sequence_sha256(sequence),
                            "oracle_valid": True,
                            **{
                                field: profile[field]
                                for field in STRUCTURAL_FIELDS
                            },
                        }
                    )
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        errors.append(
            "failed to reconstruct frozen Week 10 cases: "
            f"{type(exc).__name__}: {exc}"
        )
        return {}

    shuffled = list(cases)
    random.Random(config["case_order_seed"]).shuffle(shuffled)
    positions = {
        case["case_id"]: position
        for position, case in enumerate(shuffled, start=1)
    }
    for case in cases:
        case["case_execution_position"] = positions[case["case_id"]]
    return {case["case_id"]: case for case in cases}


def _validate_expected_case_field(row, expected, field, errors):
    actual = row[field]
    expected_text = _stringify(expected[field])
    _require(
        actual == expected_text,
        f"case provenance mismatch for {field}: "
        f"{row['case_id']} -> {actual!r}, expected {expected_text!r}",
        errors,
    )


def _validate_raw_rows(raw_rows, config, expected_cases_by_id, errors):
    expected_cases = expected_case_count(_config_view(config))
    measured_runs = _parse_int(
        config.get("measured_runs"),
        "config measured_runs",
        errors,
    )
    if measured_runs is None:
        return
    expected_raw = expected_cases * len(EXECUTION_MODES) * measured_runs
    _require(
        len(raw_rows) == expected_raw,
        f"raw row count {len(raw_rows)} != expected {expected_raw}",
        errors,
    )

    configured_modes = config.get("execution_modes")
    _require(
        configured_modes == EXECUTION_MODES,
        "config execution modes do not match the fixed registry",
        errors,
    )
    _require(
        {row["execution_mode"] for row in raw_rows} == set(EXECUTION_MODES),
        "raw rows do not contain exactly the five execution modes",
        errors,
    )

    expected_run_indices = set(range(1, measured_runs + 1))
    expected_positions = set(range(1, len(EXECUTION_MODES) + 1))
    expected_case_positions = set(range(1, expected_cases + 1))
    case_positions = {}
    position_owners = {}
    case_indices = {}
    index_owners = {}
    case_metadata = {}
    grouped_rounds = {}
    mode_position_counts = {}
    observed_case_ids = set()

    for row in raw_rows:
        case_id = row["case_id"]
        observed_case_ids.add(case_id)
        expected_case = expected_cases_by_id.get(case_id)
        if expected_case is None:
            errors.append(f"unexpected raw case_id: {case_id}")
        else:
            for field in (
                "case_index",
                "family",
                "n",
                "seed",
                "sequence_sha256",
                "case_execution_position",
                *STRUCTURAL_FIELDS,
                "oracle_valid",
            ):
                _validate_expected_case_field(
                    row,
                    expected_case,
                    field,
                    errors,
                )

        mode = row["execution_mode"]
        policy = PAPER_EXECUTION_POLICIES.get(mode)
        if policy is None:
            errors.append(f"unknown execution mode: {mode}")
            continue

        for field, expected in (
            ("record_trace", policy.record_trace),
            ("count_operations", policy.count_operations),
            (
                "validate_backend_commits",
                policy.validate_backend_commits,
            ),
        ):
            actual = _parse_bool(row[field], field, errors)
            _require(
                actual is None or actual == expected,
                f"{field} does not match mode {mode}",
                errors,
            )

        oracle_valid = _parse_bool(row["oracle_valid"], "oracle_valid", errors)
        output_correct = _parse_bool(
            row["output_correct"],
            "output_correct",
            errors,
        )
        audit_passed = _parse_bool(row["audit_passed"], "audit_passed", errors)
        _require(
            oracle_valid is True,
            f"paper timing row is not oracle-valid: {row['case_id']}",
            errors,
        )
        _require(
            output_correct is True,
            f"paper timing row has wrong output: {row['case_id']}, {mode}",
            errors,
        )
        _require(
            audit_passed is True,
            f"paper timing row failed checked audit: {row['case_id']}",
            errors,
        )
        _require(
            not row["error"],
            f"paper timing row contains error: {row['case_id']}, {mode}",
            errors,
        )

        n = _parse_int(row["n"], "n", errors)
        case_index = _parse_int(row["case_index"], "case_index", errors)
        case_position = _parse_int(
            row["case_execution_position"],
            "case_execution_position",
            errors,
        )
        run_index = _parse_int(row["run_index"], "run_index", errors)
        measured_round = _parse_int(
            row["measured_round"],
            "measured_round",
            errors,
        )
        mode_position = _parse_int(
            row["mode_position"],
            "mode_position",
            errors,
        )
        time_ns = _parse_int(row["time_ns"], "time_ns", errors)
        _require(n is None or n > 0, f"n must be positive: {row['n']}", errors)
        _require(
            row["run_id"] == config["run_id"],
            f"raw run_id mismatch: {row['case_id']}",
            errors,
        )
        _require(
            row["family"] in config["families"],
            f"raw family is not configured: {row['family']}",
            errors,
        )
        _require(
            n in set(config["sizes"]),
            f"raw size is not configured: {row['n']}",
            errors,
        )
        _require(
            run_index in expected_run_indices,
            f"run_index out of range: {row['case_id']} -> {row['run_index']}",
            errors,
        )
        _require(
            measured_round == run_index,
            f"measured_round must equal run_index: {row['case_id']}",
            errors,
        )
        _require(
            mode_position in expected_positions,
            f"mode_position out of range: {row['case_id']} -> "
            f"{row['mode_position']}",
            errors,
        )
        _require(
            time_ns is None or time_ns >= 0,
            f"time_ns must be non-negative: {row['case_id']}",
            errors,
        )
        for field in (
            "upper_interval_count",
            "lower_interval_count",
            "total_interval_count",
            "upper_root_count",
            "lower_root_count",
            "nesting_count",
            "max_depth",
        ):
            value = _parse_int(row[field], field, errors)
            _require(
                value is None or value >= 0,
                f"{field} must be non-negative: {row['case_id']}",
                errors,
            )
        density = _parse_float(
            row["nesting_density"],
            "nesting_density",
            errors,
        )
        _require(
            density is None or 0 <= density <= 1,
            f"nesting_density must be in [0, 1]: {row['case_id']}",
            errors,
        )

        if case_position is not None:
            known_position = case_positions.setdefault(
                row["case_id"],
                case_position,
            )
            _require(
                known_position == case_position,
                f"case position changed within {row['case_id']}",
                errors,
            )
            owner = position_owners.setdefault(
                case_position,
                row["case_id"],
            )
            _require(
                owner == row["case_id"],
                f"case position {case_position} has multiple owners",
                errors,
            )

        if case_index is not None:
            known_index = case_indices.setdefault(row["case_id"], case_index)
            _require(
                known_index == case_index,
                f"case_index changed within {row['case_id']}",
                errors,
            )
            owner = index_owners.setdefault(case_index, row["case_id"])
            _require(
                owner == row["case_id"],
                f"case_index {case_index} has multiple owners",
                errors,
            )

        metadata = tuple(
            row[field]
            for field in (
                "run_id",
                "case_index",
                "family",
                "n",
                "seed",
                "sequence_sha256",
                *STRUCTURAL_FIELDS,
                "oracle_valid",
                "audit_passed",
            )
        )
        known_metadata = case_metadata.setdefault(row["case_id"], metadata)
        _require(
            known_metadata == metadata,
            f"structural/case fields changed between modes: {row['case_id']}",
            errors,
        )
        sequence_hash = row["sequence_sha256"]
        _require(
            len(sequence_hash) == 64
            and all(
                character in "0123456789abcdef"
                for character in sequence_hash
            ),
            f"invalid sequence SHA-256: {row['case_id']}",
            errors,
        )

        grouped_rounds.setdefault(
            (row["case_id"], row["run_index"]),
            [],
        ).append(row)
        mode_position_counts.setdefault(
            (row["case_id"], mode),
            {},
        )[mode_position] = (
            mode_position_counts.setdefault(
                (row["case_id"], mode),
                {},
            ).get(mode_position, 0)
            + 1
        )

    _require(
        set(case_positions.values()) == expected_case_positions,
        "case_execution_position values must be exactly 1..case_count",
        errors,
    )
    _require(
        set(case_indices.values()) == set(range(expected_cases)),
        "case_index values must be exactly 0..case_count-1",
        errors,
    )

    for (case_id, run_index), rows in grouped_rounds.items():
        modes = [row["execution_mode"] for row in rows]
        round_number = _parse_int(run_index, "run_index", errors)
        parsed_positions = [
            _parse_int(row["mode_position"], "mode_position", errors)
            for row in rows
        ]
        positions = set(parsed_positions)
        _require(
            len(rows) == len(EXECUTION_MODES)
            and set(modes) == set(EXECUTION_MODES),
            f"{case_id} round {run_index} has missing/duplicate modes",
            errors,
        )
        _require(
            positions == expected_positions,
            f"{case_id} round {run_index} has incomplete mode positions",
            errors,
        )
        case_index = case_indices.get(case_id)
        if (
            case_index is not None
            and round_number is not None
            and all(position is not None for position in parsed_positions)
        ):
            expected_order = mode_order_for_round(
                EXECUTION_MODES,
                config["mode_order_seed"],
                case_index,
                round_number,
            )
            observed_order = [
                row["execution_mode"]
                for row in sorted(
                    rows,
                    key=lambda item: int(item["mode_position"]),
                )
            ]
            _require(
                observed_order == expected_order,
                f"{case_id} round {run_index} mode order does not match seed",
                errors,
            )

    for (case_id, mode), counts in mode_position_counts.items():
        observed = [counts.get(position, 0) for position in expected_positions]
        _require(
            max(observed) - min(observed) <= 1,
            f"mode positions are not cyclically balanced: {case_id}, {mode}",
            errors,
        )
    _require(
        len(case_metadata) == expected_cases,
        f"raw case count {len(case_metadata)} != expected {expected_cases}",
        errors,
    )
    _require(
        observed_case_ids == set(expected_cases_by_id),
        "raw case IDs do not match independently reconstructed cases",
        errors,
    )


def _validate_summary_values(case_rows, group_rows, config, errors):
    expected_cases = expected_case_count(_config_view(config))
    expected_case_rows = expected_cases * len(EXECUTION_MODES)
    expected_group_rows = (
        len(config.get("families", []))
        * len(config.get("sizes", []))
        * len(EXECUTION_MODES)
    )
    _require(
        len(case_rows) == expected_case_rows,
        f"case-summary row count {len(case_rows)} != expected "
        f"{expected_case_rows}",
        errors,
    )
    _require(
        len(group_rows) == expected_group_rows,
        f"group-summary row count {len(group_rows)} != expected "
        f"{expected_group_rows}",
        errors,
    )

    measured_runs = config.get("measured_runs")
    for row in case_rows:
        count = _parse_int(
            row["measured_run_count"],
            "measured_run_count",
            errors,
        )
        error_count = _parse_int(row["error_count"], "error_count", errors)
        all_correct = _parse_bool(row["all_correct"], "all_correct", errors)
        _require(
            count == measured_runs,
            f"incomplete case-summary runs: {row['case_id']}, "
            f"{row['execution_mode']}",
            errors,
        )
        _require(error_count == 0, "case summary contains errors", errors)
        _require(all_correct is True, "case summary is not all correct", errors)
        for field in (
            "median_time_ns",
            "q1_time_ns",
            "q3_time_ns",
            "iqr_time_ns",
            "mean_time_ns",
            "stdev_time_ns",
            "median_over_minimal_ratio",
        ):
            value = _parse_float(row[field], field, errors)
            _require(
                value is None or value >= 0,
                f"{field} must be non-negative",
                errors,
            )

    for row in group_rows:
        case_count = _parse_int(row["case_count"], "case_count", errors)
        error_count = _parse_int(
            row["total_error_count"],
            "total_error_count",
            errors,
        )
        all_correct = _parse_bool(
            row["all_cases_correct"],
            "all_cases_correct",
            errors,
        )
        expected_family_cases = (
            config["randomized_cases"]
            if row["family"] == "incremental_valid"
            else 1
        )
        _require(
            case_count == expected_family_cases,
            f"wrong group case_count: {row['family']}, n={row['n']}",
            errors,
        )
        _require(error_count == 0, "group summary contains errors", errors)
        _require(
            all_correct is True,
            "group summary is not all correct",
            errors,
        )
        for field in (
            "median_case_time_ns",
            "median_over_minimal_ratio",
        ):
            value = _parse_float(row[field], field, errors)
            _require(
                value is None or value >= 0,
                f"{field} must be non-negative",
                errors,
            )


def _stringify(value):
    return "" if value is None else str(value)


def _rows_equal(left_rows, right_rows, fields):
    if len(left_rows) != len(right_rows):
        return False
    left = [
        {field: _stringify(row.get(field, "")) for field in fields}
        for row in left_rows
    ]
    right = [
        {field: _stringify(row.get(field, "")) for field in fields}
        for row in right_rows
    ]
    key = lambda row: json.dumps(row, sort_keys=True)
    return sorted(left, key=key) == sorted(right, key=key)


def _validate_summary_consistency(raw_rows, case_rows, group_rows, errors):
    try:
        expected_case_rows = summarize_by_case(raw_rows)
        expected_group_rows = summarize_by_group(expected_case_rows)
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(
            "failed to recompute summaries: "
            f"{type(exc).__name__}: {exc}"
        )
        return
    _require(
        _rows_equal(case_rows, expected_case_rows, CASE_SUMMARY_FIELDS),
        "case summary does not match recomputed raw summary",
        errors,
    )
    _require(
        _rows_equal(group_rows, expected_group_rows, GROUP_SUMMARY_FIELDS),
        "group summary does not match recomputed case summary",
        errors,
    )


def _validate_manifest(manifest, config, environment, run_dir, errors):
    _require(
        manifest.get("run_id")
        == config.get("run_id")
        == environment.get("run_id"),
        "run_id mismatch across manifest/config/environment",
        errors,
    )
    _require(
        manifest.get("git_commit_sha") == environment.get("git_commit_sha"),
        "git commit mismatch across manifest/environment",
        errors,
    )
    _require(
        manifest.get("git_dirty") == environment.get("git_dirty"),
        "git dirty state mismatch across manifest/environment",
        errors,
    )
    _require(
        environment.get("config") == config,
        "environment/config snapshot mismatch",
        errors,
    )
    expected_files = {
        "raw_csv": run_dir / "raw.csv",
        "case_summary_csv": run_dir / "case_summary.csv",
        "group_summary_csv": run_dir / "group_summary.csv",
        "environment_json": run_dir / "environment.json",
        "config_json": run_dir / "config.json",
    }
    _require(
        set(manifest.get("files", {})) == set(expected_files),
        "manifest file labels do not match the Week 10 contract",
        errors,
    )
    for label, expected_path in expected_files.items():
        info = manifest.get("files", {}).get(label, {})
        if not isinstance(info, dict):
            errors.append(f"manifest file entry is not an object: {label}")
            continue
        path = Path(info.get("path", ""))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        _require(
            path.resolve() == expected_path.resolve(),
            f"manifest path mismatch for {label}",
            errors,
        )
        outputs = config.get("outputs", {})
        if not isinstance(outputs, dict):
            errors.append("config outputs must be an object")
            break
        configured_path = Path(outputs.get(label, ""))
        if not configured_path.is_absolute():
            configured_path = PROJECT_ROOT / configured_path
        _require(
            configured_path.resolve() == expected_path.resolve(),
            f"config output path mismatch for {label}",
            errors,
        )
        if not path.exists():
            errors.append(f"manifest file is missing: {label}")
            continue
        _require(
            file_sha256(path) == info.get("sha256"),
            f"manifest hash mismatch for {label}",
            errors,
        )


def _safe_read_json(path, label, errors):
    try:
        value = read_json(path)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError) as exc:
        errors.append(
            f"failed to read {label} JSON: {type(exc).__name__}: {exc}"
        )
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} JSON must contain an object")
        return None
    return value


def _safe_read_csv(path, label, errors):
    try:
        rows = read_csv(path)
    except (OSError, UnicodeError, csv.Error, TypeError) as exc:
        errors.append(
            f"failed to read {label} CSV: {type(exc).__name__}: {exc}"
        )
        return None
    if not isinstance(rows, list):
        errors.append(f"{label} CSV reader returned an invalid container")
        return None
    return rows


def validate_outputs(run_dir=None, report_json=None):
    """Validate one Week 10 run directory and write a JSON report."""
    root = Path(run_dir or DEFAULT_RUN_DIR)
    paths = {
        "config": root / "config.json",
        "manifest": root / "manifest.json",
        "environment": root / "environment.json",
        "raw": root / "raw.csv",
        "case": root / "case_summary.csv",
        "group": root / "group_summary.csv",
    }
    errors = []
    for label, path in paths.items():
        _require(path.exists(), f"missing required file: {label} -> {path}", errors)

    raw_rows = None
    case_rows = None
    group_rows = None
    if not errors:
        config = _safe_read_json(paths["config"], "config", errors)
        manifest = _safe_read_json(paths["manifest"], "manifest", errors)
        environment = _safe_read_json(
            paths["environment"],
            "environment",
            errors,
        )
        raw_rows = _safe_read_csv(paths["raw"], "raw", errors)
        case_rows = _safe_read_csv(paths["case"], "case-summary", errors)
        group_rows = _safe_read_csv(paths["group"], "group-summary", errors)

        raw_schema_valid = (
            raw_rows is not None
            and _validate_schema(raw_rows, RAW_FIELDS, "raw", errors)
        )
        case_schema_valid = (
            case_rows is not None
            and _validate_schema(
                case_rows,
                CASE_SUMMARY_FIELDS,
                "case-summary",
                errors,
            )
        )
        group_schema_valid = (
            group_rows is not None
            and _validate_schema(
                group_rows,
                GROUP_SUMMARY_FIELDS,
                "group-summary",
                errors,
            )
        )
        config_valid = False
        if config is not None:
            config_errors = []
            config_valid = _validate_config_data(config, config_errors)
            errors.extend(config_errors)

        expected_cases_by_id = {}
        if config_valid:
            expected_cases_by_id = _rebuild_expected_cases(config, errors)
        if config_valid and raw_schema_valid:
            _validate_raw_rows(
                raw_rows,
                config,
                expected_cases_by_id,
                errors,
            )
        if config_valid and case_schema_valid and group_schema_valid:
            _validate_summary_values(case_rows, group_rows, config, errors)
        if raw_schema_valid and case_schema_valid and group_schema_valid:
            _validate_summary_consistency(
                raw_rows,
                case_rows,
                group_rows,
                errors,
            )
        if (
            manifest is not None
            and config is not None
            and environment is not None
        ):
            try:
                _validate_manifest(
                    manifest,
                    config,
                    environment,
                    root,
                    errors,
                )
            except (AttributeError, OSError, TypeError, ValueError) as exc:
                errors.append(
                    "failed to validate manifest: "
                    f"{type(exc).__name__}: {exc}"
                )
        if manifest is not None and raw_rows is not None:
            row_counts = manifest.get("row_counts", {})
            if not isinstance(row_counts, dict):
                errors.append("manifest row_counts must be an object")
                row_counts = {}
            _require(
                row_counts.get("raw") == len(raw_rows),
                "manifest raw row count mismatch",
                errors,
            )
        if manifest is not None and case_rows is not None:
            row_counts = manifest.get("row_counts", {})
            if not isinstance(row_counts, dict):
                row_counts = {}
            _require(
                row_counts.get("case_summary") == len(case_rows),
                "manifest case-summary row count mismatch",
                errors,
            )
        if manifest is not None and group_rows is not None:
            row_counts = manifest.get("row_counts", {})
            if not isinstance(row_counts, dict):
                row_counts = {}
            _require(
                row_counts.get("group_summary") == len(group_rows),
                "manifest group-summary row count mismatch",
                errors,
            )

    report = {
        "valid": not errors,
        "errors": errors,
        "run_dir": str(root),
    }
    if (
        not errors
        and raw_rows is not None
        and case_rows is not None
        and group_rows is not None
    ):
        report["row_counts"] = {
            "raw": len(raw_rows),
            "case_summary": len(case_rows),
            "group_summary": len(group_rows),
        }
    output = Path(report_json or (root / "validation_report.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--report-json", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = validate_outputs(args.run_dir, args.report_json)
    print(json.dumps(report, indent=2))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
