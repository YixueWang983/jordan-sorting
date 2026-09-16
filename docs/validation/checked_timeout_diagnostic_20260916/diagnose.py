import sys,json,time,signal,hashlib,platform
from pathlib import Path
from collections import defaultdict
repo=Path('/Users/schnee/Codex/2026-06-05/files-mentioned-by-the-user-thesis/jordan-sorting')
out=Path(__file__).parent
sys.path.insert(0,str(repo/'src'))
import paper_jordan as pj
import paper_jordan_sort as ps
from oracle import oracle
from sibling_list_backend import OrdinarySiblingListBackend as Backend
casepath=repo/'results/validation_runs/ordinary_list_extended_correctness_v1__run001/cases/incremental_valid_n513_005.json'
case=json.loads(casepath.read_text()); seq=case['sequence']
report={'case_id':case['case_id'],'case_file_sha256':hashlib.sha256(casepath.read_bytes()).hexdigest(),'python':sys.version,'platform':platform.platform(),'budget_seconds':180,'source_sha256':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((repo/'src').glob('*.py'))},'purpose':'Single-input instrumented resource diagnosis; NOT a sorting benchmark; historical archive unchanged.'}
cert=oracle(seq);assert cert['valid']; expected=cert['sorted']
report['oracle_valid']=True
stats=defaultdict(lambda:{'calls':0,'inclusive_seconds':0.0,'exclusive_seconds':0.0})
stack=[]; progress=[]; started=time.perf_counter()
def save():
 report.update(elapsed_seconds=time.perf_counter()-started,stats=dict(stats),prefix_progress=progress,active_stack=[f[0] for f in stack])
 (out/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
def wrap(name,fn):
 def wrapped(*args,**kwargs):
  start=time.perf_counter(); frame=[name,0.0];stack.append(frame);stats[name]['calls']+=1
  try:return fn(*args,**kwargs)
  finally:
   elapsed=time.perf_counter()-start;stats[name]['inclusive_seconds']+=elapsed;stats[name]['exclusive_seconds']+=elapsed-frame[1];stack.pop()
   if stack:stack[-1][1]+=elapsed
 return wrapped
pj._validate_state_against_deterministic_replay=wrap('deterministic_replay',pj._validate_state_against_deterministic_replay)
Backend.validate_invariants=wrap('backend_invariants',Backend.validate_invariants)
original=wrap('full_state_validation',ps.validate_paper_jordan_state)
def callback(state):
 report['active_prefix']=state.processed_count
 original(state)
 report['last_completed_prefix']=state.processed_count
 if state.processed_count%32==0 or state.processed_count==len(seq):
  progress.append({'prefix':state.processed_count,'elapsed_seconds':time.perf_counter()-started});save();print(progress[-1],flush=True)
ps.validate_paper_jordan_state=callback
class BudgetExpired(Exception):pass
def expired(*args):raise BudgetExpired('180-second diagnostic budget expired')
signal.signal(signal.SIGALRM,expired);signal.alarm(180)
try:
 result=ps.paper_jordan_diagnostics_valid(seq)
 report['checked_status']='PASS' if result['output']==expected and result['invariants_valid'] else 'FAIL'
 report['checked_output_matches_oracle']=result['output']==expected
except BudgetExpired as exc:report['checked_status']='TIMEOUT';report['reason']=str(exc)
except Exception as exc:report['checked_status']='ERROR';report['reason']=repr(exc)
finally:signal.alarm(0);save()
print(json.dumps({'status':report['checked_status'],'elapsed_seconds':report['elapsed_seconds'],'stats':dict(stats)}),flush=True)
