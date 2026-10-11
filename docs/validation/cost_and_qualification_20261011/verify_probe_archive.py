"""Read-only archive integrity and recorded qualification checks, not a replay."""
import argparse, hashlib, json
from collections import Counter
from pathlib import Path

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def require(condition,message):
 if not condition: raise ValueError(message)

def verify(root, repo):
 manifest_count=0
 for file in [root/'manifest.json', *sorted(root.glob('n*/manifest.json'))]:
  record=read(file)['files']; base=file.parent
  actual={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and p!=file}
  require(set(record)==actual,f'file set mismatch: {file}')
  for name,digest in record.items(): require(sha(base/name)==digest,f'hash mismatch: {name}')
  manifest_count+=len(record)
 config=read(root/'campaign_config.json'); summary=read(root/'campaign_summary.json')
 provenance=read(root/'campaign_provenance.json')
 for name,digest in provenance['source_sha256'].items():
  require(sha(repo/name)==digest,f'source mismatch: {name}')
 rows=[];identities=set(); budgets=[]
 for batch in config['batches']:
  n=batch['plan'][0]['n']; folder=root/f'n{n}'
  require(read(folder/'config.json')==batch,f'configuration mismatch: {n}')
  subprov=read(folder/'provenance.json')
  require(subprov['source_sha256']==provenance['source_sha256'],f'provenance mismatch: {n}')
  subrows=[]
  for spec in batch['plan']:
   row=read(folder/'cases'/f"{spec['case_id']}.json")
   for key,value in spec.items(): require(row[key]==value,f'case identity mismatch: {key}')
   if 'sequence' in row:
    seq=row['sequence']; digest=hashlib.sha256(json.dumps(seq,separators=(',',':')).encode()).hexdigest()
    require(digest==row['sequence_sha256'],'input hash mismatch')
    require(len(seq)==n and sorted(seq)==list(range(1,n+1)),'rank input mismatch')
    require(digest not in identities,'duplicate rank input');identities.add(digest)
   if row['status']=='PASS':
    expected=hashlib.sha256(json.dumps(sorted(seq),separators=(',',':')).encode()).hexdigest()
    require(expected==row['expected_sha256'],'expected output hash mismatch')
    require(row['certification']['valid'] is True and row['modes_equal'] is True,'certification/mode failure')
    for mode in ['checked','minimal']:
     require(row['mode_calls'][mode]=='COMPLETED',f'incomplete {mode}')
     require(row[mode]['passed'] is True and all(row[mode]['checks'].values()),f'failed {mode}')
     require(row[mode]['output_sha256']==expected,f'wrong {mode} output identity')
    require(row['checked']['processed_count']==n and row['checked']['invariants_valid'] is True,'state failure')
   require(row.get('worker_resource_wall_seconds',0)>=0,'negative resource wall time')
   subrows.append(row);rows.append(row)
  sub=read(folder/'summary.json')
  require(sub['passed']==sum(r['status']=='PASS' for r in subrows),'batch count mismatch')
  require(sub['source_unchanged'] is True,'changed batch source')
  budgets.append(sub['resource_wall_seconds'])
 require(summary['status_counts']==dict(Counter(r['status'] for r in rows)),'campaign count mismatch')
 require(summary['recorded']==len(rows) and summary['planned']==sum(len(b['plan']) for b in config['batches']),'planned/recorded mismatch')
 require(summary['source_unchanged'] is True,'changed campaign source')
 return dict(status='PASS', archive_entries_checked=manifest_count, recorded_cases=len(rows), unique_rank_inputs=len(identities),
             status_counts=summary['status_counts'],resource_wall_seconds=sum(budgets),
             verification_scope='File and source hashes, frozen configuration, recorded input/output identities and audit status. Does not rerun checked/replay or prove universal correctness.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--repo',type=Path,required=True)
 a=p.parse_args();print(json.dumps(verify(a.archive,a.repo),indent=2))
