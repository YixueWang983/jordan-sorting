"""Independently rebuild all input medians and descriptive rerun summaries."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics

from committed_records import read_records
from common_qualification_v2_protocol import frozen_selection
from split_qualification_protocol import split_selection
from validate_matched_measurement import validate
from uninstrumented_protocol import BACKENDS


def r7(values,p):
    ordered=sorted(values);x=(len(ordered)-1)*p;i=int(x);fraction=x-i
    return ordered[i]+fraction*(ordered[min(i+1,len(ordered)-1)]-ordered[i])


def aggregate(rows):
    ratios=[r['ratio'] for r in rows]
    return dict(inputs=len(rows),list_ms=statistics.median(r['list_ms'] for r in rows),
                tree_ms=statistics.median(r['tree_ms'] for r in rows),
                ratio_min=min(ratios),ratio_q25=r7(ratios,.25),ratio_median=statistics.median(ratios),
                ratio_q75=r7(ratios,.75),ratio_max=max(ratios),tree_faster=sum(r<1 for r in ratios))


def analyze(qualification,calibration,formal,output):
    all_rows=[];summaries={};reports={}
    for dataset,selection in (('common',frozen_selection()),('targeted_split',split_selection())):
        report=validate(formal/dataset,qualification=qualification/dataset,calibration=calibration/dataset)
        if not report['complete'] or report.get('configuration')!='uninstrumented' or report['stage']!='formal':
            raise ValueError('complete uninstrumented formal archives required')
        rows=[];counts=dict(sample_batches=0,sample_calls=0,warmup_calls=0,sample_elapsed_ns=0,batches_below_10ms=0)
        for case in selection['cases']:
            spec=case['spec'];cid=spec['case'];batch=report['batch_sizes'][cid]
            records=read_records(formal/dataset/'jobs'/cid);groups={}
            row=dict(dataset=dataset,case=cid,n=spec['n'],category=spec['requested_category'],
                     mirror=spec['mirror'],k=spec.get('k'),batch_size=batch)
            for name,short in zip(BACKENDS,('list','tree')):
                samples=[r for r in records if r['kind']=='sample' and r['backend']==name]
                if len(samples)!=20:raise ValueError('missing input batches')
                values=[r['elapsed_ns']/r['completed_calls'] for r in samples]
                med=statistics.median(values);lo=r7(values,.25);hi=r7(values,.75)
                rebuilt=dict(batches=20,median_ns_per_call=med,q25_ns_per_call=lo,q75_ns_per_call=hi,iqr_ns_per_call=hi-lo)
                expected=report['statistics'][cid]['groups'][name]
                if any(not math.isclose(rebuilt[k],expected[k],rel_tol=1e-12,abs_tol=1e-8) for k in rebuilt):
                    raise ValueError('independent summary disagrees with archive validator')
                row.update({short+'_ms':med/1e6,short+'_q25_ms':lo/1e6,short+'_q75_ms':hi/1e6,short+'_relative_iqr':(hi-lo)/med})
                groups[name]=med
            row['ratio']=groups[BACKENDS[1]]/groups[BACKENDS[0]]
            if not math.isclose(row['ratio'],report['statistics'][cid]['tree_over_list_median'],rel_tol=1e-12):
                raise ValueError('paired ratio mismatch')
            for r in records:
                if r['status']!='PASS':raise ValueError('failed formal record')
                if r['kind']=='sample':
                    counts['sample_batches']+=1;counts['sample_calls']+=r['completed_calls']
                    counts['sample_elapsed_ns']+=r['elapsed_ns'];counts['batches_below_10ms']+=r['elapsed_ns']<10_000_000
                else:counts['warmup_calls']+=r['completed_calls']
            rows.append(row)
        summaries[dataset]=dict(overall=aggregate(rows),accounting=counts,
            by_length={str(n):aggregate([r for r in rows if r['n']==n]) for n in sorted({r['n'] for r in rows})},
            by_category={c:aggregate([r for r in rows if r['category']==c]) for c in sorted({r['category'] for r in rows})},
            maximum_relative_iqr=max(r[s+'_relative_iqr'] for r in rows for s in ('list','tree')))
        all_rows.extend(rows);reports[dataset]=report
    output.mkdir(parents=True,exist_ok=False)
    for name,value in [('summary',summaries),('cases',all_rows),('validation',reports)]:
        (output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    with (output/'cases.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(all_rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(all_rows)
    (output/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},indent=2)+'\n')
    return summaries


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('qualification','calibration','formal','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(analyze(a.qualification,a.calibration,a.formal,a.output),indent=2))
