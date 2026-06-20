"""Summarize raw baseline CSV output into per-(algorithm,family,n) aggregates."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import argparse
import csv


SUMMARY_FIELDS = [
    "algorithm",
    "family",
    "n",
    "run_count",
    "min_time_ns",
    "median_time_ns",
    "mean_time_ns",
    "max_time_ns",
    "all_correct",
]


def csv_value(value):
    if value is None:
        return ""
    return value


def read_rows(csv_path):
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _safe_int(value):
    if value == "" or value is None:
        return None
    return int(float(value))


def _to_float_rows(raw_rows):
    parsed = []
    for row in raw_rows:
        time_ns = _safe_int(row["time_ns"])
        sorted_correct = row["sorted_correct"] == "True"
        parsed.append(
            {
                "algorithm": row["algorithm"],
                "family": row["family"],
                "n": int(row["n"]),
                "time_ns": time_ns,
                "sorted_correct": sorted_correct,
            }
        )
    return parsed


def _median(values):
    sorted_values = sorted(values)
    mid = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[mid]
    return (sorted_values[mid - 1] + sorted_values[mid]) / 2


def summarize(rows):
    parsed = _to_float_rows(rows)
    groups = defaultdict(list)

    for row in parsed:
        if row["time_ns"] is None:
            continue
        groups[(row["algorithm"], row["family"], row["n"])].append(row)

    summary = []
    for key, group_rows in sorted(groups.items()):
        times = [r["time_ns"] for r in group_rows]
        run_count = len(times)
        if run_count == 0:
            continue

        summary.append(
            {
                "algorithm": key[0],
                "family": key[1],
                "n": key[2],
                "run_count": run_count,
                "min_time_ns": min(times),
                "median_time_ns": _median(times),
                "mean_time_ns": sum(times) / run_count,
                "max_time_ns": max(times),
                "all_correct": all(r["sorted_correct"] for r in group_rows),
            }
        )

    return summary


def write_summary(summary_rows, output_csv):
    path = Path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary_rows)


@dataclass(frozen=True)
class SummaryConfig:
    input_csv: Path
    output_csv: Path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("results/week1_baseline_results.csv"),
        help="input raw CSV from run_small_tests",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("results/week1_baseline_summary.csv"),
        help="output summary CSV",
    )
    return parser.parse_args()


def run():
    args = parse_args()
    config = SummaryConfig(input_csv=args.input_csv, output_csv=args.output_csv)

    raw_rows = read_rows(config.input_csv)
    summary_rows = summarize(raw_rows)
    write_summary(summary_rows, config.output_csv)

    print(f"wrote {len(summary_rows)} rows to {config.output_csv}")


if __name__ == "__main__":
    run()
