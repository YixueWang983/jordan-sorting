"""Read-only data and preservation checks for the November 2 text refinement."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    preservation = read(HERE / "preservation.json")
    baseline = preservation["baseline"]
    paths = subprocess.check_output([
        "git", "ls-tree", "-r", "--name-only", baseline, "src", "experiments", "tests",
        "docs/validation", "docs/thesis/unified_results_20261101", "thesis/appendix",
        "thesis/figures", "thesis/generated", "output/pdf", "thesis/bibliography.bib"
    ], cwd=ROOT, text=True).splitlines()
    hashes = {p: digest(ROOT / p) for p in paths}
    aggregate = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert len(paths) == preservation["covered_paths"]
    assert aggregate == preservation["path_sha256_map_digest"]
    for p in paths:
        # Git's content comparison also binds the initial preservation snapshot
        # to the baseline, rather than only comparing two current hash maps.
        if p in preservation["explicit_hashes"]:
            assert (ROOT / p).read_bytes() == subprocess.check_output(["git", "show", baseline + ":" + p], cwd=ROOT)
    protected_prefixes = ("src/", "experiments/", "tests/", "docs/validation/",
                          "docs/thesis/unified_results_20261101/", "thesis/appendix/", "thesis/figures/")
    changed = subprocess.check_output(["git", "diff", "--name-only", baseline], cwd=ROOT, text=True).splitlines()
    assert not [p for p in changed if p.startswith(protected_prefixes)]
    facts = read(HERE / "derived.json")
    provenance = read(HERE / "provenance.json")
    for p, sha in provenance["inputs"].items():
        assert digest(ROOT / p) == sha, p
    assert digest(HERE / "generate.py") == provenance["script_sha256"]
    cases = read(ROOT / "docs/validation/unified_formal_20261101/unified_analysis_bca4c1c6_restart_20261101_01/cases.json")
    for source, d in facts["source_endpoints"].items():
        rows = [c for c in cases if c["source"] == source]
        for point in d["by_length"]:
            ratios = [c["ratio"] for c in rows if c["n"] == point["n"]]
            assert len(ratios) == point["inputs"]
            assert float(np.median(ratios)) == point["median"]
        assert d["largest"]["median"] < d["smallest"]["median"]
    comparison = facts["constructor_comparison"]
    shortest = min(cases, key=lambda c: c["tree_median_ns"])
    assert shortest["case_id"] == comparison["shortest_tree_case"]
    assert shortest["tree_median_ns"] == comparison["shortest_tree_median_ns"]
    ctor = read(ROOT / "docs/validation/unified_followup_20261101/results/analysis/constructor_summary.json")
    percent = 100 * ctor["paired_difference_ns"]["median"] / shortest["tree_median_ns"]
    assert percent == comparison["percent_of_shortest_tree_median"]
    assert facts["macros"]["UnifiedCtorShortestPercent"] == f"{percent:.2f}"
    macro_text = (ROOT / "thesis/generated/unified_refinement.tex").read_text()
    for name, value in facts["macros"].items():
        assert f"\\newcommand{{\\{name}}}{{{value}}}" in macro_text
    thesis = ROOT / "thesis"
    tex = "\n".join(p.read_text() for p in thesis.rglob("*.tex") if "build" not in p.parts)
    labels = re.findall(r"\\label\{([^}]+)\}", tex)
    refs = [key for keys in re.findall(r"\\(?:[Cc]ref|ref|pageref)\{([^}]+)\}", tex) for key in keys.split(",")]
    assert len(labels) == len(set(labels)) and not set(refs) - set(labels)
    body = "\n".join(p.read_text() for area in ("chapters", "frontmatter") for p in (thesis / area).glob("*.tex"))
    assert not re.search(r"\b(frozen|v2|matched|post-review)\b|access hooks", body, re.I)
    abstract = (thesis / "frontmatter/abstract.tex").read_text().split("In a paired experiment", 1)[1]
    assert not re.search(r"\d|restart|attempt|therefore", abstract)
    for f in ("introduction.tex", "results.tex", "conclusion.tex"):
        assert not re.search(r"restart|no-retry", (thesis / "chapters" / f).read_text(), re.I)
    results = (thesis / "chapters/results.tex").read_text()
    assert results.count(r"\begin{figure}[htbp]") == 3
    assert results.count(r"\begin{table}[htbp]") == 4
    assert "[H]" not in results and "Summary of Observations" in results
    build = thesis / "build/refinement-20261102"
    log = (build / "main.log").read_text()
    assert not re.search(r"Warning|Overfull|Underfull|undefined|Missing character", log)
    assert not re.search(r"WARN|ERROR", (build / "main.blg").read_text())
    report = dict(baseline=baseline, passed=True, new_measurements_executed=False,
                  preserved_baseline_files=len(paths), preserved_path_map_digest=aggregate,
                  appendix_A_and_B_unchanged=True, original_PDF_preserved=True,
                  source_endpoint_medians_independently_verified=True,
                  constructor_percentage_independently_verified=percent,
                  generated_macros_and_references_verified=True,
                  result_float_placement="htbp for all three figures and four tables",
                  compile_warnings=0, undefined_references=0, overfull_boxes=0, underfull_boxes=0)
    (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
