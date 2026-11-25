"""Build the defence plots from the inputs used by the two thesis figures.

Run python3 talk/figures/plot_results.py from the repository root. The ratio plot
reads the manuscript's saved plotting rows. The growth plots share the
manuscript's archive reader, band definitions and median calculation.
"""

from decimal import Decimal, ROUND_HALF_UP
import json
import math
from pathlib import Path
import re
from statistics import median
import sys
import tarfile
from tempfile import TemporaryDirectory

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
from docs.thesis.baseline_comparison_revision_20261120 import generate as growth
from docs.thesis.unified_results_20261101 import generate as ratios


def save(fig, filename):
    fig.savefig(HERE / filename, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def outside_legend(ax):
    ax.legend(loc="center left", bbox_to_anchor=(1.01, .5), frameon=False,
              borderaxespad=0, handlelength=1.6, handletextpad=.5)


def ratio_figure():
    data = json.loads((ratios.HERE / "derived.json").read_text())
    cases = data["graph_inputs"]["ratio_by_n"]
    fig, ax = plt.subplots(figsize=(6.8, 2.75), layout="constrained")
    ratios.scatter(ax, cases, lambda case: case["n"])
    ratios.baseline(ax)
    for source in ratios.SOURCES:
        groups = {}
        for case in cases:
            if case["source"] == source:
                groups.setdefault(case["n"], []).append(case["ratio"])
        lengths = sorted(groups)
        ax.plot(lengths, [median(groups[n]) for n in lengths],
                color=ratios.COLORS[source], lw=1.2, alpha=.9)
    ax.set_xscale("log", base=2)
    ax.set_xticks(growth.NOMINAL, labels=growth.NOMINAL)
    ax.set(xlabel="Input length $n$", xlim=(29, 570), ylim=(.55, 1.59))
    outside_legend(ax)
    save(fig, "ratio_by_length.pdf")


def fixed_source_times():
    cases = growth.inputs()
    with TemporaryDirectory() as temp:
        with tarfile.open(growth.ARCHIVE / "raw_records.tar.gz") as archive:
            archive.extractall(temp, filter="data")
        raw = Path(temp)
        manifest, config, selected, _, _ = growth.preparation(raw / "preparation", cases)
        times = growth.formal(raw / "formal", cases, manifest, config, selected)

    groups = [[case["case_id"] for case in cases
               if lo <= case["n"] <= hi and case["source"] in {"common", "geometric"}]
              for lo, hi in growth.BANDS]
    return growth.growth_curves(times, groups)


def published_growth_labels():
    macro_names = {
        "ordinary_list": "BaselineListGrowth",
        "heterogeneous_finger_uninstrumented": "BaselineTreeGrowth",
        "merge_sort": "BaselineMergeGrowth",
        "quick_sort": "BaselineQuickGrowth",
        "sorted": "BaselineBuiltinGrowth",
    }
    source = (ROOT / "thesis/generated/baseline_comparison.tex").read_text()
    values = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{([\d.]+)\}", source))
    return {
        method: Decimal(values[name]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        for method, name in macro_names.items()
    }


def growth_figures():
    nominal = growth.NOMINAL
    steps = range(len(nominal) - 1)
    series = fixed_source_times()
    factors = published_growth_labels()
    curve_fig, curve = plt.subplots(figsize=(6.8, 2.75), layout="constrained")
    exp_fig, exponent = plt.subplots(figsize=(6.8, 3.0), layout="constrained")

    for method, (label, color, marker) in growth.STYLES.items():
        times = series[method]
        style = dict(color=color, marker=marker, ms=4.5, lw=1.5)
        curve.plot(nominal, [t / times[0] for t in times],
                   label=f"{label} ({factors[method]}×)", **style)
        exponent.plot(steps, [math.log2(b / a) for a, b in zip(times, times[1:])], label=label, **style)

    for ax in (curve, exponent):
        ax.grid(alpha=.22, linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
        outside_legend(ax)

    curve.set(xscale="log", yscale="log", xlim=(28, 690), ylim=(.82, 64),
              xlabel="Nominal input length", ylabel="Time / first-band median")
    curve.set_xticks(nominal, labels=nominal)
    ticks = [1, 2, 4, 8, 16, 32, 64]
    curve.set_yticks(ticks, labels=ticks)
    curve.minorticks_off()
    for fn, ls in ((lambda n: n, "--"), (lambda n: n * math.log2(n), "--"),
                   (lambda n: n * n, ":")):
        curve.plot(nominal, [fn(n) / fn(nominal[0]) for n in nominal],
                   color=".55", lw=.95, ls=ls, zorder=1)
    for x, y, label in ((535, 11, "$n$"), (475, 37, r"$n\,\log_2 n$"), (178, 43, "$n^2$")):
        curve.text(x, y, label, fontsize=11, color=".36")

    exponent.set(xticks=list(steps), xticklabels=[f"{a}→{b}" for a, b in zip(nominal, nominal[1:])],
                 xlim=(-.18, 3.58), ylim=(.6, 2.2), yticks=[.6, .8, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.2],
                 xlabel="Nominal size step", ylabel="Doubling exponent")
    for value, label, ls in ((1, "linear", "--"), (2, "quadratic", ":")):
        exponent.axhline(value, color=".48", ls=ls, lw=.9, zorder=1)
        exponent.annotate(label, xy=(3.55, value), xytext=(0, 3), textcoords="offset points",
                          ha="right", va="bottom", fontsize=10.8, color=".33")

    save(curve_fig, "growth_curves.pdf")
    save(exp_fig, "growth_exponent.pdf")


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42,
                         "axes.labelsize": 13.5, "xtick.labelsize": 12,
                         "ytick.labelsize": 12, "legend.fontsize": 12})
    ratio_figure()
    growth_figures()
