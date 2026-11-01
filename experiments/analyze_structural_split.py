"""Rebuild the structural extension's coverage and timing tables from archives."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

from committed_records import read_records
from structural_split_protocol import structural_selection, coverage_summary
from validate_common_qualification_v2 import validate as validate_qualification
from validate_matched_measurement import validate as validate_measurement


def analyze(qualification, calibration, formal, output):
    qualification, calibration, formal, output = map(Path, (qualification, calibration, formal, output))
    q = validate_qualification(qualification, historical=True, dataset='structural_split')
    cal = validate_measurement(calibration, qualification=qualification)
    measured = validate_measurement(formal, qualification=qualification, calibration=calibration)
    if not (q['all_selected_qualified'] and cal['complete'] and measured['complete']
            and measured['stage'] == 'formal' and measured['dataset'] == 'structural_split'):
        raise ValueError('all three complete structural archives are required')
    coverage = {(r['case'], r['backend']): coverage_summary(r) for r in q['split_coverage']}
    rows = []
    total = dict(sample_batches=0, measured_calls=0, warmup_batches=0, warmup_calls=0,
                 sample_elapsed_ns=0, warmup_elapsed_ns=0)
    for case in structural_selection()['cases']:
        spec = case['spec']; cid = spec['case']
        left = coverage[cid, 'ordinary_list']; right = coverage[cid, 'heterogeneous_finger']
        if left != right:
            raise ValueError('backend logical workload coverage differs')
        stats = measured['statistics'][cid]
        row = dict(case=cid, n=spec['n'], shape=spec['shape'], mirror=spec['mirror'],
                   batch_size=cal['batch_sizes'][cid],
                   list_ms=stats['groups']['ordinary_list']['median_ns_per_call']/1e6,
                   tree_ms=stats['groups']['heterogeneous_finger']['median_ns_per_call']/1e6,
                   ratio=stats['tree_over_list_median'], **left)
        rows.append(row)
        for record in read_records(formal/'jobs'/cid):
            if record['status'] != 'PASS':
                raise ValueError('failed batch in complete formal archive')
            prefix = 'sample' if record['kind'] == 'sample' else 'warmup'
            total[prefix+'_batches'] += 1
            total['measured_calls' if prefix == 'sample' else 'warmup_calls'] += record['completed_calls']
            total[prefix+'_elapsed_ns'] += record['elapsed_ns']
    def aggregate(items):
        ratios = [r['ratio'] for r in items]
        return dict(inputs=len(items), list_ms=statistics.median(r['list_ms'] for r in items),
                    tree_ms=statistics.median(r['tree_ms'] for r in items),
                    ratio_min=min(ratios), ratio_median=statistics.median(ratios), ratio_max=max(ratios),
                    tree_faster=sum(r < 1 for r in ratios),
                    two_sided_splits=sum(r['two_sided_splits'] for r in items),
                    resplit_previous_output=sum(r['resplit_previous_output'] for r in items))
    summary = dict(dataset='structural_split', input_count=len(rows),
                   producing_head=measured['source_head'], qualification_head=q['source_head'],
                   overall=aggregate(rows),
                   by_shape={shape:aggregate([r for r in rows if r['shape']==shape]) for shape in ('balanced','skew','repeated')},
                   by_length={str(n):aggregate([r for r in rows if r['n']==n]) for n in sorted({r['n'] for r in rows})},
                   accounting=total,
                   coverage_scope='per backend primary qualification traces; measured calls have no detailed traces',
                   timing_scope='separate November campaign; complete sorting calls; dependent constructed inputs')
    output.mkdir(parents=True, exist_ok=False)
    for name, data in [('summary',summary),('cases',rows),('qualification_validation',q),
                       ('calibration_validation',cal),('formal_validation',measured)]:
        (output/(name+'.json')).write_text(json.dumps(data, indent=2)+'\n')
    with (output/'cases.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('qualification','calibration','formal','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(analyze(args.qualification,args.calibration,args.formal,args.output),indent=2))
