"""Analyze a validated Week 10 timing-contamination run."""

import argparse
import csv
import json
import statistics
from pathlib import Path


EXECUTION_MODES = [
    "checked",
    "instrumented",
    "trace_only",
    "counters_only",
    "minimal",
]

MODE_COLORS = {
    "checked": "#c23b33",
    "instrumented": "#2f6db0",
    "trace_only": "#16847b",
    "counters_only": "#d27a22",
    "minimal": "#555555",
}

OVERHEAD_FIELDS = [
    "case_id",
    "family",
    "n",
    "minimal_time_ns",
    "validation_overhead_ns",
    "trace_overhead_ns",
    "counter_overhead_ns",
    "combined_instrumentation_overhead_ns",
    "checked_ratio",
    "instrumented_ratio",
    "trace_only_ratio",
    "counters_only_ratio",
    "minimal_ratio",
]

MODE_TABLE_FIELDS = [
    "execution_mode",
    "case_count",
    "median_overhead_ns",
    "median_ratio",
    "q1_ratio",
    "q3_ratio",
    "iqr_ratio",
]

SIZE_RATIO_FIELDS = [
    "n",
    "execution_mode",
    "case_count",
    "median_ratio",
    "q1_ratio",
    "q3_ratio",
]

COMPONENT_FIELDS = [
    "component",
    "comparison",
    "case_count",
    "median_overhead_ns",
    "median_ratio",
    "q1_ratio",
    "q3_ratio",
    "iqr_ratio",
]

FAMILY_RATIO_FIELDS = [
    "family",
    "execution_mode",
    "case_count",
    "median_ratio",
    "q1_ratio",
    "q3_ratio",
]

COMPONENTS = [
    (
        "validation",
        "checked / instrumented",
        "checked",
        "instrumented",
        "validation_overhead_ns",
    ),
    (
        "trace",
        "trace_only / minimal",
        "trace_only",
        "minimal",
        "trace_overhead_ns",
    ),
    (
        "counters",
        "counters_only / minimal",
        "counters_only",
        "minimal",
        "counter_overhead_ns",
    ),
    (
        "combined_instrumentation",
        "instrumented / minimal",
        "instrumented",
        "minimal",
        "combined_instrumentation_overhead_ns",
    ),
]


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
    q1 = statistics.median(lower) if lower else ordered[0]
    q3 = statistics.median(upper) if upper else ordered[-1]
    return q1, q3


def compute_case_overheads(case_rows):
    """Return one equal-weighted overhead record per generated case."""
    grouped = {}
    metadata = {}
    for row in case_rows:
        case_id = row["case_id"]
        mode = row["execution_mode"]
        if mode not in EXECUTION_MODES:
            raise ValueError(f"unknown execution mode: {mode}")
        key = (case_id, mode)
        if key in grouped:
            raise ValueError(f"duplicate case/mode summary row: {key}")
        try:
            grouped[key] = float(row["median_time_ns"])
            n = int(row["n"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid timing summary for {case_id}, mode={mode}"
            ) from exc
        current_metadata = (row["family"], n)
        previous_metadata = metadata.setdefault(case_id, current_metadata)
        if previous_metadata != current_metadata:
            raise ValueError(f"case metadata changed between modes: {case_id}")

    records = []
    for case_id, (family, n) in sorted(metadata.items()):
        missing = [
            mode
            for mode in EXECUTION_MODES
            if (case_id, mode) not in grouped
        ]
        if missing:
            raise ValueError(f"{case_id} is missing modes: {missing}")
        times = {
            mode: grouped[(case_id, mode)]
            for mode in EXECUTION_MODES
        }
        minimal = times["minimal"]
        if minimal <= 0:
            raise ValueError(f"{case_id} has non-positive minimal timing")
        records.append(
            {
                "case_id": case_id,
                "family": family,
                "n": n,
                "minimal_time_ns": minimal,
                "validation_overhead_ns": (
                    times["checked"] - times["instrumented"]
                ),
                "trace_overhead_ns": times["trace_only"] - minimal,
                "counter_overhead_ns": times["counters_only"] - minimal,
                "combined_instrumentation_overhead_ns": (
                    times["instrumented"] - minimal
                ),
                **{
                    f"{mode}_ratio": times[mode] / minimal
                    for mode in EXECUTION_MODES
                },
                **{
                    f"{mode}_time_ns": times[mode]
                    for mode in EXECUTION_MODES
                },
            }
        )
    return records


def summarize_modes(case_records):
    """Aggregate mode ratios across equal-weighted cases."""
    rows = []
    for mode in EXECUTION_MODES:
        ratios = [record[f"{mode}_ratio"] for record in case_records]
        overheads = [
            record[f"{mode}_time_ns"] - record["minimal_time_ns"]
            for record in case_records
        ]
        q1, q3 = _quartiles(ratios)
        rows.append(
            {
                "execution_mode": mode,
                "case_count": len(case_records),
                "median_overhead_ns": statistics.median(overheads),
                "median_ratio": statistics.median(ratios),
                "q1_ratio": q1,
                "q3_ratio": q3,
                "iqr_ratio": q3 - q1,
            }
        )
    return rows


def summarize_ratios_by_size(case_records):
    """Aggregate per-case slowdown ratios by size and mode."""
    grouped = {}
    for record in case_records:
        for mode in EXECUTION_MODES:
            grouped.setdefault((record["n"], mode), []).append(
                record[f"{mode}_ratio"]
            )

    rows = []
    for (n, mode), ratios in sorted(
        grouped.items(),
        key=lambda item: (
            item[0][0],
            EXECUTION_MODES.index(item[0][1]),
        ),
    ):
        q1, q3 = _quartiles(ratios)
        rows.append(
            {
                "n": n,
                "execution_mode": mode,
                "case_count": len(ratios),
                "median_ratio": statistics.median(ratios),
                "q1_ratio": q1,
                "q3_ratio": q3,
            }
        )
    return rows


def summarize_components(case_records):
    """Summarize the four frozen contamination comparisons."""
    rows = []
    for component, comparison, numerator, denominator, overhead_field in (
        COMPONENTS
    ):
        ratios = [
            record[f"{numerator}_time_ns"]
            / record[f"{denominator}_time_ns"]
            for record in case_records
        ]
        overheads = [record[overhead_field] for record in case_records]
        q1, q3 = _quartiles(ratios)
        rows.append(
            {
                "component": component,
                "comparison": comparison,
                "case_count": len(case_records),
                "median_overhead_ns": statistics.median(overheads),
                "median_ratio": statistics.median(ratios),
                "q1_ratio": q1,
                "q3_ratio": q3,
                "iqr_ratio": q3 - q1,
            }
        )
    return rows


def summarize_ratios_by_family(case_records):
    """Aggregate per-case slowdown ratios by generator family."""
    grouped = {}
    for record in case_records:
        for mode in EXECUTION_MODES:
            grouped.setdefault((record["family"], mode), []).append(
                record[f"{mode}_ratio"]
            )

    rows = []
    for (family, mode), ratios in sorted(
        grouped.items(),
        key=lambda item: (
            item[0][0],
            EXECUTION_MODES.index(item[0][1]),
        ),
    ):
        q1, q3 = _quartiles(ratios)
        rows.append(
            {
                "family": family,
                "execution_mode": mode,
                "case_count": len(ratios),
                "median_ratio": statistics.median(ratios),
                "q1_ratio": q1,
                "q3_ratio": q3,
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
                field: row.get(field, "")
                for field in fields
            }
            for row in rows
        )


def _svg_text(x, y, text, size=13, anchor="start", weight="normal"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="#202020">{text}</text>'
    )


def _write_ratio_figure(size_rows, path, plotted_modes, title, subtitle):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    width = 920
    height = 540
    left = 82
    right = 225
    top = 65
    bottom = 75
    plot_width = width - left - right
    plot_height = height - top - bottom
    sizes = sorted({int(row["n"]) for row in size_rows})
    values = {
        (int(row["n"]), row["execution_mode"]): float(row["median_ratio"])
        for row in size_rows
    }
    ratios = [
        values[(n, mode)]
        for n in sizes
        for mode in plotted_modes
    ]
    y_min = min(0.98, min(ratios))
    y_max = max(ratios)
    padding = max((y_max - y_min) * 0.12, 0.04)
    y_max += padding
    y_min = max(0, y_min - padding)

    def x_position(index):
        if len(sizes) == 1:
            return left + plot_width / 2
        return left + index * plot_width / (len(sizes) - 1)

    def y_position(value):
        return top + (y_max - value) * plot_height / (y_max - y_min)

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        _svg_text(
            width / 2,
            30,
            title,
            size=19,
            anchor="middle",
            weight="bold",
        ),
        _svg_text(
            width / 2,
            51,
            subtitle,
            size=12,
            anchor="middle",
        ),
    ]

    tick_count = 5
    for tick in range(tick_count + 1):
        ratio = y_min + tick * (y_max - y_min) / tick_count
        y = y_position(ratio)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" '
            f'x2="{left + plot_width}" y2="{y:.2f}" '
            'stroke="#dddddd" stroke-width="1"/>'
        )
        parts.append(
            _svg_text(left - 10, y + 4, f"{ratio:.2f}x", anchor="end")
        )

    baseline_y = y_position(1.0)
    parts.append(
        f'<line x1="{left}" y1="{baseline_y:.2f}" '
        f'x2="{left + plot_width}" y2="{baseline_y:.2f}" '
        'stroke="#555555" stroke-width="1.5" stroke-dasharray="5 5"/>'
    )

    for index, n in enumerate(sizes):
        x = x_position(index)
        parts.append(
            f'<line x1="{x:.2f}" y1="{top + plot_height}" '
            f'x2="{x:.2f}" y2="{top + plot_height + 6}" '
            'stroke="#333333"/>'
        )
        parts.append(
            _svg_text(
                x,
                top + plot_height + 25,
                str(n),
                anchor="middle",
            )
        )

    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" '
        f'y2="{top + plot_height}" stroke="#333333" stroke-width="1.5"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top + plot_height}" '
        f'x2="{left + plot_width}" y2="{top + plot_height}" '
        'stroke="#333333" stroke-width="1.5"/>'
    )
    parts.append(
        _svg_text(
            left + plot_width / 2,
            height - 22,
            "Input size n",
            anchor="middle",
            weight="bold",
        )
    )

    for mode in plotted_modes:
        points = [
            (
                x_position(index),
                y_position(values[(n, mode)]),
            )
            for index, n in enumerate(sizes)
        ]
        point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        color = MODE_COLORS[mode]
        parts.append(
            f'<polyline points="{point_text}" fill="none" '
            f'stroke="{color}" stroke-width="3"/>'
        )
        for x, y in points:
            parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" '
                f'fill="{color}" stroke="#ffffff" stroke-width="1.5"/>'
            )

    legend_x = left + plot_width + 28
    legend_y = top + 20
    parts.append(
        _svg_text(legend_x, legend_y - 17, "Execution mode", weight="bold")
    )
    for index, mode in enumerate(plotted_modes):
        y = legend_y + index * 34
        color = MODE_COLORS[mode]
        parts.append(
            f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 28}" '
            f'y2="{y}" stroke="{color}" stroke-width="3"/>'
        )
        parts.append(_svg_text(legend_x + 38, y + 5, mode))

    parts.append("</svg>")
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_ratio_figure(size_rows, path):
    """Write the full-scale execution-mode slowdown figure."""
    _write_ratio_figure(
        size_rows,
        path,
        [mode for mode in EXECUTION_MODES if mode != "minimal"],
        "Week 10 execution-mode slowdown relative to minimal",
        "Median of equal-weighted case ratios at each input size",
    )


def write_observation_ratio_figure(size_rows, path):
    """Write a zoomed figure for trace and counter observation costs."""
    _write_ratio_figure(
        size_rows,
        path,
        ["instrumented", "trace_only", "counters_only"],
        "Week 10 observation overhead relative to minimal",
        "Zoomed view without checked-mode backend validation",
    )


def require_validated_run(run_dir):
    report_path = Path(run_dir) / "validation_report.json"
    report = read_json(report_path)
    if not isinstance(report, dict) or report.get("valid") is not True:
        raise ValueError(
            "Week 10 run must have a successful validation_report.json"
        )
    return report


def analyze_run(
    run_dir,
    case_overheads_csv,
    mode_table_csv,
    component_table_csv,
    size_ratios_csv,
    family_ratios_csv,
    ratio_figure,
    observation_figure,
):
    require_validated_run(run_dir)
    case_rows = read_csv(Path(run_dir) / "case_summary.csv")
    case_records = compute_case_overheads(case_rows)
    mode_rows = summarize_modes(case_records)
    component_rows = summarize_components(case_records)
    size_rows = summarize_ratios_by_size(case_records)
    family_rows = summarize_ratios_by_family(case_records)
    write_csv(case_records, case_overheads_csv, OVERHEAD_FIELDS)
    write_csv(mode_rows, mode_table_csv, MODE_TABLE_FIELDS)
    write_csv(component_rows, component_table_csv, COMPONENT_FIELDS)
    write_csv(size_rows, size_ratios_csv, SIZE_RATIO_FIELDS)
    write_csv(family_rows, family_ratios_csv, FAMILY_RATIO_FIELDS)
    write_ratio_figure(size_rows, ratio_figure)
    write_observation_ratio_figure(size_rows, observation_figure)
    return case_records, mode_rows, component_rows, size_rows, family_rows


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--case-overheads-csv", type=Path, required=True)
    parser.add_argument("--mode-table-csv", type=Path, required=True)
    parser.add_argument("--component-table-csv", type=Path, required=True)
    parser.add_argument("--size-ratios-csv", type=Path, required=True)
    parser.add_argument("--family-ratios-csv", type=Path, required=True)
    parser.add_argument("--ratio-figure", type=Path, required=True)
    parser.add_argument("--observation-figure", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    (
        case_records,
        mode_rows,
        component_rows,
        size_rows,
        family_rows,
    ) = analyze_run(
        args.run_dir,
        args.case_overheads_csv,
        args.mode_table_csv,
        args.component_table_csv,
        args.size_ratios_csv,
        args.family_ratios_csv,
        args.ratio_figure,
        args.observation_figure,
    )
    print(
        json.dumps(
            {
                "case_count": len(case_records),
                "mode_table_rows": len(mode_rows),
                "component_table_rows": len(component_rows),
                "size_ratio_rows": len(size_rows),
                "family_ratio_rows": len(family_rows),
                "mode_table": mode_rows,
                "component_table": component_rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
