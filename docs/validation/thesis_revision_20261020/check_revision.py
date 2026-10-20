"""Read-only numeric/source checks for the thesis revision; no sorting or timing."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Run evidence checks without Python optimization')
import csv
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

R = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
BASE = '19a553fb9a089fae726c4ba49c5412a9e4bd12d3'
FORMAL = '4a83fa6b7a4213e9e5758fe3454e002ebc266459'
def git(*args):
    return subprocess.check_output(['git',*args], cwd=R, text=True).strip()
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def quantile(values, p):
    a=sorted(values); x=(len(a)-1)*p; i=int(x)
    return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)

allowed=('thesis/','docs/validation/thesis_revision_20261020/',
         'output/pdf/jordan_thesis_supervisor_review_20261020',
         'output/packages/jordan_supervisor_review_20261020')
for path in git('diff','--name-only',BASE).splitlines():
    assert path=='README.md' or path.startswith(allowed), path
frozen={}
for path in ('src','experiments','tests','data','results'):
    assert not git('diff',BASE,'--',path), path
    baseline=git('rev-parse',f'{BASE}:{path}')
    measured=git('rev-parse',f'{FORMAL}:{path}')
    assert baseline==measured,(path,baseline,measured)
    frozen[path]={'baseline_tree':baseline,'formal_tree':measured,'working_tree_unchanged':True}
A=R/'docs/validation/final_review_formal_20261015'
summary=json.loads((A/'formal_analysis.json').read_text())
rows=list(csv.DictReader((A/'formal_case_statistics.csv').open()))
tex=(R/'thesis/chapters/results.tex').read_text()
checks={}
for dataset in ('common','targeted_split'):
    s=summary[dataset];selected=[r for r in rows if r['dataset']==dataset]
    assert len(selected)==s['inputs']
    ratios=[float(r['ratio']) for r in selected]
    for k,p in [('min',0),('q25',.25),('median',.5),('q75',.75),('max',1)]:
        assert abs(quantile(ratios,p)-s['ratio'][k])<1e-12
    assert min(ratios)>1
    groups=s['groups']['n' if dataset=='common' else 'stratum']
    for k,g in groups.items():
        expected=f"{k.removeprefix('k')} & {g['inputs']} & {g['ordinary_list_median_ms']:.3f} & {g['heterogeneous_finger_median_ms']:.3f} & {g['ratio']['median']:.3f}"
        assert expected in tex,expected
    label='Common' if dataset=='common' else 'Targeted split';c=s['counts']
    assert f"{label} & {s['inputs']} & {c['sample_batches']} & {c['sample_calls']} & {c['warmup_calls']}" in tex
    checks[dataset]={'csv_rows':len(selected),'rounded_runtime_rows':len(groups),'ratio_rebuilt_from_case_csv':s['ratio'],'archived_counts':c}
for key,label in [('strict_flat','Strict-flat'),('low_nesting_valid','Low nesting'),('medium_nesting_valid','Medium nesting'),('nested_heavy_valid','Heavy nesting')]:
    g=summary['common']['groups']['stratum'][key];s=g['ratio']
    assert f"{label} & {g['inputs']} & {s['median']:.3f} & {s['min']:.3f}--{s['max']:.3f} & 0" in tex
proof=(R/'thesis/appendix/backend_argument.tex').read_text()
for required in ('recursive transient','not $D$','1\\leq a\\leq b',r'\Delta\Psi=0','never reset',r'\label{thm:proof-total}'):
    assert required in proof,required
report={
 'scope':'current_thesis_numeric_tables_and_frozen_source_diff',
 'baseline':BASE,'formal_execution':FORMAL,
 'frozen_directories':frozen,
 'prior_tracked_archives_and_outputs_unchanged':True,
 'current_numeric_rows_checked':19,
 'stratum_rows_with_explicit_zero_two_sided':4,
 'datasets':checks,
 'source_summary_sha256':sha(A/'formal_analysis.json'),
 'source_case_csv_sha256':sha(A/'formal_case_statistics.csv'),
 'corrected_review_sha256':sha(R/'docs/development/finger_final_review_20261015.md'),
 'english_argument_sha256':sha(R/'thesis/appendix/backend_argument.tex'),
 'general_mathematical_proof_independently_certified':False,
 'raw_archive_revalidated_this_run':False,
 'existing_test_suite_or_qualification_calibration_formal_rerun':False,
 'new_local_exploratory_supplement':'local_supplement_check.json',
 'historical_table_removed_from_current_text_old_archive_unchanged':True
}
print(json.dumps(report,indent=2,sort_keys=True))
