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
# Legend order follows the comparison from the two Jordan backends to the baselines.
STYLES = {
    METHODS[1]: ("Jordan · finger tree", "#2876b5", "o"),
    METHODS[0]: ("Jordan · Python lists", "#c65320", "s"),
    METHODS[2]: ("Merge sort (Python)", "#288454", "^"),
    METHODS[3]: ("Quicksort (Python)", "#704bc2", "v"),
    METHODS[4]: ("sorted() (C, Timsort)", "#6c7f96", "D"),
}


def growth_curves(times, groups):
    return {m: [median(times[i,m] for i in ids) for ids in groups] for m in METHODS}


def growth_figure(series):
    normalized = {m: [t / vals[0] for t in vals] for m, vals in series.items()}
    slopes = {m: [math.log2(b/a) for a,b in zip(vals, vals[1:])] for m, vals in series.items()}
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.45, 3.42))
    steps = range(len(NOMINAL) - 1)
    for method, (label, color, marker) in STYLES.items():
        style = dict(label=label, color=color, marker=marker, ms=3.8, lw=1.5)
        left.plot(NOMINAL, normalized[method], **style)
        right.plot(steps, slopes[method], **style)
    for ax in (left, right):
        ax.grid(alpha=.22, linewidth=.6)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=8)

    left.set(xscale="log", yscale="log", xlim=(28, 690), ylim=(.82, 64),
             xlabel="Nominal input length", ylabel="Time / median time at 32–33",
             title="(a)  Growth of median sort time")
    left.set_xticks(NOMINAL, labels=NOMINAL)
    ticks = [1, 2, 4, 8, 16, 32, 64]
    left.set_yticks(ticks, labels=ticks)
    left.minorticks_off()
    for fn, style in ((lambda n: n, "--"), (lambda n: n*math.log2(n), "--"),
                      (lambda n: n*n, ":")):
        left.plot(NOMINAL, [fn(n)/fn(NOMINAL[0]) for n in NOMINAL],
                  color="#898989", lw=.9, ls=style, zorder=1)
    for x, y, label in ((552, 14, "$n$"), (442, 36, "$n\\,\\log_2 n$"), (225, 53, "$n^2$")):
        left.text(x, y, label, fontsize=7.4, color="#626262")
    left.legend(loc="upper left", fontsize=7.1, frameon=False, handlelength=1.6,
                borderaxespad=.35, labelspacing=.35)

    right.set(xticks=list(steps), xticklabels=[f"{a}→{b}" for a,b in zip(NOMINAL, NOMINAL[1:])],
              xlim=(-.18, 3.58), ylim=(.6, 2.2), yticks=[.6,.8,1,1.2,1.4,1.6,1.8,2,2.2],
              xlabel="Nominal size step", ylabel="Doubling exponent",
              title="(b)  Growth exponent per doubling")
    for value, label in ((1, "linear"), (2, "quadratic")):
        right.axhline(value, color="#757575", linestyle=":" if value == 2 else "--", lw=.85, zorder=1)
        right.annotate(label, xy=(3.54, value), xytext=(0, 3),
                       textcoords="offset points", ha="right",
                       va="bottom", fontsize=7.2, color="#555555")
    fig.subplots_adjust(left=.08, right=.985, bottom=.17, top=.905, wspace=.32)
    fig.savefig(FIGURES / "baseline_growth.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    return normalized, slopes


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
