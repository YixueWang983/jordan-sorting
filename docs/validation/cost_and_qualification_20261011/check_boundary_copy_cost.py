"""Observe insertion list lengths, not wall-clock sorting performance."""
import argparse, csv, json, sys, hashlib
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser()
p.add_argument('--repo',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
sys.path.insert(0,str(a.repo/'src'))
from paper_jordan_sort import paper_jordan_sort_valid
from sibling_list_backend import OrdinarySiblingListBackend
orig_insert=OrdinarySiblingListBackend.insert_at_boundary
orig_split=OrdinarySiblingListBackend.split_pairs_at_value
rows=[]
for n in [4,8,16,32,64,128,256,512]:
 for direction in ['increasing','decreasing']:
  counts={'boundary_insertions':0,'existing_ids_copied':0,'split_calls':0}
  def observe_insert(self,pair_id,anchor_pair_id,side):
   anchor=self.get_pair(anchor_pair_id)
   counts['boundary_insertions']+=1
   counts['existing_ids_copied']+=len(self.get_list(anchor.sibling_list_id).pair_ids)
   return orig_insert(self,pair_id,anchor_pair_id,side)
  def observe_split(self,*args,**kwargs):
   counts['split_calls']+=1
   return orig_split(self,*args,**kwargs)
  values=list(range(1,n+1))
  if direction=='decreasing': values.reverse()
  with patch.object(OrdinarySiblingListBackend,'insert_at_boundary',observe_insert),patch.object(OrdinarySiblingListBackend,'split_pairs_at_value',observe_split):
   result=paper_jordan_sort_valid(values,execution_mode='minimal')
  formula=(n//2-1)**2
  if not(result==sorted(values) and counts['existing_ids_copied']==formula and counts['split_calls']==0):
   raise RuntimeError((n,direction,counts))
  rows.append(dict(n=n,direction=direction,**counts,formula=formula,output_ok=True))
a.output.mkdir(parents=True,exist_ok=False)
with (a.output/'counts.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
record=dict(cases=len(rows),all_passed=True,mode='minimal',
 method='Sum lengths observed before original boundary insertion; source copies each such list. No interpreter copy instrumentation or timing.',
 source_sha256={str(x.relative_to(a.repo)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted((a.repo/'src').glob('*.py'))})
(a.output/'record.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),all_passed=True)))
