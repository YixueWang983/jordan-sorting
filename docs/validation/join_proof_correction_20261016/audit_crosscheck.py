from pathlib import Path
import csv,gzip,hashlib,json,re,statistics,subprocess
R=Path(__file__).resolve().parents[3]
D=R/'docs/validation/join_proof_correction_20261016'
A=R/'docs/validation/final_review_formal_20261015'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def q(v,p):
 v=sorted(v);at=(len(v)-1)*p;i=int(at);j=min(i+1,len(v)-1)
 return v[i]+(v[j]-v[i])*(at-i)
report={'scope':'read_only_saved_evidence_and_thesis_numeric_crosscheck','archives':{},'datasets':{}}
for name in ['common_qualification_v2_20261015','split_trace_followup_20261015','id_lifecycle_calibration_20261015','final_review_formal_20261015']:
 root=R/'docs/validation'/name;manifest=read(root/'SHA256SUMS.json')
 for p,h in manifest.items():assert sha(root/p)==h,(name,p)
 report['archives'][name]={'verified_files':len(manifest),'manifest_sha256':sha(root/'SHA256SUMS.json')}
summary=read(A/'formal_analysis.json')
rows=list(csv.DictReader((A/'formal_case_statistics.csv').open()))
tex=(R/'thesis/chapters/results.tex').read_text()
for name,dirname,reportname in [('common','formal_common','formal_common_readonly.json'),('targeted_split','formal_targeted_split','formal_targeted_readonly.json')]:
 v=read(D/reportname);old=read(A/(dirname+'_validation.json'))
 assert v==old,(name,'read-only reports differ')
 assert v['archive_valid'] and v['complete'] and v['stage']=='formal'
 counts=dict(sample_batches=0,sample_calls=0,warmup_batches=0,warmup_calls=0,sample_batches_below_10ms=0,measured_sample_ns=0)
 for p in (A/dirname/'jobs').glob('*/records/*.json.gz'):
  r=json.loads(gzip.decompress(p.read_bytes()));kind=r['kind']
  assert r['status']=='PASS'
  counts[kind+'_batches']+=1;counts[kind+'_calls']+=r['completed_calls']
  if kind=='sample':
   counts['sample_batches_below_10ms']+=r['elapsed_ns']<10_000_000
   counts['measured_sample_ns']+=r['elapsed_ns']
 s=summary[name];assert counts==s['counts']
 ratios=[x['tree_over_list_median'] for x in v['statistics'].values()]
 for k,p in [('min',0),('q25',.25),('median',.5),('q75',.75),('max',1)]:
  assert abs(q(ratios,p)-s['ratio'][k])<1e-12
 assert min(ratios)>1
 selected=[r for r in rows if r['dataset']==name]
 assert len(selected)==len(ratios)==s['inputs']
 for r in selected:
  st=v['statistics'][r['case']]
  assert abs(float(r['ratio'])-st['tree_over_list_median'])<1e-12
  for b in ['ordinary_list','heterogeneous_finger']:
   assert float(r[b+'_ms'])==st['groups'][b]['median_ns_per_call']/1e6
   assert float(r[b+'_iqr_ms'])==st['groups'][b]['iqr_ns_per_call']/1e6
 groups=s['groups']['n' if name=='common' else 'stratum']
 for k,g in groups.items():
  expected=f"{k.removeprefix('k')} & {g['inputs']} & {g['ordinary_list_median_ms']:.3f} & {g['heterogeneous_finger_median_ms']:.3f} & {g['ratio']['median']:.3f}"
  assert expected in tex,expected
 report['datasets'][name]={'counts':counts,'inputs':len(ratios),'ratios':s['ratio'],'rounded_table_rows':len(groups),'readonly_report_exactly_matches_archived':True}
# Include the stratum table's four descriptive rows.
strata=summary['common']['groups']['stratum']
for name,label in [('strict_flat','Strict-flat'),('low_nesting_valid','Low nesting'),('medium_nesting_valid','Medium nesting'),('nested_heavy_valid','Heavy nesting')]:
 g=strata[name];ratio=g['ratio']
 assert f"{label} & {g['inputs']} & {ratio['median']:.3f} & {ratio['min']:.3f}--{ratio['max']:.3f}" in tex
report['stratum_rows_checked']=4
historical=list(csv.DictReader((R/'docs/analysis/week12_runtime_ratios.csv').open()))
hr=[r for r in historical if r['scope']=='size' and r['comparison']=='paper/reference']
assert len(hr)==5
for r in hr:assert f"{float(r['median_ratio']):.3f}" in tex
report['historical_ratio_cells_checked']=5
# No source mutation; compare file hashes with the frozen revision, not just HEAD trees.
paths=subprocess.check_output(['git','ls-tree','-r','--name-only','ce0148b','src','tests','experiments','data','results'],cwd=R,text=True).splitlines()
for p in paths:
 old=subprocess.check_output(['git','show','ce0148b:'+p],cwd=R)
 assert hashlib.sha256(old).hexdigest()==sha(R/p),p
report['frozen_tracked_files_unchanged']=len(paths)
proof='docs/development/finger_final_review_20261015.md'
old=subprocess.check_output(['git','show','ce0148b:'+proof],cwd=R)
report['proof_binding']={'old_commit':subprocess.check_output(['git','rev-parse','ce0148b'],cwd=R,text=True).strip(),'old_sha256':hashlib.sha256(old).hexdigest(),'corrected_sha256':sha(R/proof),'old_receipt_unchanged':True}
report['current_thesis_table_rows_checked']=17
(D/'crosscheck_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
