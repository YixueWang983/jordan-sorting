"""Fixed large-input resource probes; never a sorting-time benchmark.

Each length is an independent batch. Resource failures stop that batch, but
not the other predeclared lengths. A correctness/execution failure stops the
whole campaign. Inputs, budgets and ordering are frozen before generation.
"""
import argparse
from collections import Counter
from pathlib import Path
import platform
import sys

from preflight_next_stage import config, run as run_batch, source_hashes
from validate_ordinary_list_extended import (
    STOP_ERRORS, git, read_json, reserve, sha, write_json,
)


def campaign_config():
    batches = []
    for n in (256, 257, 512, 513):
        cfg = config()
        cfg.update(
            schema='large_qualification_probe_v1', case_seconds=180,
            batch_seconds=720, seed_base=20261011,
            larger_sizes='Only the four frozen lengths; one candidate per construction.',
            sampling_boundary='Coverage-guided representatives, not random samples or a formal timing set.',
        )
        cfg['plan'] = [dict(
            case_id=f'{family}_n{n}_probe', family=family, n=n,
            seed=20261011+n*100, kind='base', base_case_id=None,
            transform=None, prefix_check=False,
            sampling='coverage-guided construction',
        ) for family in ('flat_valid', 'blocks_low', 'blocks_medium', 'nested_valid')]
        batches.append(cfg)
    return dict(
        schema='large_qualification_campaign_v1', batches=batches,
        purpose='Resource qualification with full checked replay and fresh minimal output checks; NOT timing.',
        stop='Resource failure stops its length batch. Correctness/execution failure stops all later batches.',
        limits='180 seconds per worker, 720 per length; 2880 seconds total worker budget capacity, not a prediction.',
    )


def run(output):
    reserve(output)
    cfg = campaign_config()
    write_json(output/'campaign_config.json', cfg)
    before = source_hashes()
    write_json(output/'campaign_provenance.json', dict(
        head=git('rev-parse', 'HEAD'), status=git('status', '--short'),
        source_sha256=before, python=sys.version, executable=sys.executable,
        platform=platform.platform(), machine=platform.machine(),
        meaning='Worktree source hashes identify execution; HEAD alone does not include uncommitted tools.',
    ))
    outcomes = []
    stop = None
    for batch in cfg['batches']:
        n = batch['plan'][0]['n']
        if stop:
            outcomes.append(dict(n=n, status='NOT_RUN_STOP', reason=stop))
            continue
        print(f'BEGIN n={n}', flush=True)
        code = run_batch(output/f'n{n}', run_config=batch)
        summary = read_json(output/f'n{n}'/'summary.json')
        rows = [read_json(output/f'n{n}'/'cases'/f"{s['case_id']}.json") for s in batch['plan']]
        outcomes.append(dict(n=n, exit_code=code, summary=summary))
        for row in rows:
            if row['status'] in STOP_ERRORS:
                stop = f"{row['case_id']}: {row['status']}"
    rows = [read_json(p) for p in sorted(output.glob('n*/cases/*.json'))
            if not p.name.endswith('.request.json')]
    counts = dict(Counter(row['status'] for row in rows))
    unchanged = source_hashes() == before
    write_json(output/'campaign_summary.json', dict(
        planned=16, recorded=len(rows), status_counts=counts,
        not_run_after_campaign_stop=16-len(rows), batches=outcomes,
        source_unchanged=unchanged,
        qualification='Only PASS inputs qualify; timeout is neither a sorting error nor a pass.',
    ))
    write_json(output/'manifest.json', dict(files={
        str(p.relative_to(output)): sha(p) for p in sorted(output.rglob('*')) if p.is_file()
    }))
    return 0 if counts.get('PASS') == 16 and unchanged else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(run(args.output.resolve()))
