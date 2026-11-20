"""Generate the thesis supplement from the archived, independently verified sessions."""
from collections import Counter
from datetime import datetime
import json
import math
from pathlib import Path
from statistics import median
import sys
import tarfile
from tempfile import TemporaryDirectory

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiments"))
from analyze_baseline_comparison import preparation, formal
from baseline_comparison import CANDIDATES, METHODS, inputs, TARGET_NS

ARCHIVE = ROOT / "docs/validation/baseline_comparison_20261120"
FIGURES = ROOT / "thesis/figures"
BANDS = ((32, 33), (64, 70), (128, 129), (256, 257), (512, 513))
NOMINAL = [low for low, high in BANDS]
NAMES = ("Jordan list", "Jordan tree", "Merge sort", "Quicksort", "sorted() [C]")
COLORS = ("#993d13", "#146a82", "#3f627b", "#7b5787", "#4c6836")
MARKERS = ("o", "s", "^", "D", "x")


def method_curves(ax, x, series):
    for m, name, color, marker in zip(METHODS, NAMES, COLORS, MARKERS):
        ax.plot(x, series[m], label=name, color=color, marker=marker, ms=4, lw=1.45)
    ax.grid(axis="y", alpha=.18)
    ax.spines[["top", "right"]].set_visible(False)


def save(fig, filename):
    fig.savefig(FIGURES / filename, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def growth_curves(times, groups):
    return {m: [median(times[i,m] for i in ids) for ids in groups] for m in METHODS}


def growth_figure(series):
    normalized = {m: [t / vals[0] for t in vals] for m, vals in series.items()}
    slopes = {m: [math.log2(b/a) for a,b in zip(vals, vals[1:])] for m, vals in series.items()}
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(6.1, 5.3))
    method_curves(top, NOMINAL, normalized)
    fig.legend(*top.get_legend_handles_labels(), loc="upper center", ncol=5, frameon=False,
               columnspacing=1, handlelength=1.5)
    for fn, name, style in ((lambda n:n, "$n$", "--"), (lambda n:n*math.log2(n), "$n\\,\\log_2 n$", "-."),
                            (lambda n:n*n, "$n^2$", ":")):
        top.plot(NOMINAL, [fn(n)/fn(NOMINAL[0]) for n in NOMINAL], color="#555555",
                 lw=1, ls=style, zorder=0, label=name)
    handles, labels = top.get_legend_handles_labels()
    top.legend(handles[-3:], labels[-3:], loc="upper left", ncol=3, frameon=False)
    top.set(xscale="log", yscale="log", ylabel="Time / first-band time",
            title="(a)  Growth relative to the first band")
    top.set_xticks(NOMINAL, labels=[str(n) for n in NOMINAL], minor=False)
    top.minorticks_off()
    method_curves(bottom, list(range(4)), slopes)
    for y in (1, 2):
        bottom.axhline(y, color="#555555", ls="--", lw=.85, zorder=0)
    bottom.set(xticks=range(4), xticklabels=[f"{a}–{b}" for a,b in zip(NOMINAL, NOMINAL[1:])],
               yticks=[1,1.25,1.5,1.75,2], ylim=(.84,2.1), ylabel="Doubling exponent",
               xlabel="Adjacent bands (nominal lengths)", title="(b)  Growth between adjacent bands")
    fig.subplots_adjust(top=.865, bottom=.105, left=.12, right=.98, hspace=.55)
    save(fig, "baseline_growth.pdf")
    return normalized, slopes


def exact_figure(cases, values, timing):
    lengths = sorted({c["n"] for c in cases})
    series = {m: [median(values[c["case_id"], m] / (1000 if timing else n)
                         for c in cases if c["n"] == n) for n in lengths] for m in METHODS}
    fig, ax = plt.subplots(figsize=(6.1, 3.2))
    method_curves(ax, lengths, series)
    ax.set_xscale("log", base=2)
    ax.set_xticks(NOMINAL, labels=NOMINAL)
    ax.set_xlabel("Input length")
    if timing:
        ax.set_yscale("log")
    ax.set_ylabel("Time per sort (µs)" if timing else "Key comparisons per element")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper center", ncol=5, frameon=False,
               columnspacing=1, handlelength=1.5)
    fig.subplots_adjust(top=.86, bottom=.16, left=.115, right=.98)
    save(fig, "baseline_runtime.pdf" if timing else "baseline_comparisons.pdf")


def generate(raw):
    cases = inputs()
    manifest, config, selected, counts, _ = preparation(raw / "preparation", cases)
    times = formal(raw / "formal", cases, manifest, config, selected)
    all_ids = [c["case_id"] for c in cases]
    formal_dir = raw / "formal"
    kinds = Counter()
    with (formal_dir / "records.jsonl").open() as records:
        for line in records:
            kinds[json.loads(line)["kind"]] += 1
    def timestamp(file, key):
        return datetime.fromisoformat(json.loads((formal_dir / file).read_bytes())[key])
    duration = timestamp("complete.json", "end_utc") - timestamp("config.json", "start_utc")
    minutes, seconds = divmod(round(duration.total_seconds()), 60)
    groups = [[c for c in cases if a <= c["n"] <= b] for a,b in BANDS]
    subset = [[c for c in group if c["source"] in {"common", "geometric"}] for group in groups]
    per_band = Counter(c["source"] for c in subset[0])
    assert all(Counter(c["source"] for c in group) == per_band for group in subset)
    def curves(groups):
        return growth_curves(times, [[c["case_id"] for c in group] for group in groups])
    norm, slopes = growth_figure(curves(subset))
    full = {m: vals[-1]/vals[0] for m,vals in curves(groups).items()}
    exact_figure(cases, counts, False)
    exact_figure(cases, times, True)
    warmups = kinds["warmup"] // len(times)
    batches = kinds["sample"] // len(times)
    macros = dict(Inputs=len(cases), MinLength=min(c["n"] for c in cases), MaxLength=max(c["n"] for c in cases),
                  Warmups=warmups, Rounds=batches, First=batches//len(METHODS),
                  Samples=f"{kinds['sample']:,}", Power=kinds["power"], Minutes=minutes, Seconds=seconds,
                  CapExponent=int(math.log2(CANDIDATES[-1])), TargetMs=TARGET_NS//1_000_000,
                  JordanMaxB=max(v[m]["B"] for v in selected.values() for m in METHODS[:2]),
                  Common=per_band["common"], Geometric=per_band["geometric"], PerBand=len(subset[0]),
                  Subset=sum(map(len, subset)), ListLast=f"{slopes[METHODS[0]][-1]:.2f}",
                  TreeMin=f"{min(slopes[METHODS[1]]):.2f}", TreeMax=f"{max(slopes[METHODS[1]]):.2f}",
                  TreeFewerQuick=sum(counts[i,METHODS[1]] < counts[i,METHODS[3]] for i in all_ids),
                  TreeMoreQuick=sum(counts[i,METHODS[1]] > counts[i,METHODS[3]] for i in all_ids),
                  MaxSensitivity=f"{max(abs(full[m]/norm[m][-1]-1) for m in METHODS)*100:.1f}")
    assert all(counts[i,METHODS[0]] > counts[i,m] for i in all_ids for m in METHODS[2:4])
    assert all(counts[i,METHODS[1]] > counts[i,METHODS[2]] for i in all_ids)
    for j, jname in zip(METHODS[:2], ("List","Tree")):
        for m, mname in zip(METHODS[2:4], ("Merge","Quick")):
            ratios = [times[i,j]/times[i,m] for i in all_ids]
            macros[jname+mname] = f"{median(ratios):.1f}"
            macros[jname+mname+"Wins"] = sum(r < 1 for r in ratios)
            assert min(ratios) > 1
    for m, name in zip(METHODS, ("List","Tree","Merge","Quick","Builtin")):
        macros[name+"Growth"] = f"{norm[m][-1]:.2f}"
        macros[name+"AllGrowth"] = f"{full[m]:.2f}"
    path = ROOT / "thesis/generated/baseline_comparison.tex"
    path.write_text("% Generated by docs/thesis/baseline_comparison_revision_20261120/generate.py\n"
                    + "".join(r"\newcommand{\Baseline" + k + "}{" + str(v) + "}\n" for k,v in macros.items()))


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 8.5, "axes.titlelocation": "left", "axes.titlesize": 9, "pdf.fonttype": 42})
    with TemporaryDirectory() as temp, tarfile.open(ARCHIVE / "raw_records.tar.gz") as archive:
        archive.extractall(temp, filter="data")
        generate(Path(temp))
