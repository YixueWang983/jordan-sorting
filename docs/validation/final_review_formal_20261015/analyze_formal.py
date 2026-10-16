"""Rebuild descriptive formal tables from already validated immutable records.

Run with the same Python runtime as the archive; no sorting is executed.
This supplements, and does not replace, validate_matched_measurement.py.
"""
import csv
import gzip
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
NAMES = ('ordinary_list', 'heterogeneous_finger')


def read(path):
    return json.loads(path.read_text())


def quantile(xs, p):
    xs = sorted(xs)
    at = (len(xs)-1)*p
    lo, hi = math.floor(at), math.ceil(at)
    return xs[lo] if lo == hi else xs[lo]*(hi-at)+xs[hi]*(at-lo)


def stats(xs):
    return dict(min=min(xs), q25=quantile(xs, .25), median=statistics.median(xs),
                q75=quantile(xs, .75), max=max(xs))


def main():
    all_rows, reports = [], {}
    for dataset, expected_cases in (('common', 140), ('targeted_split', 12)):
        path = ROOT/f'formal_{dataset}'
        report = read(ROOT/f'formal_{dataset}_validation.json')
        if not (report['archive_valid'] and report['complete'] and report['stage'] == 'formal'):
            raise ValueError('formal archive lacks accepted independent validation')
        cfg = read(path/'config.json')
        totals = dict(sample_batches=0, sample_calls=0, warmup_batches=0,
                      warmup_calls=0, sample_batches_below_10ms=0, measured_sample_ns=0)
        rows = []
        if len(cfg['cases']) != expected_cases:
            raise ValueError('case count')
        for case in cfg['cases']:
            key = case['case']
            batch = cfg['batch_sizes'][key]
            raw = [json.loads(gzip.decompress(p.read_bytes()))
                   for p in sorted((path/'jobs'/key/'records').glob('*.gz'))]
            row = dict(dataset=dataset, case=key, n=len(case['values']), batch=batch)
            row['stratum'] = key.split('-', 2)[1] if dataset == 'common' else 'k'+key.split('-k')[1].split('-')[0]
            for name in NAMES:
                samples = [r for r in raw if r['kind'] == 'sample' and r['backend'] == name]
                warmups = [r for r in raw if r['kind'] == 'warmup' and r['backend'] == name]
                if len(samples) != 20 or len(warmups) != 5:
                    raise ValueError('sample/warmup count')
                values = []
                for record in samples+warmups:
                    if record['status'] != 'PASS' or any(o['output'] != sorted(case['values']) or o['output_diagnostic'] is not None for o in record['outputs']):
                        raise ValueError('record output/status')
                    if len(record['outputs']) != record['completed_calls'] or record['completed_calls'] != record['batch_size']:
                        raise ValueError('call count')
                    kind = record['kind']
                    totals[kind+'_batches'] += 1
                    totals[kind+'_calls'] += record['completed_calls']
                    if kind == 'sample':
                        values.append(record['elapsed_ns']/batch)
                        totals['measured_sample_ns'] += record['elapsed_ns']
                        totals['sample_batches_below_10ms'] += record['elapsed_ns'] < 10_000_000
                median = statistics.median(values)
                iqr = quantile(values, .75)-quantile(values, .25)
                accepted = report['statistics'][key]['groups'][name]
                if median != accepted['median_ns_per_call'] or iqr != accepted['iqr_ns_per_call']:
                    raise ValueError('independent statistics mismatch')
                row[name+'_ms'] = median/1e6
                row[name+'_iqr_ms'] = iqr/1e6
                row[name+'_relative_iqr'] = iqr/median
            row['ratio'] = row[NAMES[1]+'_ms']/row[NAMES[0]+'_ms']
            if not math.isclose(row['ratio'], report['statistics'][key]['tree_over_list_median'], rel_tol=1e-14):
                raise ValueError('ratio mismatch')
            rows.append(row)
        rows.sort(key=lambda x: (x['n'], int(x['stratum'][1:]) if dataset == 'targeted_split' else x['stratum'], x['case']))
        groups = {}
        for dimension in ('n', 'stratum'):
            groups[dimension] = {}
            for group in sorted(set(r[dimension] for r in rows)):
                cell = [r for r in rows if r[dimension] == group]
                groups[dimension][group] = dict(inputs=len(cell), ratio=stats([r['ratio'] for r in cell]),
                    **{name+'_median_ms': statistics.median(r[name+'_ms'] for r in cell) for name in NAMES})
        reports[dataset] = dict(inputs=len(rows), counts=totals,
            ratio=stats([r['ratio'] for r in rows]), groups=groups,
            relative_iqr={name:stats([r[name+'_relative_iqr'] for r in rows]) for name in NAMES},
            source_head=report['source_head'],
            captured_environment=read(path/'environment.json')['execution']['captured_at'])
        all_rows.extend(rows)
    with (ROOT/'formal_case_statistics.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]), lineterminator='\n')
        writer.writeheader();writer.writerows(all_rows)
    (ROOT/'formal_analysis.json').write_text(json.dumps(reports, indent=2)+'\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':11, 'axes.spines.top':False, 'axes.spines.right':False,
                         'pdf.fonttype':42, 'savefig.bbox':'tight'})
    figures = REPO/'thesis/figures'
    common = [r for r in all_rows if r['dataset'] == 'common']
    sizes = sorted({r['n'] for r in common})
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    for name, color, label in zip(NAMES, ('#26718c','#bd593b'), ('Ordinary list','Finger tree')):
        medians = [statistics.median(r[name+'_ms'] for r in common if r['n'] == n) for n in sizes]
        axes[0].plot(range(len(sizes)), medians, 'o-', color=color, label=label, markersize=3)
    axes[0].set(yscale='log', ylabel='Median of input medians (ms/call)', xlabel='Input length n')
    axes[0].set_xticks(range(len(sizes)),sizes,rotation=45);axes[0].legend(frameon=False)
    for idx, n in enumerate(sizes):
        cell = [r for r in common if r['n'] == n]
        offsets = [(j-(len(cell)-1)/2)*.035 for j in range(len(cell))]
        axes[1].scatter([idx+x for x in offsets], [r['ratio'] for r in cell],s=10,color='#26718c',alpha=.7)
        axes[1].plot([idx-.27,idx+.27],[statistics.median(r['ratio'] for r in cell)]*2,color='#bd593b',lw=2)
    axes[1].axhline(1, color='gray',linestyle='--',lw=.8)
    axes[1].set(ylabel='Tree / list: ratio of input medians',xlabel='Input length n')
    axes[1].set_xticks(range(len(sizes)),sizes,rotation=45)
    fig.tight_layout();fig.savefig(figures/'current_formal_common.pdf');fig.savefig(ROOT/'current_formal_common.png',dpi=160);plt.close(fig)
    targeted = [r for r in all_rows if r['dataset'] == 'targeted_split']
    fig, ax = plt.subplots(figsize=(7.4,3))
    labels = [r['case'].replace('split-','').replace('-mirror',' M') for r in targeted]
    ax.plot(range(len(targeted)),[r['ratio'] for r in targeted],'o',color='#26718c',markersize=5)
    ax.axhline(1,color='gray',linestyle='--',lw=.8)
    ax.set(ylabel='Tree / list: ratio of input medians',ylim=(.8,max(r['ratio'] for r in targeted)+.3))
    ax.set_xticks(range(len(targeted)),labels,rotation=40,ha='right')
    fig.tight_layout();fig.savefig(figures/'current_formal_targeted.pdf');fig.savefig(ROOT/'current_formal_targeted.png',dpi=160);plt.close(fig)
    print(json.dumps(reports,indent=2))


if __name__ == '__main__':
    main()
