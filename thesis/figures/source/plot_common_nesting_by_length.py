"""Plot common-source medians from the archived complete formal comparison."""

import csv
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


FIGURES = Path(__file__).resolve().parents[1]
ARCHIVE = FIGURES.parents[1] / "docs/validation/unified_formal_20261101"
CASES = ARCHIVE / "unified_analysis_bca4c1c6_restart_20261101_01/cases.csv"
CATEGORIES = (
    ("strict_flat", "Strict-flat", "#3366AA", "o"),
    ("low_nesting_valid", "Low", "#AA3377", "s"),
    ("medium_nesting_valid", "Medium", "#228866", "^"),
    ("nested_heavy_valid", "Heavy", "#A86112", "D"),
)


def main():
    ratios = defaultdict(list)
    with CASES.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["source"] == "common":
                ratios[int(row["n"]), row["category"]].append(float(row["ratio"]))

    lengths = sorted({n for n, _ in ratios})
    even_lengths = [n for n in lengths if n % 2 == 0]
    medians = {group: median(values) for group, values in ratios.items()}

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "pdf.fonttype": 42, "axes.linewidth": 0.6})
    fig, ax = plt.subplots(figsize=(6.25, 2.5), layout="constrained")
    ax.axhline(1, color="0.35", linewidth=0.85, linestyle="--", zorder=1)
    ax.grid(axis="y", color="0.88", linewidth=0.55)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for category, label, color, marker in CATEGORIES:
        ax.plot(even_lengths, [medians[n, category] for n in even_lengths],
                color=color, marker=marker, label=label, linewidth=1.35,
                markersize=4)

    ax.set_xscale("log", base=2)
    ax.set_xticks(even_lengths, labels=[str(n) for n in even_lengths])
    ax.set_yticks([0.50, 0.75, 1.00, 1.25, 1.50])
    ax.set(xlabel="Input length $n$", ylabel="Median tree/list ratio", ylim=(0.5, 1.59))
    ax.legend(loc="lower left", ncol=2, frameon=False, fontsize=8)
    fig.savefig(FIGURES / "unified_common_nesting_by_length.pdf",
                metadata={"Creator": Path(__file__).name,
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)

    print("Length, " + ", ".join(label for _, label, _, _ in CATEGORIES))
    for n in lengths:
        print(f"{n}, " + ", ".join(f"{medians[n, category]:.6f}"
                                  for category, _, _, _ in CATEGORIES))


if __name__ == "__main__":
    main()
