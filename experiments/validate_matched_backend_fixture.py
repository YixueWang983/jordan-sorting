"""Rebuild fixture evidence from raw rows; never grant permission for timing."""
import argparse
import hashlib
import json
from pathlib import Path

from matched_backend_fixture import SCHEMA, PROTOCOL, BACKENDS, canonical, digest, identity, source_identity
from oracle import oracle


def require(condition,message):
    if not condition: raise ValueError(message)


def validate(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    expected_files={'config.json','environment.json','raw.jsonl','summary.json'}
    require(set(manifest)==expected_files,'manifest file set changed')
    for name,value in manifest.items():
        require(hashlib.sha256((directory/name).read_bytes()).hexdigest()==value,'file hash mismatch: '+name)
    config=json.loads((directory/'config.json').read_text())
    environment=json.loads((directory/'environment.json').read_text())
    summary=json.loads((directory/'summary.json').read_text())
    require(config['schema']==SCHEMA and canonical(config['protocol'])==canonical(PROTOCOL),'protocol or stage changed')
    require(canonical(config['backends'])==canonical({name:identity(name) for name in BACKENDS}),'explicit backend configuration changed')
    require(environment['source_sha256']==source_identity(),'source content differs from this validator')
    require(environment['measurement_kind']=='synthetic_ticks','fixture is not a timing run')
    cases=config['inputs']; require(1<=len(cases)<=8,'case count invalid')
    lookup={}; hashes=set(); plan=[]
    # Deliberately reconstruct the schedule independently of runner.actions.
    for i,case in enumerate(cases):
        values=case['values']; cid=f'case-{i:02d}'
        require(case['case']==cid and type(values) is list and 3<=len(values)<=64,'case identity or size changed')
        require(all(type(x) is int for x in values),'noninteger input')
        require(case['sha256']==digest(values) and case['sha256'] not in hashes,'input hash or uniqueness failure')
        hashes.add(case['sha256']); lookup[cid]=case
        plan.append((cid,'input',None,None))
        plan.extend((cid,'qualification',name,None) for name in BACKENDS)
        for kind,count in (('warmup',1),('sample',2)):
            for rep in range(count):
                for name in (BACKENDS if (i+rep)%2==0 else BACKENDS[::-1]):
                    plan.append((cid,kind,name,rep))
    rows=[json.loads(line) for line in (directory/'raw.jsonl').read_text().splitlines()]
    require(0<len(rows)<=len(plan),'missing or extra rows')
    rebuilt={name:{'samples':0,'passed_samples':0,'sample_synthetic_ticks':0} for name in BACKENDS}
    failed=False
    for index,row in enumerate(rows):
        require(canonical((row['case'],row['kind'],row['backend'],row['round']))==canonical(plan[index]),'row order, duplicate or missing row')
        case=lookup[row['case']]; name=row['backend']; values=case['values']
        require(row['input_sha256']==case['sha256'],'row input changed')
        require(canonical(row['backend_identity'])==canonical(identity(name) if name else None),'row backend identity changed')
        require(row['status'] in ('PASS','ERROR'),'invalid status')
        if row['status']=='ERROR':
            require(index==len(rows)-1,'execution continued after an error')
            require(type(row['error']) is dict and bool(row['error'].get('type')) and 'message' in row['error'],'error detail missing')
            failed=True
        else:
            require(row['error'] is None,'success with error detail')
            if row['kind']=='input':
                require(len(set(values))==len(values) and oracle(values)['valid'],'illegal input accepted')
            else:
                require(type(row['output']) is list and all(type(x) is int for x in row['output']) and
                        row['output']==sorted(values),'wrong output accepted')
                if row['kind']=='qualification':
                    require(row['processed_count']==len(values) and row['same_backend_replay'] is True,'qualification incomplete')
        if row['kind'] in ('warmup','sample'):
            require(type(row.get('synthetic_ticks')) is int and row['synthetic_ticks']==1,'synthetic boundary ticks changed')
        else:
            require('synthetic_ticks' not in row,'qualification or oracle placed inside measurement')
        if row['kind']=='sample':
            rebuilt[name]['samples']+=1
            rebuilt[name]['passed_samples']+=row['status']=='PASS'
            rebuilt[name]['sample_synthetic_ticks']+=row['synthetic_ticks']
    success=not failed and len(rows)==len(plan)
    require(failed or success,'successful archive has an incomplete schedule')
    require(canonical(summary)==canonical({'schema':SCHEMA,'completed_successfully':success,'source_unchanged':True,
                      'performance_eligible':False,'rows':len(rows),'planned_rows':len(plan),'summary':rebuilt}),'summary cannot be rebuilt')
    return {'archive_valid':True,'completed_successfully':success,'performance_eligible':False,
            'source_verified':True,'rows':len(rows),'inputs':len(cases),'summary_rebuilt':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    print(json.dumps(validate(p.parse_args().directory),indent=2))
