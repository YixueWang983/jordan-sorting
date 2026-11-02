"""Independent manuscript data/preservation audit; does not execute sorting."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASELINE = "7006629fa93a43001ce32c73f9446be90ba15ba8"


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def read(p):
    return json.loads((ROOT / p).read_text())


def original(path):
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)


def main():
    report = {"baseline": BASELINE, "sorter_executed": False, "checks": {}}
    preserved = []
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASELINE,
                                    "src", "experiments", "tests", "output/pdf"], cwd=ROOT, text=True).splitlines()
    for p in paths + ["thesis/appendix/backend_argument.tex", "thesis/appendix/claim_traceability.tex",
                      "thesis/appendix/ai_reflection.tex", "thesis/bibliography.bib"]:
        assert (ROOT / p).read_bytes() == original(p), p
        preserved.append(p)
    report["checks"]["unchanged_source_and_historical_files"] = len(preserved)
    report["appendix_A_sha256"] = digest((ROOT / "thesis/appendix/backend_argument.tex").read_bytes())
    before = original("thesis/appendix/ai_documentation.tex").decode()
    expected = before.replace(
        r"Appendix~\ref{app:backend-argument}, Table~\ref{tab:results-hooks} and related discussion",
        r"Appendix~\ref{app:backend-argument} and the archived diagnostic indexed in Section~\ref{sec:appendix-external-review}")
    assert (ROOT / "thesis/appendix/ai_documentation.tex").read_text() == expected
    report["checks"]["appendix_B_only_removed_table_reference_repaired"] = True
    archive_checks = {}
    for name in ("unified_preflight_20261101", "unified_formal_20261101", "unified_followup_20261101"):
        root = ROOT / "docs/validation" / name
        manifest = json.loads((root / "package_manifest.json").read_text())
        assert (root / "package_manifest.json").read_bytes() == original(str((root / "package_manifest.json").relative_to(ROOT)))
        for rel, sha in manifest.items():
            assert digest((root / rel).read_bytes()) == sha, str(root / rel)
        archive_checks[name] = len(manifest)
    report["checks"]["archive_files_match_original_manifests"] = archive_checks
    analysis = "docs/validation/unified_formal_20261101/unified_analysis_bca4c1c6_restart_20261101_01/"
    cases = read(analysis + "cases.json")
    source_summary = read(analysis + "summary.json")
    derived = read("docs/thesis/unified_results_20261101/derived.json")
    ratios = np.array([c["ratio"] for c in cases])
    assert len(cases) == len({c['case_id'] for c in cases}) == 302
    assert int(np.sum(ratios < 1)) == derived['overall']['wins'] == 44
    assert np.median(ratios) == derived['overall']['median']
    assert ratios.min() == derived['overall']['minimum'] and ratios.max() == derived['overall']['maximum']
    assert [c['case_id'] for c in cases if abs(c['ratio']-1)<.02] == derived['near_one_case_ids']
    bins = {'32/33': [32,33], '64--70': [64,65,70], '128/129': [128,129],
            '256/257': [256,257], '512/513': [512,513]}
    for label, ns in bins.items():
        r = np.array([c['ratio'] for c in cases if c['n'] in ns]); d = derived['size_bins'][label]
        assert (len(r), int(np.sum(r<1)),np.median(r),r.min(),r.max()) == tuple(d[k] for k in ('inputs','wins','median','minimum','maximum'))
    for source, d in source_summary['per_source'].items():
        cc=[c for c in cases if c['source']==source]
        assert len(cc) == d['registered'] == d['canonical_inputs'] == d['timing']['inputs'] == d['structure']['inputs']
        assert d['duplicates'] == 0
        assert sum(c['S_i'] for c in cc) == d['structure']['splits']
        assert sum(c['I_i'] for c in cc) == d['structure']['interior_splits']
        assert Counter(k for c in cc for k in c['smaller_sides']) == {int(k): v for k,v in d['structure']['smaller_side_histogram'].items()}
        for c in cc:
            assert c['p_i'] == (c['I_i']/c['S_i'] if c['S_i'] else None)
    hist=np.histogram(ratios,bins=derived['histogram']['edges'])[0]
    assert list(hist) == derived['histogram']['counts'] and sum(hist)==302
    assert len(derived['graph_inputs']['ratio_by_n']) == len(derived['graph_inputs']['split_fraction']) == 302
    assert len(derived['graph_inputs']['values_for']) == 24
    order=read(analysis+'overview_order.json')
    by_id={c['case_id']:c for c in cases}
    assert derived['graph_inputs']['overview']==[dict(index=x['index'],case_id=x['case_id'],ratio=by_id[x['case_id']]['ratio']) for x in order]
    provenance=read('docs/thesis/unified_results_20261101/provenance.json')
    for p,sha in provenance['inputs'].items():
        assert digest((ROOT/p).read_bytes())==sha,p
    assert provenance['script_sha256']==digest((HERE/'generate.py').read_bytes())
    report['checks']['numbers_graph_inputs_and_sources_reconciled']=True
    body_paths=list((ROOT/'thesis/chapters').glob('*.tex'))+list((ROOT/'thesis/frontmatter').glob('*.tex'))
    body='\n'.join(p.read_text() for p in body_paths)
    assert not re.search(r'\b(frozen|v2|matched|post-review)\b|access hooks',body,re.I)
    assert not re.search(r'(?<![A-Za-z0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?![A-Za-z0-9])',body)
    assert 'tab:results-hooks' not in '\n'.join(p.read_text() for p in (ROOT/'thesis').rglob('*.tex') if 'build' not in p.parts)
    result_text=(ROOT/'thesis/chapters/results.tex').read_text()
    assert result_text.count(r'\begin{figure}')==3
    tex='\n'.join(p.read_text() for p in (ROOT/'thesis').rglob('*.tex') if 'build' not in p.parts)
    labels=re.findall(r'\\label\{([^}]+)\}',tex)
    refs=[k for s in re.findall(r'\\(?:[Cc]ref|ref|pageref)\{([^}]+)\}',tex) for k in s.split(',')]
    assert len(labels)==len(set(labels))
    assert not set(refs)-set(labels)
    report['checks']['terminology_labels_and_three_main_result_figures']=True
    report['passed']=True
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
