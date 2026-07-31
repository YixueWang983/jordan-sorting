"""Preflight-only framework for the frozen Week 11 sorting pilot."""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from week11_experiment_gate import (  # noqa: E402
    WEEK11_EXPERIMENT_GATE,
    gate_to_dict,
    validate_week11_experiment_gate,
)


MACHINE_PREFLIGHT_DOCUMENT = Path(
    "docs/analysis/week11_machine_preflight.md"
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


def git_snapshot(project_root=PROJECT_ROOT):
    """Return the clean/pushed source state required by the formal runner."""
    root = Path(project_root)
    status = _git_output(root, "status", "--porcelain")
    head = _git_output(root, "rev-parse", "HEAD")
    origin_main = _git_output(root, "rev-parse", "origin/main")
    return {
        "head": head,
        "origin_main": origin_main,
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
):
    """Build the config.json contract without writing formal evidence."""
    validate_week11_experiment_gate(gate)
    record = gate_to_dict(gate)
    record["status"] = "ready_not_executed"
    record["outputs"] = {
        path.name: str(path.relative_to(PROJECT_ROOT))
        if path.is_relative_to(PROJECT_ROOT)
        else str(path)
        for path in paths.evidence_paths
    }
    return record


def _safe_command_output(command):
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return completed.stdout.strip() or "unavailable"


def build_environment_record(
    git_state,
    gate=WEEK11_EXPERIMENT_GATE,
):
    """Build the environment.json contract before any future timing."""
    validate_week11_experiment_gate(gate)
    require_clean_pushed_git(git_state)
    return {
        "run_id": gate.run_id,
        "captured_before_timing": True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_state["head"],
        "git_dirty": False,
        "head_matches_origin_main": True,
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "perf_counter_resolution": time.get_clock_info(
            "perf_counter"
        ).resolution,
        "power_snapshot": _safe_command_output(["pmset", "-g", "batt"]),
        "load_snapshot": _safe_command_output(["uptime"]),
        "paper_execution_mode": gate.paper_execution_mode,
        "audit_execution_mode": gate.audit_execution_mode,
    }


def run_preflight(
    project_root=PROJECT_ROOT,
    gate=WEEK11_EXPERIMENT_GATE,
):
    """Validate Day 2 framework readiness without creating any output."""
    validate_week11_experiment_gate(gate)
    root = Path(project_root)
    paths = require_unused_output(build_pilot_paths(root, gate))
    machine_document = root / MACHINE_PREFLIGHT_DOCUMENT
    if not machine_document.is_file():
        raise RuntimeError("Week 11 machine preflight document is missing")
    source = require_clean_pushed_git(git_snapshot(root))
    config = build_config_record(paths, gate)
    return {
        "status": "ready_not_executed",
        "gate_valid": True,
        "machine_fixed": True,
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
