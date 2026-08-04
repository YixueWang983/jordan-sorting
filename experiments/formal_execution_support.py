"""Shared run-level support for formal sorting experiments."""

import csv
import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from run_week11_pilot import (
    capture_benchmark_environment,
    capture_load_status,
    capture_power_status,
    git_snapshot,
    require_clean_pushed_git,
    require_timing_ready_environment,
    validate_power_status,
    validate_timing_readiness_record,
)
from week11_execution_context import (
    Week11ExecutionContext,
    execution_context_to_dict,
    output_dir_for_execution,
    validate_execution_context,
    validate_execution_id,
)


@dataclass(frozen=True)
class FormalRunPaths:
    """Hold the fixed eight-file evidence contract for one execution."""

    run_dir: Path
    config_json: Path
    environment_json: Path
    raw_csv: Path
    case_summary_csv: Path
    group_summary_csv: Path
    case_audit_csv: Path
    manifest_json: Path
    validation_report_json: Path


def build_formal_run_paths(project_root, execution_id):
    validate_execution_id(execution_id)
    run_dir = Path(project_root) / "results" / "runs" / execution_id
    return FormalRunPaths(
        run_dir=run_dir,
        config_json=run_dir / "config.json",
        environment_json=run_dir / "environment.json",
        raw_csv=run_dir / "raw.csv",
        case_summary_csv=run_dir / "case_summary.csv",
        group_summary_csv=run_dir / "group_summary.csv",
        case_audit_csv=run_dir / "case_audit.csv",
        manifest_json=run_dir / "manifest.json",
        validation_report_json=run_dir / "validation_report.json",
    )


def require_unused_formal_output(paths):
    if not isinstance(paths, FormalRunPaths):
        raise TypeError("paths must be FormalRunPaths")
    if paths.run_dir.exists():
        raise RuntimeError("formal execution output is already in use")
    return paths


def build_formal_environment_record(
    project_root,
    *,
    execution_id,
    protocol_version,
    paper_execution_mode,
    audit_execution_mode,
    benchmark_environment=None,
    git_state=None,
):
    """Capture anonymous execution evidence for a formal timing run."""
    validate_execution_id(execution_id)
    root = Path(project_root)
    source = require_clean_pushed_git(git_state or git_snapshot(root))
    benchmark = benchmark_environment or capture_benchmark_environment()
    context = Week11ExecutionContext(
        execution_id=execution_id,
        output_dir=output_dir_for_execution(execution_id),
        benchmark_environment=benchmark,
        source_commit=source["head"],
    )
    validate_execution_context(context)
    record = {
        **execution_context_to_dict(context),
        "protocol_version": protocol_version,
        "captured_before_timing": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_dirty": False,
        "head_matches_origin_main": True,
        "available_disk_bytes": shutil.disk_usage(root).free,
        "perf_counter_resolution": time.get_clock_info(
            "perf_counter"
        ).resolution,
        "power_status": validate_power_status(capture_power_status()),
        "paper_execution_mode": paper_execution_mode,
        "audit_execution_mode": audit_execution_mode,
    }
    load_status = capture_load_status(benchmark["logical_cpu_count"])
    record["timing_readiness"] = require_timing_ready_environment(
        record,
        load_status,
        execution_stage="formal",
    )
    return record


def validate_formal_environment_record(
    environment,
    *,
    execution_id,
    protocol_version,
    paper_execution_mode,
    audit_execution_mode,
):
    if not isinstance(environment, dict):
        raise ValueError("environment must be a dictionary")
    if environment.get("execution_id") != execution_id:
        raise ValueError("environment execution_id changed")
    if environment.get("output_dir") != output_dir_for_execution(execution_id):
        raise ValueError("environment output_dir changed")
    if environment.get("protocol_version") != protocol_version:
        raise ValueError("environment protocol_version changed")
    if environment.get("paper_execution_mode") != paper_execution_mode:
        raise ValueError("environment paper execution mode changed")
    if environment.get("audit_execution_mode") != audit_execution_mode:
        raise ValueError("environment audit execution mode changed")
    if environment.get("captured_before_timing") is not True:
        raise ValueError("environment was not captured before timing")
    if environment.get("git_dirty") is not False:
        raise ValueError("environment records a dirty worktree")
    if environment.get("head_matches_origin_main") is not True:
        raise ValueError("environment source commit is not pushed")
    context = Week11ExecutionContext(
        execution_id=execution_id,
        output_dir=environment.get("output_dir"),
        benchmark_environment=environment.get("benchmark_environment"),
        source_commit=environment.get("source_commit"),
    )
    validate_execution_context(context)
    validate_timing_readiness_record(
        environment,
        environment.get("timing_readiness"),
        expected_stage="formal",
    )
    return environment


def reserve_formal_run_directory(paths):
    require_unused_formal_output(paths)
    try:
        paths.run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RuntimeError("formal execution output is already in use") from exc
    return paths


def write_json_exclusive(path, payload):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_json_object(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not verify JSON evidence: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON evidence must contain an object: {path}")
    return value


def write_csv_exclusive(path, fieldnames, rows):
    with Path(path).open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
