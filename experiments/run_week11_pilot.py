"""Preflight-only framework for the frozen Week 11 sorting pilot."""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from week11_experiment_gate_v2 import (  # noqa: E402
    WEEK11_EXPERIMENT_GATE,
    gate_to_dict,
    validate_week11_experiment_gate,
)


MACHINE_PREFLIGHT_DOCUMENT = Path(
    WEEK11_EXPERIMENT_GATE.machine_preflight_path
)
MACHINE_BASELINE_DOCUMENT = Path(
    WEEK11_EXPERIMENT_GATE.machine_baseline_path
)
MACHINE_IDENTITY_FIELDS = (
    "machine_name",
    "machine_model",
    "chip",
    "architecture",
    "os_name",
    "os_version",
    "os_build",
    "python_executable",
    "python_implementation",
    "python_version",
)
EVIDENCE_FILENAMES = (
    "raw.csv",
    "case_summary.csv",
    "group_summary.csv",
    "case_audit.csv",
    "config.json",
    "environment.json",
    "manifest.json",
    "validation_report.json",
)


@dataclass(frozen=True)
class Week11PilotPaths:
    """Hold the fixed output contract for one Week 11 gate."""

    run_dir: Path
    raw_csv: Path
    case_summary_csv: Path
    group_summary_csv: Path
    case_audit_csv: Path
    config_json: Path
    environment_json: Path
    manifest_json: Path
    validation_report_json: Path

    @property
    def evidence_paths(self):
        return tuple(getattr(self, field_name) for field_name in (
            "raw_csv",
            "case_summary_csv",
            "group_summary_csv",
            "case_audit_csv",
            "config_json",
            "environment_json",
            "manifest_json",
            "validation_report_json",
        ))


def build_pilot_paths(project_root=PROJECT_ROOT, gate=WEEK11_EXPERIMENT_GATE):
    """Resolve the frozen gate output directory under one project root."""
    validate_week11_experiment_gate(gate)
    root = Path(project_root)
    run_dir = root / gate.output_dir
    paths = Week11PilotPaths(
        run_dir=run_dir,
        raw_csv=run_dir / "raw.csv",
        case_summary_csv=run_dir / "case_summary.csv",
        group_summary_csv=run_dir / "group_summary.csv",
        case_audit_csv=run_dir / "case_audit.csv",
        config_json=run_dir / "config.json",
        environment_json=run_dir / "environment.json",
        manifest_json=run_dir / "manifest.json",
        validation_report_json=run_dir / "validation_report.json",
    )
    if tuple(path.name for path in paths.evidence_paths) != EVIDENCE_FILENAMES:
        raise RuntimeError("Week 11 evidence filenames changed")
    if any(path.parent != run_dir for path in paths.evidence_paths):
        raise RuntimeError("Week 11 evidence must be direct children of run_dir")
    return paths


def require_unused_output(paths):
    """Reject any pre-existing formal run directory or evidence file."""
    existing = [path for path in paths.evidence_paths if path.exists()]
    if paths.run_dir.exists() or existing:
        raise RuntimeError(
            "Week 11 frozen output is already in use: "
            f"run_dir={paths.run_dir}, existing={existing}"
        )
    return paths


def _git_output(project_root, *args):
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _remote_main_sha(project_root):
    """Query the real remote main ref without trusting a tracking ref."""
    output = _git_output(
        project_root,
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/heads/main",
    )
    lines = [line.split() for line in output.splitlines() if line.strip()]
    if len(lines) != 1 or len(lines[0]) != 2:
        raise RuntimeError("could not resolve exactly one remote main ref")
    sha, ref_name = lines[0]
    if ref_name != "refs/heads/main" or len(sha) not in {40, 64}:
        raise RuntimeError("origin main returned an invalid ref record")
    try:
        int(sha, 16)
    except ValueError as exc:
        raise RuntimeError("origin main returned a non-hex commit SHA") from exc
    return sha


def git_snapshot(project_root=PROJECT_ROOT):
    """Return the clean/pushed source state required by the formal runner."""
    root = Path(project_root)
    status = _git_output(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    head = _git_output(root, "rev-parse", "HEAD")
    origin_main = _remote_main_sha(root)
    return {
        "head": head,
        "origin_main": origin_main,
        "origin_main_source": "git_ls_remote",
        "git_clean": status == "",
        "head_pushed": head == origin_main,
    }


def require_clean_pushed_git(snapshot):
    """Reject a dirty or unpushed source state."""
    if snapshot.get("git_clean") is not True:
        raise RuntimeError("Week 11 preflight requires a clean worktree")
    if snapshot.get("head_pushed") is not True:
        raise RuntimeError("Week 11 preflight requires HEAD == origin/main")
    return snapshot


def build_config_record(
    paths,
    gate=WEEK11_EXPERIMENT_GATE,
    project_root=PROJECT_ROOT,
):
    """Build the config.json contract without writing formal evidence."""
    validate_week11_experiment_gate(gate)
    root = Path(project_root)
    record = gate_to_dict(gate)
    record["status"] = "ready_not_executed"
    record["outputs"] = {
        path.name: str(path.relative_to(root))
        if path.is_relative_to(root)
        else str(path)
        for path in paths.evidence_paths
    }
    return record


def _capture_command(command):
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {"success": False, "output": "unavailable"}
    return {
        "success": True,
        "output": completed.stdout.strip() or "unavailable",
    }


def _hardware_identity():
    """Capture non-sensitive Mac hardware fields for machine matching."""
    captured = _capture_command(
        ["system_profiler", "SPHardwareDataType", "-json"]
    )
    if not captured["success"]:
        return {
            "machine_name": "unavailable",
            "machine_model": "unavailable",
            "chip": "unavailable",
        }
    try:
        payload = json.loads(captured["output"])
        hardware = payload["SPHardwareDataType"][0]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return {
            "machine_name": "unavailable",
            "machine_model": "unavailable",
            "chip": "unavailable",
        }
    return {
        "machine_name": hardware.get("machine_name", "unavailable"),
        "machine_model": hardware.get("machine_model", "unavailable"),
        "chip": hardware.get("chip_type", "unavailable"),
    }


def capture_machine_identity():
    """Capture the stable fields compared with the frozen machine baseline."""
    hardware = _hardware_identity()
    build = _capture_command(["sw_vers", "-buildVersion"])
    os_name = "macOS" if platform.system() == "Darwin" else platform.system()
    return {
        **hardware,
        "architecture": platform.machine(),
        "os_name": os_name,
        "os_version": platform.mac_ver()[0] or platform.release(),
        "os_build": build["output"],
        "python_executable": sys.executable,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }


def _sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_verified_machine_baseline(
    project_root,
    baseline_path,
    expected_sha256,
):
    """Load one machine baseline only when its bytes match a frozen hash."""
    path = Path(project_root) / baseline_path
    try:
        actual_sha256 = _sha256_file(path)
    except FileNotFoundError as exc:
        raise RuntimeError("Week 11 machine baseline is missing") from exc
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            "Week 11 machine baseline SHA-256 does not match the gate"
        )
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Week 11 machine baseline is invalid JSON") from exc
    if not isinstance(baseline, dict):
        raise RuntimeError("Week 11 machine baseline must be an object")
    missing = [field for field in MACHINE_IDENTITY_FIELDS if field not in baseline]
    if missing:
        raise RuntimeError(
            f"Week 11 machine baseline is missing fields: {missing}"
        )
    return baseline


def load_machine_baseline(
    project_root=PROJECT_ROOT,
    gate=WEEK11_EXPERIMENT_GATE,
):
    """Load the baseline cryptographically bound to the active gate."""
    validate_week11_experiment_gate(gate)
    return load_verified_machine_baseline(
        project_root,
        gate.machine_baseline_path,
        gate.machine_baseline_sha256,
    )


def machine_identity_mismatches(baseline, actual):
    """Return every frozen identity field that differs from this machine."""
    return {
        field: {"expected": baseline[field], "actual": actual.get(field)}
        for field in MACHINE_IDENTITY_FIELDS
        if actual.get(field) != baseline[field]
    }


def build_environment_record(
    git_state,
    gate=WEEK11_EXPERIMENT_GATE,
    project_root=PROJECT_ROOT,
    machine_identity=None,
):
    """Build the environment.json contract before any future timing."""
    validate_week11_experiment_gate(gate)
    require_clean_pushed_git(git_state)
    identity = machine_identity or capture_machine_identity()
    power = _capture_command(["pmset", "-g", "batt"])
    load = _capture_command(["uptime"])
    return {
        "run_id": gate.run_id,
        "gate_version": gate.gate_version,
        "machine_identity_id": gate.machine_identity_id,
        "machine_baseline_path": gate.machine_baseline_path,
        "machine_baseline_sha256": gate.machine_baseline_sha256,
        "captured_before_timing": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_state["head"],
        "git_dirty": False,
        "head_matches_origin_main": True,
        **identity,
        "python_runtime": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "available_disk_bytes": shutil.disk_usage(project_root).free,
        "perf_counter_resolution": time.get_clock_info(
            "perf_counter"
        ).resolution,
        "power_command_success": power["success"],
        "power_snapshot": power["output"],
        "load_command_success": load["success"],
        "load_snapshot": load["output"],
        "paper_execution_mode": gate.paper_execution_mode,
        "audit_execution_mode": gate.audit_execution_mode,
    }


def _write_json_exclusive(path, payload):
    """Create one JSON evidence file without permitting replacement."""
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not verify JSON evidence: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON evidence must contain an object: {path}")
    return value


def initialize_evidence_directory(
    paths,
    config_record,
    environment_record,
    gate=WEEK11_EXPERIMENT_GATE,
):
    """Atomically reserve a run directory and prewrite timing evidence."""
    validate_week11_experiment_gate(gate)
    require_unused_output(paths)
    expected_binding = {
        "run_id": gate.run_id,
        "gate_version": gate.gate_version,
        "machine_identity_id": gate.machine_identity_id,
        "machine_baseline_path": gate.machine_baseline_path,
        "machine_baseline_sha256": gate.machine_baseline_sha256,
    }
    for field, expected in expected_binding.items():
        if config_record.get(field) != expected:
            raise ValueError(f"config {field} does not match the gate")
        if environment_record.get(field) != expected:
            raise ValueError(f"environment {field} does not match the gate")
    if environment_record.get("captured_before_timing") is not True:
        raise ValueError("environment must be captured before timing")
    try:
        paths.run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RuntimeError("Week 11 frozen output is already in use") from exc

    # Deliberately leave partial evidence in place if a later write fails.
    _write_json_exclusive(paths.config_json, config_record)
    _write_json_exclusive(paths.environment_json, environment_record)

    if _read_json_object(paths.config_json) != config_record:
        raise RuntimeError("config.json verification failed")
    if _read_json_object(paths.environment_json) != environment_record:
        raise RuntimeError("environment.json verification failed")
    return {
        "status": "evidence_initialized_before_timing",
        "run_dir": str(paths.run_dir),
        "config_json": str(paths.config_json),
        "environment_json": str(paths.environment_json),
    }


def initialize_formal_evidence(
    project_root=PROJECT_ROOT,
    gate=WEEK11_EXPERIMENT_GATE,
):
    """Perform the mandatory evidence prewrite for a future formal run."""
    validate_week11_experiment_gate(gate)
    root = Path(project_root)
    paths = require_unused_output(build_pilot_paths(root, gate))
    if not (root / gate.machine_preflight_path).is_file():
        raise RuntimeError("Week 11 machine preflight document is missing")

    baseline = load_machine_baseline(root, gate)
    identity = capture_machine_identity()
    mismatches = machine_identity_mismatches(baseline, identity)
    if mismatches:
        raise RuntimeError(
            f"current machine does not match the Week 11 baseline: {mismatches}"
        )

    source = require_clean_pushed_git(git_snapshot(root))
    config = build_config_record(paths, gate, project_root=root)
    environment = build_environment_record(
        source,
        gate,
        project_root=root,
        machine_identity=identity,
    )
    return initialize_evidence_directory(paths, config, environment)


def run_preflight(
    project_root=PROJECT_ROOT,
    gate=WEEK11_EXPERIMENT_GATE,
):
    """Validate Day 2 framework readiness without creating any output."""
    validate_week11_experiment_gate(gate)
    root = Path(project_root)
    paths = require_unused_output(build_pilot_paths(root, gate))
    machine_document = root / gate.machine_preflight_path
    if not machine_document.is_file():
        raise RuntimeError("Week 11 machine preflight document is missing")
    baseline = load_machine_baseline(root, gate)
    identity = capture_machine_identity()
    mismatches = machine_identity_mismatches(baseline, identity)
    source = require_clean_pushed_git(git_snapshot(root))
    config = build_config_record(paths, gate, project_root=root)
    environment = build_environment_record(
        source,
        gate,
        project_root=root,
        machine_identity=identity,
    )
    return {
        "status": (
            "ready_not_executed" if not mismatches
            else "blocked_machine_mismatch"
        ),
        "gate_valid": True,
        "machine_preflight_document_present": True,
        "machine_baseline_present": True,
        "machine_identity_matches_baseline": not mismatches,
        "machine_identity_mismatches": mismatches,
        "git_clean": source["git_clean"],
        "head_pushed": source["head_pushed"],
        "head": source["head"],
        "origin_main": source["origin_main"],
        "run_id": gate.run_id,
        "output_dir": str(paths.run_dir),
        "output_directory_unused": True,
        "case_count": gate.case_count,
        "expected_raw_rows": gate.raw_row_count,
        "expected_case_summary_rows": gate.case_summary_row_count,
        "expected_group_summary_rows": gate.group_summary_row_count,
        "paper_execution_mode": gate.paper_execution_mode,
        "audit_execution_mode": gate.audit_execution_mode,
        "config_contract_ready": config["status"] == "ready_not_executed",
        "environment_contract_ready": (
            environment["captured_before_timing"] is True
            and environment["available_disk_bytes"] >= 0
            and "power_command_success" in environment
            and "load_command_success" in environment
        ),
        "formal_execution_enabled": False,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate the frozen framework without creating evidence",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.preflight_only:
        raise RuntimeError(
            "formal Week 11 execution is disabled until the Day 5 gate"
        )
    print(json.dumps(run_preflight(), indent=2))


if __name__ == "__main__":
    main()
