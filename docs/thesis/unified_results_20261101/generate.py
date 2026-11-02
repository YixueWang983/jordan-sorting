"""Read archived observations and generate manuscript numbers, tables and figures.

No sorter is imported or run. Archived inputs/outputs are read only. All
regenerated assets live in thesis/generated or thesis/figures, outside archives.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import statistics as st
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
THESIS = ROOT / "thesis"
GEN = THESIS / "generated"
FIG = THESIS / "figures"
ARCH = ROOT / "docs/validation/unified_formal_20261101"
ANA = ARCH / "unified_analysis_bca4c1c6_restart_20261101_01"
FORMAL = ARCH / "unified_formal_bca4c1c6_restart_20261101_01"
FOLLOW = ROOT / "docs/validation/unified_followup_20261101"
PREFLIGHT = ROOT / "docs/validation/unified_preflight_20261101"
SOURCES = ["common", "targeted_split", "structural", "geometric", "seeded"]
LABELS = dict(zip(SOURCES, ["Common", "Targeted", "Structural", "Geometric", "Seeded"]))
COLORS = dict(zip(SOURCES, ["#3366AA", "#DD9933", "#AA3377", "#228866", "#7755AA"]))
MARKERS = dict(zip(SOURCES, ["o", "^", "s", "D", "v"]))
BACKENDS = ["ordinary_list", "heterogeneous_finger_uninstrumented"]
INPUTS = {}


def read(path):
    path = Path(path)
    blob = path.read_bytes()
    INPUTS[str(path.relative_to(ROOT))] = hashlib.sha256(blob).hexdigest()
    return json.loads(gzip.decompress(blob) if path.suffix == ".gz" else blob)


def summary(rows):
    r = [x["ratio"] for x in rows]
    return dict(inputs=len(r), wins=sum(x < 1 for x in r), median=st.median(r),
                minimum=min(r), maximum=max(r))


def f(x):
    return f"{x:.3f}"


def interval(d):
    return f"{f(d['minimum'])}--{f(d['maximum'])}"


def rows_file(name, rows):
    (GEN / f"unified_{name}.tex").write_text(
        "% Generated from archived records by docs/thesis/unified_results_20261101/generate.py\n"
        + f"\\newcommand{{\\Unified{name.capitalize()}Rows}}{{%\n"
        + "\n".join(" & ".join(map(str, row)) + r"\\%" for row in rows) + "\n}\n")


def save(fig, name):
    fig.savefig(FIG / f"unified_{name}.pdf", bbox_inches="tight",
                metadata={"Creator": "Archived Jordan sorting results; generate.py",
                          "CreationDate": None, "ModDate": None})
    plt.close(fig)


def baseline(ax):
    ax.axhline(1, color="0.25", lw=.8, ls="--", zorder=0)
    ax.grid(axis="y", color=".9", lw=.5)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_ylabel("Tree / list median time")


def scatter(ax, rows, x):
    for source in SOURCES:
        rr = [r for r in rows if r["source"] == source]
        ax.scatter([x(r) for r in rr], [r["ratio"] for r in rr],
                   s=14, alpha=.7, c=COLORS[source], marker=MARKERS[source],
                   linewidths=.35, label=LABELS[source])


def main():
    GEN.mkdir(exist_ok=True)
    cases = read(ANA / "cases.json")
    archive_summary = read(ANA / "summary.json")
    suite = read(ROOT / "docs/validation/input_suite_registry_20261101/suite.json")
    config = read(FORMAL / "config.json")
    read(FORMAL / "manifest.json")
    env = read(FORMAL / "environment.json")
    ctor = read(FOLLOW / "results/analysis/constructor_summary.json")
    stability = read(FOLLOW / "results/analysis/stability_summary.json")
    follow_plan = read(FOLLOW / "protocol.json")
    # Reconstruct formal medians from the original batches before using the
    # independently archived analysis. This reads data; it does not run sorting.
    total_sample_calls = total_batches = 0
    for r in cases:
        records = [read(p) for p in sorted((FORMAL / "sources" / r["source"] /
                   "jobs" / r["case_id"] / "records").glob("*.json.gz"))]
        assert records, r["case_id"]
        for backend in BACKENDS:
            samples = [x for x in records if x["kind"] == "sample" and x["backend"] == backend]
            assert len(samples) == 20
            times = [x["elapsed_ns"] / x["batch_size"] for x in samples]
            assert st.median(times) == r["groups"][backend]["median_ns_per_call"]
            total_batches += len(samples)
            total_sample_calls += sum(x["batch_size"] for x in samples)
        assert r["ratio"] == r["tree_median_ns"] / r["list_median_ns"]
    overall = summary(cases)
    assert overall["median"] == archive_summary["overall"]["median"]
    assert overall["wins"] == archive_summary["overall"]["tree_faster"]
    bins = [("32/33", [32, 33]), ("64--70", [64, 65, 70]),
            ("128/129", [128, 129]), ("256/257", [256, 257]), ("512/513", [512, 513])]
    sizes = {name: summary([r for r in cases if r["n"] in nn]) for name, nn in bins}
    rows_file("sizes", [[name, d["inputs"], d["wins"], f(d["median"]), interval(d)]
                        for name, d in sizes.items()])
    common = []
    for category, label in [("strict_flat", "Strict-flat"), ("low_nesting_valid", "Low"),
                            ("medium_nesting_valid", "Medium"), ("nested_heavy_valid", "Heavy")]:
        rr = [r for r in cases if r["source"] == "common" and r["category"] == category]
        d = summary(rr)
        common.append([label, d["inputs"], d["wins"], f(d["median"]), interval(d),
                       sum(r["S_i"] for r in rr), sum(r["I_i"] for r in rr)])
    rows_file("common", common)
    structural = []
    for shape in ["balanced", "skew", "repeated"]:
        rr = [r for r in cases if r["source"] == "structural" and r["shape"] == shape]
        d = summary(rr)
        structural.append([shape.capitalize(), d["inputs"], d["wins"], f(d["median"]), interval(d)])
    rows_file("structural", structural)
    source_rows, structure_rows, frequency_rows = [], [], []
    for source in SOURCES:
        d = archive_summary["per_source"][source]
        t, q = d["timing"], d["structure"]
        assert d["formal_status"] == "COMPLETE"
        source_rows.append([LABELS[source], d["registered"], d["duplicates"], d["canonical_inputs"],
                            q["inputs"], t["inputs"], t["tree_faster"], f(t["median"]), interval(t)])
        small = [x for r in cases if r["source"] == source for x in r["smaller_sides"]]
        assert dict(Counter(small)) == {int(k): v for k, v in q["smaller_side_histogram"].items()}
        structure_rows.append([LABELS[source], q["inputs"], q["splits"], q["interior_splits"],
                               q["inputs_with_interior_split"], q["inputs_with_no_split"],
                               "NA" if not small else f"{min(small)}/{st.median(small):g}/{max(small)}"])
    rows_file("sources", source_rows)
    rows_file("structure", structure_rows)
    all_k = sorted({k for r in cases for k in r["smaller_sides"]})
    for k in all_k:
        frequency_rows.append([k] + [archive_summary["per_source"][s]["structure"]["smaller_side_histogram"].get(str(k), 0)
                                    for s in SOURCES])
    rows_file("frequencies", frequency_rows)
    # Historical numbers come from their original saved observations.
    old_ratios = []
    for job in sorted((ROOT / "docs/validation/final_review_formal_20261015/formal_common/jobs").iterdir()):
        d = read(job / "summary.json")
        old_ratios.append(d["result"]["tree_over_list_median"])
    diag = read(ROOT / "docs/validation/thesis_review_round2_20261020/local_supplement_recheck.json")
    drops = [x["drop_percent"] for x in diag["diagnostic_cases"]]
    heavy = [r for r in cases if r["source"] == "common" and r["category"] == "nested_heavy_valid"]
    assert max(r["S_i"] for r in heavy) == 1 and not any(r["I_i"] for r in heavy)
    near = [r["case_id"] for r in cases if abs(r["ratio"] - 1) < .02]
    variability = {b: dict(median=st.median([100*r['groups'][b]['iqr_ns_per_call']/r['groups'][b]['median_ns_per_call'] for r in cases]),
                          maximum=max(100*r['groups'][b]['iqr_ns_per_call']/r['groups'][b]['median_ns_per_call'] for r in cases))
                   for b in BACKENDS}
    macros = dict(UnifiedN=len(cases), UnifiedWins=overall["wins"], UnifiedListWins=len(cases)-overall["wins"],
                  UnifiedMedian=f(overall["median"]), UnifiedMinimum=f(overall["minimum"]),
                  UnifiedMaximum=f(overall["maximum"]), UnifiedNear= len(near),
                  UnifiedExcluded=len(suite["exclusions"]), UnifiedMaxN=max(r["n"] for r in cases),
                  UnifiedNoSplit=sum(r["S_i"] == 0 for r in cases), UnifiedBatches=total_batches,
                  UnifiedCalls=total_sample_calls, UnifiedHeavyN=len(heavy), UnifiedHeavyWins=sum(r["ratio"] < 1 for r in heavy),
                  UnifiedHeavyZero=sum(r["S_i"] == 0 for r in heavy),
                  UnifiedGeometricSmallMax=archive_summary["per_source"]["geometric"]["structure"]["smaller_side_max"],
                  UnifiedCtorInstrumented=f(ctor["per_configuration"]["instrumented"]["median"]/1000),
                  UnifiedCtorUninstrumented=f(ctor["per_configuration"]["uninstrumented"]["median"]/1000),
                  UnifiedCtorDifference=f(ctor["paired_difference_ns"]["median"]/1000),
                  UnifiedStabilityN=stability["overall"]["inputs"],
                  UnifiedStabilitySame=stability["overall"]["same_direction"],
                  UnifiedStabilityMedian=f(stability["overall"]["absolute_relative_change_percent"]["median"]),
                  UnifiedStabilityMaximum=f(stability["overall"]["absolute_relative_change_percent"]["maximum"]),
                  OldCommonN=len(old_ratios), OldCommonMedian=f(st.median(old_ratios)),
                  OldDiagnosticN=len(drops), OldDiagnosticDropLow=f"{min(drops):.1f}", OldDiagnosticDropHigh=f"{max(drops):.1f}",
                  UnifiedListIQRMedian=f(variability[BACKENDS[0]]["median"]),
                  UnifiedTreeIQRMedian=f(variability[BACKENDS[1]]["median"]),
                  UnifiedListIQRMax=f(variability[BACKENDS[0]]["maximum"]),
                  UnifiedTreeIQRMax=f(variability[BACKENDS[1]]["maximum"]))
    for source in SOURCES:
        macros['Unified'+LABELS[source]+'N'] = archive_summary['per_source'][source]['timing']['inputs']
    macros.update(UnifiedWarmups=config['rules']['warmups_per_backend'],
                  UnifiedRounds=config['rules']['repetitions'])
    assert all(r > 1 for r in old_ratios)
    (GEN / "unified_numbers.tex").write_text("% Generated; see docs/thesis/unified_results_20261101/generate.py\n" +
        "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k,v in macros.items()) +
        "".join(f"\\input{{generated/unified_{name}}}\n" for name in
                ('sizes','common','structural','sources','structure','frequencies')))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
                         "axes.labelsize": 9, "legend.fontsize": 8, "pdf.fonttype": 42,
                         "axes.linewidth": .6, "xtick.labelsize": 8, "ytick.labelsize": 8})
    edges = np.arange(.55, 1.550001, .05)
    counts, _ = np.histogram([r["ratio"] for r in cases], bins=edges)
    assert int(counts.sum()) == len(cases)
    fig, ax = plt.subplots(figsize=(6.4, 3.0), layout="constrained")
    ax.hist([r["ratio"] for r in cases], bins=edges, color="#3366AA", edgecolor="white", linewidth=.5)
    ax.axvline(1, color=".2", ls="--", lw=1)
    ax.set(xlabel="Tree / list median time", ylabel="Number of inputs", xlim=(.55,1.55))
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(.03,.96,f"{len(cases)} inputs\n{overall['wins']} tree-faster inputs", transform=ax.transAxes, va="top")
    save(fig, "distribution")

    fig = plt.figure(figsize=(6.8, 3.8), layout="constrained")
    gs = fig.add_gridspec(2, 1, height_ratios=[3.2, 1.1])
    ax = fig.add_subplot(gs[0]); scatter(ax, cases, lambda r: r["n"]); baseline(ax)
    for source in SOURCES:
        ns = sorted({r["n"] for r in cases if r["source"] == source})
        ax.plot(ns, [st.median([r["ratio"] for r in cases if r["source"] == source and r["n"] == n]) for n in ns],
                color=COLORS[source], lw=.9, alpha=.9)
    ax.set_xscale("log", base=2)
    ax.set_xticks([32,64,128,256,512], ["32","64","128","256","512"])
    ax.set(xlabel="Input length n", ylim=(.55,1.59), xlim=(29,570))
    ax.legend(loc="lower left", ncol=2, frameon=False)
    tax = fig.add_subplot(gs[1]);tax.axis("off")
    ns = sorted({r["n"] for r in cases})
    cells = [[LABELS[s]]+[str(sum(r["source"]==s and r["n"]==n for r in cases)) for n in ns] for s in SOURCES]
    tab=tax.table(cellText=cells,colLabels=["Inputs at n"]+list(map(str,ns)),
                  loc="center",cellLoc="center",colWidths=[.20]+[.80/len(ns)]*len(ns))
    tab.auto_set_font_size(False);tab.set_fontsize(8.2)
    for (i,j),cell in tab.get_celld().items():
        cell.set_edgecolor(".85");cell.set_linewidth(.3)
        if j==0 and i>0: cell.get_text().set_color(COLORS[SOURCES[i-1]])
    save(fig, "ratio_by_n")

    fig, (left,right)=plt.subplots(1,2,figsize=(7.2,4.05),sharey=True,layout="constrained")
    family=[r for r in cases if r["construction_family"]=="values_for"]
    ns=sorted({r["n"] for r in family})
    ncolors=dict(zip(ns,["#3366AA","#6F92BB","#A95F12","#D59B4C","#7D3975","#B67BAF"]))
    for n in ns:
        for shape,marker in [("targeted","o"),("balanced","^"),("skew","s")]:
            for mirror in (False,True):
                rr=[r for r in family if r["n"]==n and r["shape"]==shape and r["mirror"]==mirror]
                if rr:
                    left.scatter([r["smaller_side_k"] for r in rr],[r["ratio"] for r in rr],
                                 s=27,marker=marker,edgecolors=ncolors[n],linewidths=.8,
                                 facecolors="none" if mirror else ncolors[n])
    baseline(left);left.set_xscale("log");left.set_xticks([1,3,7,19,30,62,126],["1","3","7","19","30","62","126"])
    left.set(xlabel="Smaller-side parameter k",title="(a) One construction family",ylim=(.55,1.60))
    left.legend(handles=[Line2D([],[],color=ncolors[n],marker="o",ls="",label=f"n = {n}") for n in ns],
                loc="upper center",ncol=2,fontsize=8.5,frameon=False,columnspacing=.7,handletextpad=.3)
    valid=[r for r in cases if r["p_i"] is not None]
    scatter(right,valid,lambda r:r["p_i"]);baseline(right)
    right.set(xlabel=r"Two-sided split fraction $p_i$",ylabel="",title=f"(b) Split frequency\nS = 0: {len(cases)-len(valid)} inputs omitted",ylim=(.55,1.60))
    right.legend(loc="lower right",frameon=False,fontsize=8.5)
    save(fig,"split_panels")
    # A paper-sized layout of the predetermined overview. The archive keeps
    # the original PDF; input order and all values are checked unchanged.
    order=read(ANA / 'overview_order.json')
    by_id={r['case_id']:r for r in cases}
    ordered=[by_id[x['case_id']] for x in order]
    positions={x['case_id']:x['index'] for x in order}
    assert len(ordered)==len(cases) and set(positions.values())==set(range(1,len(cases)+1))
    fig,ax=plt.subplots(figsize=(6.6,3.3),layout='constrained')
    scatter(ax,ordered,lambda r:positions[r['case_id']]);baseline(ax)
    ax.set(xlabel='Input index (source, length, case ID)',ylim=(.55,1.60))
    ax.legend(loc='lower left',ncol=2,frameon=False)
    save(fig,'overview')
    derived=dict(overall=overall,size_bins=sizes,near_one_case_ids=near,macros=macros,
                 histogram=dict(edges=edges.tolist(),counts=counts.tolist(),supplementary=True),
                 variability_percent=variability,
                 graph_inputs=dict(overview=[dict(index=positions[r['case_id']],case_id=r['case_id'],ratio=r['ratio']) for r in ordered],
                     ratio_by_n=[{k:r[k] for k in ('case_id','source','n','ratio')} for r in cases],
                     values_for=[{k:r[k] for k in ('case_id','n','shape','mirror','smaller_side_k','ratio')} for r in family],
                     split_fraction=[{k:r[k] for k in ('case_id','source','S_i','I_i','p_i','ratio')} for r in cases]))
    (HERE / "derived.json").write_text(json.dumps(derived,indent=2)+"\n")
    (HERE / "provenance.json").write_text(json.dumps(dict(
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        inputs={k:v for k,v in INPUTS.items() if '/records/' not in k},
        raw_records_read=sum('/records/' in k for k in INPUTS),
        raw_record_sha256_map_digest=hashlib.sha256(json.dumps(
            {k:v for k,v in INPUTS.items() if '/records/' in k},sort_keys=True).encode()).hexdigest(),
        raw_formal_batches_recomputed=total_batches,sorter_executed=False,
        notes=["Histogram and 2% band are post hoc descriptive additions.",
               "Raw archives and the four original figures are unchanged.",
               "Manuscript figures preserve each observation and use revised layout only."]),indent=2)+"\n")
    print(json.dumps(dict(overall=overall,near_one=len(near),batches=total_batches,calls=total_sample_calls)))


if __name__ == "__main__":
    main()
