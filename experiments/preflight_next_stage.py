"""Bounded non-timing preflight on the current (possibly dirty) source tree.

Reuse the extended validator's isolated workers, certification, full checked
replay, minimal call, external output checks and trace coverage. No benchmark.
"""
import argparse
from collections import Counter
from pathlib import Path
import random
import time

from validate_ordinary_list_extended import (
    ROOT, STOP_ERRORS, bounded_case, git, merge_coverage, read_json, reserve,
    sequence_hash, sha, summarize, write_json,
)


def rank_normalize(values):
    """Only the harness may rank inputs; no expected ranks enter the core."""
    ordered = sorted(set(values))
    rank = {value: i + 1 for i, value in enumerate(ordered)}
    return [rank[value] for value in values]


def block_sequence(n, seed, density):
    """Direct sums of endpoint-bounded, even-size excursions and flat spacers.

    Low uses [1,4,3,2,5,6]; medium uses [1,6,5,4,3,2,7,8].
    Between blocks the
    connector is outside both interiors. An odd tail is a new maximum.
    These are seeded structured constructions, NOT uniform random Jordan inputs.
    Requested density is a construction parameter, not a measured category.
    """
    if n < 6 or density not in ('low', 'medium'):
        raise ValueError('need n >= 6 and low/medium density')
    rng = random.Random(seed)
    width = 6 if density == 'low' else 8
    slots = n // width
    active = max(1, slots // 3) if density == 'low' else slots
    template = [1, 4, 3, 2, 5, 6] if density == 'low' else [1, 6, 5, 4, 3, 2, 7, 8]
    blocks = [list(template) for _ in range(active)]
    blocks += [list(range(1, width + 1)) for _ in range(slots - active)]
    # Reverse plus complement preserves endpoint bounds and varies excursion shape.
    for i in range(active):
        if rng.getrandbits(1):
            blocks[i] = [width + 1 - x for x in reversed(blocks[i])]
    rng.shuffle(blocks)
    values = [width * i + x for i, block in enumerate(blocks) for x in block]
    return values + list(range(len(values) + 1, n + 1))


def config():
    plan = []
    def add(family, n, index=0, sequence=None, reflect=False):
        cid = f'{family}_n{n}_{index}'
        item = dict(case_id=cid, family=family, n=n, seed=20260921+n*100+index,
                    kind='base', base_case_id=None, transform=None,
                    prefix_check=False,
                    sampling='seeded incremental' if family=='incremental_valid' else 'coverage-guided construction')
        if sequence is not None:
            item['fixed_sequence'] = sequence
        plan.append(item)
        if reflect:
            plan.append(dict(item, case_id=cid+'_reflect', kind='derived',
                             base_case_id=cid, transform='min+max-x'))
    for i, values in enumerate([[], [1], [2, 1], [3, 1, 2], [3, 2, 1, 4],
                               [1, 2, 3, 4, 6, 7, 0], [2, 3, 1, 7, 6, 4, 5]]):
        add('fixed', len(values), i, values, reflect=len(values)>=4)
    for n in (16,17,32,33,64,65):
        for family in ('blocks_low', 'blocks_medium', 'incremental_valid'):
            for index in (1,2):
                add(family,n,index,reflect=index==1)
        add('flat_valid',n)
        add('nested_valid',n)
    for n in (128,129,512,513):
        for family in ('blocks_low','blocks_medium','flat_valid'):
            add(family,n,1)
    return dict(schema='next_stage_preflight_v1', plan=sorted(plan,key=lambda x:(x['n'],x['case_id'])),
                case_seconds=120, batch_seconds=420, seed_base=20260921,
                rules='block_sequence v1: even six/eight-point excursions, flat spacers, optional odd maximum tail; no rejection/resampling',
                duplicates='rank-normalize all bases before certification; deduplicate rank sequences including reflections; never replace',
                stop='stop remaining cases after any execution/output/state error or timeout; generation/certification failures retained',
                validation='full checked diagnostics/replay and independent fresh minimal call; external sorted(original) expected; no extra prefix run',
                resource_scope='worker wall budget only, includes generation/certification/audit; NOT sorting timing',
                larger_sizes='512/513 low/medium/flat representatives only; heavy 512/513 and 1024/1025 NOT tested here')


def source_hashes():
    return {str(p.relative_to(ROOT)): sha(p)
            for folder in ('src','experiments','tests')
            for p in sorted((ROOT/folder).glob('*.py'))}


def run(output):
    reserve(output)  # No overwrite, even for an incomplete previous run.
    (output/'cases').mkdir()
    cfg=config()
    write_json(output/'config.json',cfg)  # Freeze BEFORE constructing new inputs.
    provenance=dict(head=git('rev-parse','HEAD'),branch=git('branch','--show-current'),
                    origin_main=git('rev-parse','origin/main'),status=git('status','--short'),
                    source_sha256=source_hashes(),meaning='dirty worktree, NOT a run of HEAD alone')
    write_json(output/'provenance.json',provenance)
    (output/'worktree.patch').write_text(git('diff','--','src','tests','experiments')+'\n')
    rows=[];known={};bases={};stop=None
    start=time.monotonic()
    for original in cfg['plan']:
        spec=dict(original)
        path=output/'cases'/f"{spec['case_id']}.json"
        remaining=cfg['batch_seconds']-(time.monotonic()-start)
        if stop or remaining<=0:
            row=dict(spec,status='NOT_RUN_STOP',reason=stop or 'batch budget exhausted',mode_calls={})
        else:
            if spec['kind']=='base' and spec['family'].startswith('blocks_'):
                spec['fixed_sequence']=block_sequence(spec['n'],spec['seed'],spec['family'].split('_')[1])
            if 'fixed_sequence' in spec:
                spec['fixed_sequence']=rank_normalize(spec['fixed_sequence'])
            # Built-in generators already return permutations of 1..n.
            tick=time.monotonic()
            row=bounded_case(spec,known,bases.get(spec['base_case_id']),path,min(remaining,cfg['case_seconds']))
            row['worker_resource_wall_seconds']=time.monotonic()-tick
            if 'sequence' in row:
                normalized=rank_normalize(row['sequence'])
                if normalized!=row['sequence']:
                    raise RuntimeError('worker did not return a canonical rank sequence')
                bases[spec['case_id']]=row['sequence']
                known.setdefault(sequence_hash(normalized),spec['case_id'])
            if row['status'] in STOP_ERRORS or row['status'] in ('TIMEOUT','RESOURCE_ERROR'):
                stop=f"{spec['case_id']}: {row['status']}"
        write_json(path,row);rows.append(row)
        print(f"{len(rows)}/{len(cfg['plan'])} {spec['case_id']}: {row['status']}",flush=True)
    report=summarize(rows)
    passed=[r for r in rows if r['status']=='PASS']
    report.update(structure_counts=dict(Counter(r['structure']['category'] for r in passed)),
                  sampling_counts=dict(Counter(r['sampling'] for r in passed)),
                  resource_wall_seconds=time.monotonic()-start,
                  source_unchanged=source_hashes()==provenance['source_sha256'],
                  limitation='non-timing, structured finite inputs; replay is same core, not independent algorithm or proof')
    write_json(output/'summary.json',report)
    coverage = merge_coverage(rows)
    # The shared historical merger still describes the former recovery tests.
    # Change only this new report's label; never rewrite archived coverage.
    coverage['limitations'].pop('rollback', None)
    coverage['limitations']['failure_handling'] = (
        'Success traces do not measure injected failures; current abort/no-retry '
        'regressions cover failure handling. The core has no rollback contract.')
    write_json(output/'coverage.json',coverage)
    write_json(output/'manifest.json',{'files':{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file()}})
    return 0 if report['passed'] and not report['failed'] and not report['timed_out'] and not report['not_run'] and report['source_unchanged'] else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    raise SystemExit(run(args.output.resolve()))
