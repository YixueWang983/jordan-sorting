"""Analyze archived Week 11 pilot evidence without modifying the run."""

import argparse
import csv
import html
import json
import math
import statistics
from pathlib import Path

from validate_week11_pilot_outputs import validate_outputs
from week11_experiment_protocol import (
    PAPER_ALGORITHM_NAME,
    WEEK11_EXPERIMENT_PROTOCOL,
)


PYTHON_ALGORITHM = "python_sort"
REFERENCE_ALGORITHM = "simplified_jordan_reference"
ALGORITHMS = WEEK11_EXPERIMENT_PROTOCOL.algorithms
COMPARISONS = (
    ("paper/reference", PAPER_ALGORITHM_NAME, REFERENCE_ALGORITHM),
    ("paper/python", PAPER_ALGORITHM_NAME, PYTHON_ALGORITHM),
    ("reference/python", REFERENCE_ALGORITHM, PYTHON_ALGORITHM),
)
HIGH_RELATIVE_IQR_THRESHOLD = 0.25
COUNTER_FIELDS = (
    "paper_sibling_scan_checks",
    "paper_sibling_list_splits",
    "paper_split_items_copied",
    "paper_split_items_transferred",
    "paper_invariant_checks",
)

CASE_RUNTIME_FIELDS = (
    "case_id",
    "family",
    "n",
    "algorithm",
    "measured_run_count",
    "median_time_ns",
    "q1_time_ns",
    "q3_time_ns",
    "iqr_time_ns",
    "relative_iqr",
    "mean_time_ns",
    "stdev_time_ns",
)
RUNTIME_GROUP_FIELDS = (
    "family",
    "n",
    "algorithm",
    "case_count",
    "median_case_time_ns",
    "q1_case_time_ns",
    "q3_case_time_ns",
    "iqr_case_time_ns",
    "median_relative_iqr",
    "max_relative_iqr",
)
RATIO_FIELDS = (
    "scope",
    "family",
    "n",
    "comparison",
    "case_count",
    "median_ratio",
    "q1_ratio",
    "q3_ratio",
    "iqr_ratio",
)
ELAPSED_FIELDS = (
    "algorithm",
    "measured_call_count",
    "measured_call_total_ns",
    "measured_call_total_seconds",
)
STRUCTURE_RELATIONSHIP_FIELDS = (
    "n",
    "algorithm",
    "case_count",
    "nesting_density_spearman",
    "max_depth_spearman",
    "containment_pair_density_spearman",
)
COUNTER_RELATIONSHIP_FIELDS = (
    "n",
    "counter",
    "case_count",
    "counter_min",
    "counter_max",
    "runtime_spearman",
)

ALGORITHM_COLORS = {
    PYTHON_ALGORITHM: "#3f6f4e",
    REFERENCE_ALGORITHM: "#2f6db0",
    PAPER_ALGORITHM_NAME: "#c0523b",
}
RATIO_COLORS = {
    "paper/reference": "#c0523b",
    "paper/python": "#7455a4",
    "reference/python": "#2f6db0",
}


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _quartiles(values):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot summarize an empty value set")
    if len(ordered) == 1:
        return ordered[0], ordered[0]
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 0:
        lower = ordered[:midpoint]
        upper = ordered[midpoint:]
    else:
        lower = ordered[:midpoint]
        upper = ordered[midpoint + 1 :]
    return statistics.median(lower), statistics.median(upper)


def _as_int(value, field_name):
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc


def _as_float(value, field_name):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _rankdata(values):
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(indexed):
        end = position + 1
        while end < len(indexed) and indexed[end][1] == indexed[position][1]:
            end += 1
        average_rank = (position + 1 + end) / 2
        for index in range(position, end):
            ranks[indexed[index][0]] = average_rank
        position = end
    return ranks


def _pearson(left, right):
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)
    left_delta = [value - left_mean for value in left]
    right_delta = [value - right_mean for value in right]
    denominator = math.sqrt(
        sum(value * value for value in left_delta)
        * sum(value * value for value in right_delta)
    )
    if denominator == 0:
        return None
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left_delta, right_delta)
    ) / denominator


def _spearman(left, right):
    return _pearson(_rankdata(left), _rankdata(right))


def load_case_runtime_records(case_rows):
    """Validate and normalize one row per case and algorithm."""
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
        if measured_runs != WEEK11_EXPERIMENT_PROTOCOL.measured_runs:
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
    expected = set(ALGORITHMS)
    for case_id, algorithms in algorithms_by_case.items():
        if algorithms != expected:
            raise ValueError(f"case is missing algorithms: {case_id}")
    if len(algorithms_by_case) != WEEK11_EXPERIMENT_PROTOCOL.case_count:
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


def summarize_runtime(records, group_fields):
    grouped = {}
    for record in records:
        key = tuple(record[field] for field in group_fields) + (
            record["algorithm"],
        )
        grouped.setdefault(key, []).append(record)
    rows = []
    for key, group in grouped.items():
        values = [record["median_time_ns"] for record in group]
        relative_iqrs = [record["relative_iqr"] for record in group]
        q1, q3 = _quartiles(values)
        key_values = dict(zip(group_fields, key[:-1]))
        rows.append(
            {
                "family": key_values.get("family", ""),
                "n": key_values.get("n", ""),
                "algorithm": key[-1],
                "case_count": len(group),
                "median_case_time_ns": statistics.median(values),
                "q1_case_time_ns": q1,
                "q3_case_time_ns": q3,
                "iqr_case_time_ns": q3 - q1,
                "median_relative_iqr": statistics.median(relative_iqrs),
                "max_relative_iqr": max(relative_iqrs),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            row["family"],
            int(row["n"]) if row["n"] != "" else -1,
            ALGORITHMS.index(row["algorithm"]),
        ),
    )


def build_case_ratio_records(records):
    grouped = {}
    for record in records:
        grouped.setdefault(record["case_id"], {})[record["algorithm"]] = record
    rows = []
    for case_id, algorithms in grouped.items():
        for comparison, numerator, denominator in COMPARISONS:
            numerator_record = algorithms[numerator]
            denominator_record = algorithms[denominator]
            denominator_time = denominator_record["median_time_ns"]
            if denominator_time <= 0:
                raise ValueError(f"non-positive ratio denominator: {case_id}")
            rows.append(
                {
                    "case_id": case_id,
                    "family": numerator_record["family"],
                    "n": numerator_record["n"],
                    "comparison": comparison,
                    "ratio": numerator_record["median_time_ns"] / denominator_time,
                }
            )
    return rows


def summarize_ratios(case_ratio_records):
    scope_fields = (
        ("overall", ()),
        ("size", ("n",)),
        ("family", ("family",)),
        ("family_size", ("family", "n")),
    )
    rows = []
    for scope, fields in scope_fields:
        grouped = {}
        for record in case_ratio_records:
            key = tuple(record[field] for field in fields) + (
                record["comparison"],
            )
            grouped.setdefault(key, []).append(record["ratio"])
        for key, values in grouped.items():
            q1, q3 = _quartiles(values)
            key_values = dict(zip(fields, key[:-1]))
            rows.append(
                {
                    "scope": scope,
                    "family": key_values.get("family", ""),
                    "n": key_values.get("n", ""),
                    "comparison": key[-1],
                    "case_count": len(values),
                    "median_ratio": statistics.median(values),
                    "q1_ratio": q1,
                    "q3_ratio": q3,
                    "iqr_ratio": q3 - q1,
                }
            )
    comparison_order = [item[0] for item in COMPARISONS]
    return sorted(
        rows,
        key=lambda row: (
            ("overall", "size", "family", "family_size").index(row["scope"]),
            row["family"],
            int(row["n"]) if row["n"] != "" else -1,
            comparison_order.index(row["comparison"]),
        ),
    )


def summarize_measured_elapsed(raw_rows):
    grouped = {algorithm: [] for algorithm in ALGORITHMS}
    for row in raw_rows:
        algorithm = row.get("algorithm")
        if algorithm not in grouped:
            raise ValueError("raw data contains an unknown algorithm")
        time_ns = _as_int(row.get("time_ns"), "time_ns")
        if time_ns <= 0 or row.get("error") or row.get("output_correct") != "True":
            raise ValueError("raw data contains a failed measured call")
        grouped[algorithm].append(time_ns)
    rows = []
    for algorithm in ALGORITHMS:
        values = grouped[algorithm]
        rows.append(
            {
                "algorithm": algorithm,
                "measured_call_count": len(values),
                "measured_call_total_ns": sum(values),
                "measured_call_total_seconds": sum(values) / 1_000_000_000,
            }
        )
    total_count = sum(row["measured_call_count"] for row in rows)
    total_ns = sum(row["measured_call_total_ns"] for row in rows)
    rows.append(
        {
            "algorithm": "all_algorithms",
            "measured_call_count": total_count,
            "measured_call_total_ns": total_ns,
            "measured_call_total_seconds": total_ns / 1_000_000_000,
        }
    )
    return rows


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
    if len(records) != WEEK11_EXPERIMENT_PROTOCOL.case_count:
        raise ValueError("case audit has an unexpected case count")
    return records


def summarize_structure_relationships(case_records, audit_records):
    grouped = {}
    for record in case_records:
        audit = audit_records[record["case_id"]]
        grouped.setdefault((record["n"], record["algorithm"]), []).append(
            (record, audit)
        )
    rows = []
    for (n, algorithm), group in sorted(
        grouped.items(),
        key=lambda item: (item[0][0], ALGORITHMS.index(item[0][1])),
    ):
        log_times = [math.log(item[0]["median_time_ns"]) for item in group]
        rows.append(
            {
                "n": n,
                "algorithm": algorithm,
                "case_count": len(group),
                "nesting_density_spearman": _spearman(
                    [item[1]["nesting_density"] for item in group],
                    log_times,
                ),
                "max_depth_spearman": _spearman(
                    [item[1]["max_depth"] for item in group],
                    log_times,
                ),
                "containment_pair_density_spearman": _spearman(
                    [item[1]["containment_pair_density"] for item in group],
                    log_times,
                ),
            }
        )
    return rows


def summarize_counter_relationships(case_records, audit_records):
    paper_records = {
        record["case_id"]: record
        for record in case_records
        if record["algorithm"] == PAPER_ALGORITHM_NAME
    }
    rows = []
    for n in WEEK11_EXPERIMENT_PROTOCOL.sizes:
        case_ids = sorted(
            case_id
            for case_id, record in paper_records.items()
            if record["n"] == n
        )
        log_times = [
            math.log(paper_records[case_id]["median_time_ns"])
            for case_id in case_ids
        ]
        for counter in COUNTER_FIELDS:
            values = [audit_records[case_id][counter] for case_id in case_ids]
            rows.append(
                {
                    "n": n,
                    "counter": counter,
                    "case_count": len(case_ids),
                    "counter_min": min(values),
                    "counter_max": max(values),
                    "runtime_spearman": _spearman(values, log_times),
                }
            )
    return rows


def write_csv(rows, path, fields):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {
                field: "" if row.get(field) is None else row.get(field, "")
                for field in fields
            }
            for row in rows
        )


def _svg_text(x, y, text, size=13, anchor="start", weight="normal"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="#202020">'
        f"{html.escape(str(text))}</text>"
    )


def _svg_vertical_text(x, y, text, size=12, weight="bold"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
        f'font-size="{size}" text-anchor="middle" font-weight="{weight}" '
        f'fill="#202020" transform="rotate(-90 {x} {y})">'
        f"{html.escape(str(text))}</text>"
    )


def _write_line_figure(
    series,
    path,
    *,
    title,
    subtitle,
    y_label,
    log_scale,
    value_kind,
    baseline=None,
    canvas_width=960,
    legend_width=270,
):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    sizes = sorted({n for values in series.values() for n in values})
    raw_values = [value for values in series.values() for value in values.values()]
    if not raw_values or any(value <= 0 for value in raw_values):
        raise ValueError("figure requires positive values")
    plotted_values = [math.log10(value) for value in raw_values] if log_scale else raw_values
    y_min = min(plotted_values)
    y_max = max(plotted_values)
    padding = max((y_max - y_min) * 0.12, 0.08 if log_scale else 0.05)
    y_min -= padding
    y_max += padding
    width, height = canvas_width, 560
    left, right, top, bottom = 92, legend_width, 72, 78
    plot_width = width - left - right
    plot_height = height - top - bottom

    def x_position(index):
        return left + index * plot_width / max(1, len(sizes) - 1)

    def transform(value):
        return math.log10(value) if log_scale else value

    def y_position(value):
        return top + (y_max - transform(value)) * plot_height / (y_max - y_min)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        _svg_text(width / 2, 31, title, 19, "middle", "bold"),
        _svg_text(width / 2, 53, subtitle, 12, "middle"),
    ]
    for tick in range(6):
        transformed = y_min + tick * (y_max - y_min) / 5
        value = 10**transformed if log_scale else transformed
        y = top + (y_max - transformed) * plot_height / (y_max - y_min)
        if value_kind == "runtime_ns":
            label = f"{value / 1_000_000:.3g} ms"
        elif value_kind == "ratio":
            label = f"{value:.3g}x"
        else:
            raise ValueError(f"unsupported figure value kind: {value_kind!r}")
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#dddddd"/>'
        )
        parts.append(_svg_text(left - 9, y + 4, label, 12, "end"))
    if baseline is not None and y_min <= transform(baseline) <= y_max:
        y = y_position(baseline)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#555555" stroke-dasharray="5 5"/>'
        )
    for index, n in enumerate(sizes):
        x = x_position(index)
        parts.append(_svg_text(x, top + plot_height + 27, n, 13, "middle"))
    parts.extend(
        [
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#333333" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#333333" stroke-width="1.5"/>',
            _svg_text(left + plot_width / 2, height - 22, "Input size n", 13, "middle", "bold"),
            _svg_vertical_text(20, top + plot_height / 2, y_label),
        ]
    )
    legend_x = left + plot_width + 28
    for series_index, (label, values) in enumerate(series.items()):
        color = (
            ALGORITHM_COLORS.get(label)
            or RATIO_COLORS.get(label)
            or "#555555"
        )
        points = [
            (x_position(index), y_position(values[n]))
            for index, n in enumerate(sizes)
        ]
        parts.append(
            '<polyline points="'
            + " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
            + f'" fill="none" stroke="{color}" stroke-width="3"/>'
        )
        for x, y in points:
            parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{color}" stroke="#ffffff"/>'
            )
        legend_y = top + 18 + series_index * 42
        parts.append(
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 27}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(_svg_text(legend_x + 36, legend_y + 5, label, 11))
    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_runtime_figure(size_rows, path):
    series = {
        algorithm: {
            int(row["n"]): float(row["median_case_time_ns"])
            for row in size_rows
            if row["algorithm"] == algorithm
        }
        for algorithm in ALGORITHMS
    }
    _write_line_figure(
        series,
        path,
        title="Week 11 median case runtime by input size",
        subtitle="Equal-weighted case medians; logarithmic runtime axis",
        y_label="Median runtime",
        log_scale=True,
        value_kind="runtime_ns",
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
    _write_line_figure(
        series,
        path,
        title="Week 11 case-median runtime ratios by input size",
        subtitle="Per-case ratios; equal-weight aggregation; logarithmic ratio axis",
        y_label="Runtime ratio",
        log_scale=True,
        value_kind="ratio",
        baseline=1.0,
    )


def require_validated_run(run_dir, report_path):
    """Validate live evidence while writing the report outside the run."""
    report = validate_outputs(run_dir, report_json=report_path)
    if not isinstance(report, dict) or report.get("valid") is not True:
        raise ValueError("Week 11 evidence failed live validation")
    return report


def analyze_run(run_dir, output_dir):
    run_path = Path(run_dir)
    run_root = run_path.resolve()
    output_root = Path(output_dir).resolve()
    if output_root == run_root or run_root in output_root.parents:
        raise ValueError("analysis output must be outside archived evidence")
    output_root.mkdir(parents=True, exist_ok=True)
    live_report_path = output_root / "week11_live_validation_report.json"
    validation_report = require_validated_run(run_path, live_report_path)
    manifest = read_json(run_root / "manifest.json")
    case_records = load_case_runtime_records(
        read_csv(run_root / "case_summary.csv")
    )
    raw_rows = read_csv(run_root / "raw.csv")
    audit_records = load_audit_records(read_csv(run_root / "case_audit.csv"))
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

    artifacts = {
        "case_runtime": output_root / "week11_case_runtime_metrics.csv",
        "runtime_by_size": output_root / "week11_runtime_by_size.csv",
        "runtime_by_family": output_root / "week11_runtime_by_family.csv",
        "runtime_by_family_size": output_root / "week11_runtime_by_family_size.csv",
        "runtime_ratios": output_root / "week11_runtime_ratios.csv",
        "measured_elapsed": output_root / "week11_measured_elapsed.csv",
        "structure_relationships": output_root / "week11_structure_runtime_relationships.csv",
        "counter_relationships": output_root / "week11_paper_counter_runtime_relationships.csv",
        "runtime_figure": output_root / "week11_runtime_by_size.svg",
        "ratio_figure": output_root / "week11_runtime_ratio_by_size.svg",
        "summary": output_root / "week11_analysis_summary.json",
        "live_validation": live_report_path,
    }
    write_csv(case_records, artifacts["case_runtime"], CASE_RUNTIME_FIELDS)
    write_csv(size_rows, artifacts["runtime_by_size"], RUNTIME_GROUP_FIELDS)
    write_csv(family_rows, artifacts["runtime_by_family"], RUNTIME_GROUP_FIELDS)
    write_csv(
        family_size_rows,
        artifacts["runtime_by_family_size"],
        RUNTIME_GROUP_FIELDS,
    )
    write_csv(ratio_rows, artifacts["runtime_ratios"], RATIO_FIELDS)
    write_csv(elapsed_rows, artifacts["measured_elapsed"], ELAPSED_FIELDS)
    write_csv(
        structure_rows,
        artifacts["structure_relationships"],
        STRUCTURE_RELATIONSHIP_FIELDS,
    )
    write_csv(
        counter_rows,
        artifacts["counter_relationships"],
        COUNTER_RELATIONSHIP_FIELDS,
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
    summary = {
        "source_run": str(run_path),
        "source_commit": manifest["source_commit"],
        "validation_valid": validation_report["valid"],
        "row_counts": validation_report["row_counts"],
        "case_runtime_rows": len(case_records),
        "runtime_by_size_rows": len(size_rows),
        "runtime_by_family_rows": len(family_rows),
        "runtime_by_family_size_rows": len(family_size_rows),
        "ratio_rows": len(ratio_rows),
        "structure_relationship_rows": len(structure_rows),
        "counter_relationship_rows": len(counter_rows),
        "high_relative_iqr_threshold": HIGH_RELATIVE_IQR_THRESHOLD,
        "high_relative_iqr_rows": len(high_variability),
        "maximum_relative_iqr": max(
            record["relative_iqr"] for record in case_records
        ),
        "overall_case_median_ratios": overall_ratios,
        "measured_call_total_seconds": elapsed_rows[-1][
            "measured_call_total_seconds"
        ],
        "wall_clock_elapsed_available": False,
    }
    artifacts["summary"].write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
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
