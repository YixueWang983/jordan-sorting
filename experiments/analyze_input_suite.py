"""Descriptive analysis and four figures from independently verified raw records."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics

from committed_records import read_records
from input_suite_registry import load_suite, canonical_cases, SOURCE_ORDER
from qualify_common_inputs import read
from validate_input_suite_run import validate, dependencies
from uninstrumented_protocol import BACKENDS


def ratio_summary(rows):
    values = [r["ratio"] for r in rows]
    return dict(inputs=len(values), tree_faster=sum(x < 1 for x in values),
                ties=sum(x == 1 for x in values),
                median=statistics.median(values) if values else None,
                minimum=min(values) if values else None, maximum=max(values) if values else None)


def structure_summary(rows):
    small = [k for r in rows for k in r["smaller_sides"]]
    return dict(inputs=len(rows), splits=sum(r["S_i"] for r in rows),
                interior_splits=sum(r["I_i"] for r in rows),
                inputs_with_interior_split=sum(r["I_i"] > 0 for r in rows),
                inputs_with_no_split=sum(r["S_i"] == 0 for r in rows),
                smaller_side_histogram={str(k): n for k, n in sorted(Counter(small).items())},
                smaller_side_min=min(small) if small else None,
                smaller_side_median=statistics.median(small) if small else None,
                smaller_side_max=max(small) if small else None)


def summarize(suite, timing, structures, statuses):
    per_source = {}
    for source in SOURCE_ORDER:
        members = [e for e in suite["entries"] if e["source"] == source]
        canonical = canonical_cases(suite, source)
        timed = [r for r in timing if r["source"] == source]
        qualified = [r for r in structures if r["source"] == source]
        per_source[source] = dict(registered=len(members), canonical_inputs=len(canonical),
                                  duplicates=len(members) - len(canonical),
                                  formal_status=statuses[source],
                                  timing=ratio_summary(timed), structure=structure_summary(qualified))
    strata = {}
    for source, field in (("common", "category"), ("structural", "shape")):
        labels = sorted({e[field] for e in suite["entries"] if e["source"] == source and e[field] is not None})
        strata[source] = {label: dict(
            timing=ratio_summary([r for r in timing if r["source"] == source and r[field] == label]),
            structure=structure_summary([r for r in structures if r["source"] == source and r[field] == label]))
            for label in labels}
    return dict(scope="descriptive_only_no_independent_sample_or_causal_inference",
                suite_sha256=suite["suite_sha256"], registered_entries=len(suite["entries"]),
                excluded_entries=len(suite["exclusions"]), actual_timed_inputs=len(timing),
                overall=ratio_summary(timing), overall_ratio_role="secondary_composition_dependent",
                timed_source_composition={s: sum(r["source"] == s for r in timing) for s in SOURCE_ORDER},
                per_source=per_source, strata=strata)


def metadata(entry):
    return {k: entry[k] for k in ("case_id", "source", "n", "category", "shape",
                                  "construction_family", "smaller_side_k", "mirror")}


def r7(values, p):
    ordered = sorted(values)
    x = (len(ordered) - 1) * p
    lo = int(x)
    return ordered[lo] + (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]) * (x - lo)


def raw_timing(job, expected):
    rows = read_records(job)
    groups = {}
    for name in BACKENDS:
        values = [r["elapsed_ns"] / r["batch_size"] for r in rows
                  if r["kind"] == "sample" and r["backend"] == name]
        if len(values) != 20:
            raise ValueError("analysis requires all twenty paired batches")
        groups[name] = dict(batches=20, median_ns_per_call=statistics.median(values),
                            q25_ns_per_call=r7(values, .25), q75_ns_per_call=r7(values, .75),
                            iqr_ns_per_call=r7(values, .75) - r7(values, .25))
        for key, value in groups[name].items():
            if abs(value - expected["groups"][name][key]) > max(1e-8, abs(value) * 1e-12):
                raise ValueError("independent batch statistics disagree")
    ratio = groups[BACKENDS[1]]["median_ns_per_call"] / groups[BACKENDS[0]]["median_ns_per_call"]
    if abs(ratio - expected["tree_over_list_median"]) > max(1e-12, abs(ratio) * 1e-12):
        raise ValueError("independent ratio disagrees")
    return dict(ratio=ratio, list_median_ns=groups[BACKENDS[0]]["median_ns_per_call"],
                tree_median_ns=groups[BACKENDS[1]]["median_ns_per_call"], groups=groups)


def figures(timing, output, summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = dict(zip(SOURCE_ORDER, ("#3366AA", "#DD9933", "#AA3377", "#228866", "#7755AA")))
    files = []
    def save(fig, name):
        fig.tight_layout()
        for ext in ("png", "pdf"):
            path = output / (name + "." + ext)
            fig.savefig(path, dpi=180, bbox_inches="tight")
            files.append(path.name)
        plt.close(fig)
    def baseline(ax):
        ax.axhline(1, color="#555555", linewidth=.8, linestyle="--")
        ax.set_ylabel("Tree / list median time")
        ax.grid(alpha=.15)
    def scatter_sources(ax, x, rows):
        for source in SOURCE_ORDER:
            selected = [r for r in rows if r["source"] == source]
            if selected:
                ax.scatter([x(r) for r in selected], [r["ratio"] for r in selected],
                           color=colors[source], s=18, alpha=.65, label=f"{source} (n={len(selected)})")
    ordered = sorted(timing, key=lambda r: (SOURCE_ORDER.index(r["source"]), r["n"], r["case_id"]))
    positions = {r["case_id"]: i + 1 for i, r in enumerate(ordered)}
    fig, ax = plt.subplots(figsize=(10, 4.5))
    scatter_sources(ax, lambda r: positions[r["case_id"]], ordered)
    baseline(ax)
    ax.set_xlabel("Canonical input index (source, size, case ID)")
    ax.set_title(f"Measured: {len(timing)}; registered: {summary['registered_entries']}; "
                 f"canonical: {summary['canonical_inputs']}")
    if timing:
        ax.legend(fontsize=8)
    save(fig, "overview")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    scatter_sources(ax, lambda r: r["n"], timing)
    for source in SOURCE_ORDER:
        bins = defaultdict(list)
        for r in timing:
            if r["source"] == source:
                bins[r["n"]].append(r["ratio"])
        if bins:
            xs = sorted(bins)
            ax.plot(xs, [statistics.median(bins[n]) for n in xs], color=colors[source], linewidth=1)
            for n in xs:
                ax.annotate(str(len(bins[n])), (n, statistics.median(bins[n])), fontsize=6, xytext=(0, 4),
                            textcoords="offset points")
    baseline(ax)
    ax.set_xlabel("Input length n (labels give inputs per source/size)")
    ax.set_title("Discrete per-source medians; connecting lines are descriptive")
    if timing:
        ax.set_xscale("log", base=2)
        ax.legend(fontsize=8)
    save(fig, "ratio_by_n")

    family = [r for r in timing if r["construction_family"] == "values_for"]
    sizes = sorted({r["n"] for r in family})
    cols = min(3, max(1, len(sizes)))
    rows = max(1, (len(sizes) + cols - 1) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3.4 * rows), squeeze=False)
    for ax, n in zip(axes.flat, sizes):
        for shape, marker in (("targeted", "o"), ("balanced", "^"), ("skew", "s")):
            for mirror in (False, True):
                points = [r for r in family if r["n"] == n and r["shape"] == shape and r["mirror"] == mirror]
                if points:
                    ax.scatter([r["smaller_side_k"] for r in points], [r["ratio"] for r in points],
                               marker=marker, edgecolors=colors[points[0]["source"]],
                               facecolors="none" if mirror else colors[points[0]["source"]],
                               label=shape + (" mirror" if mirror else " original"), s=35)
        baseline(ax)
        ax.set_xscale("log")
        ax.set_xticks([1, 3, 7, 19, 30, 62, 126], labels=["1", "3", "7", "19", "30", "62", "126"])
        ax.tick_params(axis="x", labelsize=7)
        ax.set_title(f"n={n}")
        ax.set_xlabel("Smaller-side parameter k")
        ax.legend(fontsize=6)
    for ax in list(axes.flat)[len(sizes):]:
        ax.set_visible(False)
    fig.suptitle("One construction family, varying parameters; repeated is excluded", fontsize=10)
    save(fig, "values_for_by_k")

    valid = [r for r in timing if r["p_i"] is not None]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    scatter_sources(ax, lambda r: r["p_i"], valid)
    baseline(ax)
    ax.set_xlabel("Two-sided splits / all performed splits")
    ax.set_title(f"One point per input; {len(timing) - len(valid)} inputs have S=0 (p=NA)")
    if valid:
        ax.legend(fontsize=8)
    save(fig, "ratio_by_split_fraction")
    return files


def analyze(formal, output):
    formal, output = Path(formal).resolve(), Path(output)
    if output.exists():
        raise FileExistsError("analysis output must be new")
    cache = {}
    report = validate(formal, cache=cache)
    if report["stage"] != "formal":
        raise ValueError("analysis requires one formal session")
    suite, cfg = load_suite(), read(formal / "config.json")
    deps = dependencies("formal", cfg["prerequisites"], report["environment"], cache=cache)
    timing, structures = [], []
    for source in SOURCE_ORDER:
        qualified = deps["qualification"].get(source, {}).get("structures", {})
        for entry in canonical_cases(suite, source):
            cid = entry["case_id"]
            if cid in qualified:
                structures.append(dict(**metadata(entry), **qualified[cid]))
            if report["sources"][source]["status"] == "COMPLETE":
                if cid not in qualified:
                    raise ValueError("timed input lacks qualified structure evidence")
                rebuilt = raw_timing(formal / "sources" / source / "jobs" / cid,
                                     report["sources"][source]["statistics"][cid])
                timing.append(dict(**metadata(entry), **qualified[cid], **rebuilt))
    summary = summarize(suite, timing, structures, {s: report["sources"][s]["status"] for s in SOURCE_ORDER})
    summary.update(session_complete=report["complete"], all_sources_complete=report["all_sources_complete"],
                   session_hard_error=report["hard_error"],
                   canonical_inputs=len(canonical_cases(suite)))
    output.mkdir(parents=True, exist_ok=False)
    order = sorted(timing, key=lambda r: (SOURCE_ORDER.index(r["source"]), r["n"], r["case_id"]))
    (output / "overview_order.json").write_text(json.dumps(
        [dict(index=i + 1, case_id=r["case_id"], source=r["source"], n=r["n"]) for i, r in enumerate(order)], indent=2) + "\n")
    (output / "execution_statuses.json").write_text(json.dumps(dict(
        formal=report["sources"], qualification=deps["qualification"]), indent=2) + "\n")
    (output / "membership.json").write_text(json.dumps(
        [{k: e[k] for k in ("case_id", "source", "canonical_case_id", "duplicate_of", "membership_status")}
         for e in suite["entries"]], indent=2) + "\n")
    for name, value in (("summary", summary), ("cases", timing), ("qualified_structure", structures)):
        (output / (name + ".json")).write_text(json.dumps(value, indent=2) + "\n")
    fields = ["case_id", "source", "n", "category", "shape", "construction_family", "smaller_side_k",
              "mirror", "S_i", "I_i", "p_i", "ratio", "list_median_ns", "tree_median_ns"]
    with (output / "cases.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(timing)
    files = figures(timing, output, summary)
    captions = dict(
        overview="All complete-source inputs, one ratio each; missing/incomplete sources remain in the source table.",
        ratio_by_n="Counts label source/size medians; no trend fitting or complexity inference.",
        values_for_by_k="Same values_for construction; n, mirror and shape shown separately; repeated omitted. Parameter, size, parity and mirror coverage are unbalanced.",
        ratio_by_split_fraction="One point per input; S=0 yields NA, not zero. No causal interpretation.")
    (output / "figures.json").write_text(json.dumps(dict(files=files, captions=captions), indent=2) + "\n")
    (output / "manifest.json").write_text(json.dumps(
        {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--formal", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(analyze(a.formal, a.output), indent=2))
