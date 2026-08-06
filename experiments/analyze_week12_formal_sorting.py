"""Analyze immutable Week 12 formal sorting evidence without rerunning timing."""

import argparse
import json
import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiments"))

import analyze_week11_pilot as shared  # noqa: E402
from formal_execution_support import file_sha256  # noqa: E402
from validate_week12_formal_sorting_outputs import validate_outputs  # noqa: E402
from week12_experiment_gate import (  # noqa: E402
    WEEK12_EXPERIMENT_GATE,
    validate_week12_experiment_gate,
)


PAPER_ALGORITHM_NAME = "simplified_jordan_paper_ordinary_list"
REFERENCE_ALGORITHM = "simplified_jordan_reference"
PYTHON_ALGORITHM = "python_sort"
ALGORITHMS = WEEK12_EXPERIMENT_GATE.algorithms
COMPARISONS = shared.COMPARISONS
HIGH_RELATIVE_IQR_THRESHOLD = shared.HIGH_RELATIVE_IQR_THRESHOLD
COUNTER_FIELDS = shared.COUNTER_FIELDS

CASE_RUNTIME_FIELDS = shared.CASE_RUNTIME_FIELDS
RUNTIME_GROUP_FIELDS = shared.RUNTIME_GROUP_FIELDS
RATIO_FIELDS = shared.RATIO_FIELDS
ELAPSED_FIELDS = shared.ELAPSED_FIELDS
STRUCTURE_RELATIONSHIP_FIELDS = shared.STRUCTURE_RELATIONSHIP_FIELDS
COUNTER_RELATIONSHIP_FIELDS = shared.COUNTER_RELATIONSHIP_FIELDS
CORRECTNESS_FIELDS = ("metric", "value")
TREND_FIELDS = (
    "n",
    "comparison",
    "week11_case_count",
    "week12_case_count",
    "week11_median_ratio",
    "week12_median_ratio",
    "week11_change_direction",
    "week12_change_direction",
    "change_direction_consistent",
    "same_side_of_one",
)
TREND_SUMMARY_FIELDS = (
    "comparison",
    "size_count",
    "ratio_spearman",
    "matching_transition_count",
    "transition_count",
    "same_side_of_one_count",
)


def read_csv(path):
    return shared.read_csv(path)


def read_json(path):
    return shared.read_json(path)


def _as_int(value, field_name):
    return shared._as_int(value, field_name)


def _as_float(value, field_name):
    return shared._as_float(value, field_name)


def load_case_runtime_records(case_rows):
    """Validate and normalize one Week 12 row per case and algorithm."""
    records = []
    seen = set()
    algorithms_by_case = {}
    metadata_by_case = {}
    for row in case_rows:
        case_id = row.get("case_id")
        algorithm = row.get("algorithm")
        key = (case_id, algorithm)
        if not case_id or algorithm not in ALGORITHMS:
            raise ValueError("case summary contains an unknown case or algorithm")
        if key in seen:
            raise ValueError(f"duplicate case summary row: {key}")
        seen.add(key)
        n = _as_int(row.get("n"), "n")
        measured_runs = _as_int(
            row.get("measured_run_count"),
            "measured_run_count",
        )
        median = _as_float(row.get("median_time_ns"), "median_time_ns")
        q1 = _as_float(row.get("q1_time_ns"), "q1_time_ns")
        q3 = _as_float(row.get("q3_time_ns"), "q3_time_ns")
        iqr = _as_float(row.get("iqr_time_ns"), "iqr_time_ns")
        mean = _as_float(row.get("mean_time_ns"), "mean_time_ns")
        stdev = _as_float(row.get("stdev_time_ns"), "stdev_time_ns")
        if measured_runs != WEEK12_EXPERIMENT_GATE.measured_runs:
            raise ValueError(f"unexpected measured run count for {case_id}")
        if not 0 < q1 <= median <= q3 or not math.isclose(
            iqr,
            q3 - q1,
            rel_tol=1e-12,
            abs_tol=1e-9,
        ):
            raise ValueError(f"invalid quartiles for {key}")
        if mean <= 0 or stdev < 0:
            raise ValueError(f"invalid mean or stdev for {key}")
        if row.get("all_correct") != "True" or row.get("error_count") != "0":
            raise ValueError(f"failed case summary cannot be analyzed: {key}")
        family = row.get("family")
        metadata = (family, n)
        previous = metadata_by_case.setdefault(case_id, metadata)
        if previous != metadata:
            raise ValueError(f"case metadata changed: {case_id}")
        algorithms_by_case.setdefault(case_id, set()).add(algorithm)
        records.append(
            {
                "case_id": case_id,
                "family": family,
                "n": n,
                "algorithm": algorithm,
                "measured_run_count": measured_runs,
                "median_time_ns": median,
                "q1_time_ns": q1,
                "q3_time_ns": q3,
                "iqr_time_ns": iqr,
                "relative_iqr": iqr / median,
                "mean_time_ns": mean,
                "stdev_time_ns": stdev,
            }
        )
    expected_algorithms = set(ALGORITHMS)
    for case_id, algorithms in algorithms_by_case.items():
        if algorithms != expected_algorithms:
            raise ValueError(f"case is missing algorithms: {case_id}")
    if len(algorithms_by_case) != WEEK12_EXPERIMENT_GATE.case_count:
        raise ValueError("case summary has an unexpected case count")
    return sorted(
        records,
        key=lambda row: (
            row["n"],
            row["family"],
            row["case_id"],
            ALGORITHMS.index(row["algorithm"]),
        ),
    )


def load_audit_records(audit_rows):
    records = {}
    for row in audit_rows:
        case_id = row.get("case_id")
        if not case_id or case_id in records:
            raise ValueError("duplicate or missing case audit ID")
        if row.get("audit_passed") != "True":
            raise ValueError(f"failed audit cannot be analyzed: {case_id}")
        record = {
            "case_id": case_id,
            "family": row.get("family"),
            "n": _as_int(row.get("n"), "n"),
            "nesting_density": _as_float(
                row.get("nesting_density"),
                "nesting_density",
            ),
            "max_depth": _as_float(row.get("max_depth"), "max_depth"),
            "containment_pair_density": _as_float(
                row.get("containment_pair_density"),
                "containment_pair_density",
            ),
        }
        for field in COUNTER_FIELDS:
            record[field] = _as_float(row.get(field), field)
        records[case_id] = record
    if len(records) != WEEK12_EXPERIMENT_GATE.case_count:
        raise ValueError("case audit has an unexpected case count")
    return records


def summarize_correctness(raw_rows, case_rows, audit_rows, validation_report):
    totals = {
        "raw_row_count": len(raw_rows),
        "raw_error_count": sum(bool(row.get("error")) for row in raw_rows),
        "raw_incorrect_output_count": sum(
            row.get("output_correct") != "True" for row in raw_rows
        ),
        "raw_oracle_invalid_count": sum(
            row.get("oracle_valid") != "True" for row in raw_rows
        ),
        "raw_failed_audit_count": sum(
            row.get("audit_passed") != "True" for row in raw_rows
        ),
        "case_summary_row_count": len(case_rows),
        "case_summary_incorrect_count": sum(
            row.get("all_correct") != "True" for row in case_rows
        ),
        "case_summary_error_count": sum(
            _as_int(row.get("error_count"), "error_count") for row in case_rows
        ),
        "case_audit_row_count": len(audit_rows),
        "case_audit_failed_count": sum(
            row.get("audit_passed") != "True" for row in audit_rows
        ),
        "validator_error_count": len(validation_report.get("errors", [])),
    }
    expected_counts = {
        "raw_row_count": WEEK12_EXPERIMENT_GATE.raw_row_count,
        "case_summary_row_count": WEEK12_EXPERIMENT_GATE.case_summary_row_count,
        "case_audit_row_count": WEEK12_EXPERIMENT_GATE.case_audit_row_count,
    }
    for field, expected in expected_counts.items():
        if totals[field] != expected:
            raise ValueError(f"unexpected correctness count: {field}")
    failure_metrics = (
        "raw_error_count",
        "raw_incorrect_output_count",
        "raw_oracle_invalid_count",
        "raw_failed_audit_count",
        "case_summary_incorrect_count",
        "case_summary_error_count",
        "case_audit_failed_count",
        "validator_error_count",
    )
    failure_fields = [
        field
        for field in failure_metrics
        if totals[field] != 0
    ]
    if failure_fields:
        raise ValueError(f"failed evidence cannot be analyzed: {failure_fields}")
    return [
        {"metric": metric, "value": value}
        for metric, value in totals.items()
    ]


def summarize_runtime(records, group_fields):
    return shared.summarize_runtime(records, group_fields)


def build_case_ratio_records(records):
    return shared.build_case_ratio_records(records)


def summarize_ratios(case_ratio_records):
    return shared.summarize_ratios(case_ratio_records)


def summarize_measured_elapsed(raw_rows):
    return shared.summarize_measured_elapsed(raw_rows)


def summarize_structure_relationships(case_records, audit_records):
    return shared.summarize_structure_relationships(case_records, audit_records)


def summarize_counter_relationships(case_records, audit_records):
    return shared.summarize_counter_relationships(case_records, audit_records)


def load_week11_size_ratios(project_root=PROJECT_ROOT):
    """Rebuild Week 11 ratios from the manifest-bound case summary only."""
    gate = validate_week12_experiment_gate()
    manifest_path = Path(project_root) / gate.source_pilot_manifest_path
    if file_sha256(manifest_path) != gate.source_pilot_manifest_sha256:
        raise ValueError("Week 11 source manifest hash changed")
    manifest = read_json(manifest_path)
    case_info = manifest.get("files", {}).get("case_summary")
    if not isinstance(case_info, dict):
        raise ValueError("Week 11 manifest lacks case-summary provenance")
    case_path = manifest_path.parent / case_info.get("path", "")
    if file_sha256(case_path) != case_info.get("sha256"):
        raise ValueError("Week 11 case-summary hash changed")
    records = shared.load_case_runtime_records(read_csv(case_path))
    return [
        row
        for row in shared.summarize_ratios(
            shared.build_case_ratio_records(records)
        )
        if row["scope"] == "size"
    ]


def _direction(current, previous):
    if previous is None:
        return "not_applicable"
    if math.isclose(current, previous, rel_tol=1e-12, abs_tol=1e-12):
        return "flat"
    return "up" if current > previous else "down"


def _side_of_one(value):
    if math.isclose(value, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        return "at_one"
    return "above_one" if value > 1.0 else "below_one"


def summarize_week11_week12_trends(week11_rows, week12_rows):
    """Compare within-run ratios only; never pool absolute runtimes."""
    week11 = {
        (int(row["n"]), row["comparison"]): row
        for row in week11_rows
    }
    week12 = {
        (int(row["n"]), row["comparison"]): row
        for row in week12_rows
        if row["scope"] == "size"
    }
    expected = {
        (n, comparison)
        for n in WEEK12_EXPERIMENT_GATE.sizes
        for comparison, _, _ in COMPARISONS
    }
    if set(week11) != expected or set(week12) != expected:
        raise ValueError("Week 11/12 size-ratio coverage changed")
    rows = []
    previous = {comparison: (None, None) for comparison, _, _ in COMPARISONS}
    for n in WEEK12_EXPERIMENT_GATE.sizes:
        for comparison, _, _ in COMPARISONS:
            left = week11[(n, comparison)]
            right = week12[(n, comparison)]
            left_value = float(left["median_ratio"])
            right_value = float(right["median_ratio"])
            left_direction = _direction(left_value, previous[comparison][0])
            right_direction = _direction(right_value, previous[comparison][1])
            rows.append(
                {
                    "n": n,
                    "comparison": comparison,
                    "week11_case_count": int(left["case_count"]),
                    "week12_case_count": int(right["case_count"]),
                    "week11_median_ratio": left_value,
                    "week12_median_ratio": right_value,
                    "week11_change_direction": left_direction,
                    "week12_change_direction": right_direction,
                    "change_direction_consistent": (
                        "" if left_direction == "not_applicable"
                        else left_direction == right_direction
                    ),
                    "same_side_of_one": (
                        _side_of_one(left_value) == _side_of_one(right_value)
                    ),
                }
            )
            previous[comparison] = (left_value, right_value)
    return rows


def summarize_trend_consistency(trend_rows):
    rows = []
    for comparison, _, _ in COMPARISONS:
        group = [row for row in trend_rows if row["comparison"] == comparison]
        transition_rows = [
            row
            for row in group
            if row["change_direction_consistent"] != ""
        ]
        rows.append(
            {
                "comparison": comparison,
                "size_count": len(group),
                "ratio_spearman": shared._spearman(
                    [row["week11_median_ratio"] for row in group],
                    [row["week12_median_ratio"] for row in group],
                ),
                "matching_transition_count": sum(
                    row["change_direction_consistent"] for row in transition_rows
                ),
                "transition_count": len(transition_rows),
                "same_side_of_one_count": sum(
                    row["same_side_of_one"] for row in group
                ),
            }
        )
    return rows


def write_runtime_figure(size_rows, path):
    series = {
        algorithm: {
            int(row["n"]): float(row["median_case_time_ns"])
            for row in size_rows
            if row["algorithm"] == algorithm
        }
        for algorithm in ALGORITHMS
    }
    shared._write_line_figure(
        series,
        path,
        title="Week 12 median case runtime by input size",
        subtitle="Equal-weighted case medians; logarithmic runtime axis",
        y_label="Median runtime",
        log_scale=True,
        value_kind="runtime_ns",
        canvas_width=1200,
        legend_width=400,
    )


def write_ratio_figure(ratio_rows, path):
    size_rows = [row for row in ratio_rows if row["scope"] == "size"]
    series = {
        comparison: {
            int(row["n"]): float(row["median_ratio"])
            for row in size_rows
            if row["comparison"] == comparison
        }
        for comparison, _, _ in COMPARISONS
    }
    shared._write_line_figure(
        series,
        path,
        title="Week 12 case-median runtime ratios by input size",
        subtitle="Per-case ratios; equal-weight aggregation; logarithmic ratio axis",
        y_label="Runtime ratio",
        log_scale=True,
        value_kind="ratio",
        baseline=1.0,
        canvas_width=1200,
        legend_width=400,
    )


def require_validated_run(run_dir, report_path):
    report = validate_outputs(run_dir, report_json=report_path)
    if not isinstance(report, dict) or report.get("valid") is not True:
        raise ValueError("Week 12 evidence failed live validation")
    return report


def _source_hashes(run_root):
    return {
        path.name: file_sha256(path)
        for path in run_root.iterdir()
        if path.is_file()
    }


def analyze_run(run_dir, output_dir, project_root=PROJECT_ROOT):
    run_path = Path(run_dir)
    run_root = run_path.resolve()
    output_root = Path(output_dir).resolve()
    if output_root == run_root or run_root in output_root.parents:
        raise ValueError("analysis output must be outside archived evidence")
    validate_week12_experiment_gate()
    source_hashes = _source_hashes(run_root)
    output_root.mkdir(parents=True, exist_ok=True)
    live_report_path = output_root / "week12_live_validation_report.json"
    validation_report = require_validated_run(run_path, live_report_path)
    manifest = read_json(run_root / "manifest.json")
    raw_rows = read_csv(run_root / "raw.csv")
    case_rows = read_csv(run_root / "case_summary.csv")
    audit_rows = read_csv(run_root / "case_audit.csv")
    case_records = load_case_runtime_records(case_rows)
    audit_records = load_audit_records(audit_rows)
    correctness_rows = summarize_correctness(
        raw_rows,
        case_rows,
        audit_rows,
        validation_report,
    )
    size_rows = summarize_runtime(case_records, ("n",))
    family_rows = summarize_runtime(case_records, ("family",))
    family_size_rows = summarize_runtime(case_records, ("family", "n"))
    ratio_rows = summarize_ratios(build_case_ratio_records(case_records))
    elapsed_rows = summarize_measured_elapsed(raw_rows)
    structure_rows = summarize_structure_relationships(
        case_records,
        audit_records,
    )
    counter_rows = summarize_counter_relationships(case_records, audit_records)
    trend_rows = summarize_week11_week12_trends(
        load_week11_size_ratios(project_root),
        ratio_rows,
    )
    trend_summary_rows = summarize_trend_consistency(trend_rows)

    artifacts = {
        "correctness": output_root / "week12_correctness_audit_totals.csv",
        "case_runtime": output_root / "week12_case_runtime_metrics.csv",
        "runtime_by_size": output_root / "week12_runtime_by_size.csv",
        "runtime_by_family": output_root / "week12_runtime_by_family.csv",
        "runtime_by_family_size": output_root / "week12_runtime_by_family_size.csv",
        "runtime_ratios": output_root / "week12_runtime_ratios.csv",
        "measured_elapsed": output_root / "week12_measured_elapsed.csv",
        "structure_relationships": output_root / "week12_structure_runtime_relationships.csv",
        "counter_relationships": output_root / "week12_paper_counter_runtime_relationships.csv",
        "week11_week12_trends": output_root / "week12_week11_ratio_trends.csv",
        "trend_summary": output_root / "week12_week11_trend_summary.csv",
        "runtime_figure": output_root / "week12_runtime_by_size.svg",
        "ratio_figure": output_root / "week12_runtime_ratio_by_size.svg",
        "summary": output_root / "week12_analysis_summary.json",
        "live_validation": live_report_path,
    }
    shared.write_csv(correctness_rows, artifacts["correctness"], CORRECTNESS_FIELDS)
    shared.write_csv(case_records, artifacts["case_runtime"], CASE_RUNTIME_FIELDS)
    shared.write_csv(size_rows, artifacts["runtime_by_size"], RUNTIME_GROUP_FIELDS)
    shared.write_csv(family_rows, artifacts["runtime_by_family"], RUNTIME_GROUP_FIELDS)
    shared.write_csv(
        family_size_rows,
        artifacts["runtime_by_family_size"],
        RUNTIME_GROUP_FIELDS,
    )
    shared.write_csv(ratio_rows, artifacts["runtime_ratios"], RATIO_FIELDS)
    shared.write_csv(elapsed_rows, artifacts["measured_elapsed"], ELAPSED_FIELDS)
    shared.write_csv(
        structure_rows,
        artifacts["structure_relationships"],
        STRUCTURE_RELATIONSHIP_FIELDS,
    )
    shared.write_csv(
        counter_rows,
        artifacts["counter_relationships"],
        COUNTER_RELATIONSHIP_FIELDS,
    )
    shared.write_csv(trend_rows, artifacts["week11_week12_trends"], TREND_FIELDS)
    shared.write_csv(
        trend_summary_rows,
        artifacts["trend_summary"],
        TREND_SUMMARY_FIELDS,
    )
    write_runtime_figure(size_rows, artifacts["runtime_figure"])
    write_ratio_figure(ratio_rows, artifacts["ratio_figure"])

    overall_ratios = {
        row["comparison"]: row["median_ratio"]
        for row in ratio_rows
        if row["scope"] == "overall"
    }
    high_variability = [
        record
        for record in case_records
        if record["relative_iqr"] >= HIGH_RELATIVE_IQR_THRESHOLD
    ]
    correctness = {row["metric"]: row["value"] for row in correctness_rows}
    summary = {
        "source_run": str(run_path),
        "source_commit": manifest["source_commit"],
        "validation_valid": validation_report["valid"],
        "row_counts": validation_report["row_counts"],
        "correctness": correctness,
        "case_runtime_rows": len(case_records),
        "runtime_by_size_rows": len(size_rows),
        "runtime_by_family_rows": len(family_rows),
        "runtime_by_family_size_rows": len(family_size_rows),
        "ratio_rows": len(ratio_rows),
        "structure_relationship_rows": len(structure_rows),
        "counter_relationship_rows": len(counter_rows),
        "week11_week12_trend_rows": len(trend_rows),
        "high_relative_iqr_threshold": HIGH_RELATIVE_IQR_THRESHOLD,
        "high_relative_iqr_rows": len(high_variability),
        "maximum_relative_iqr": max(
            record["relative_iqr"] for record in case_records
        ),
        "overall_case_median_ratios": overall_ratios,
        "measured_call_total_seconds": elapsed_rows[-1][
            "measured_call_total_seconds"
        ],
        "pipeline_wall_clock_seconds": (
            int(manifest["experiment_elapsed_ns"]) / 1_000_000_000
        ),
        "trend_consistency": {
            row["comparison"]: {
                field: row[field]
                for field in TREND_SUMMARY_FIELDS
                if field != "comparison"
            }
            for row in trend_summary_rows
        },
        "week11_absolute_timings_pooled": False,
    }
    artifacts["summary"].write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if _source_hashes(run_root) != source_hashes:
        raise RuntimeError("Week 12 analysis modified archived evidence")
    return summary, artifacts


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    summary, artifacts = analyze_run(args.run_dir, args.output_dir)
    print(
        json.dumps(
            {
                "summary": summary,
                "artifacts": {
                    key: str(value)
                    for key, value in artifacts.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
