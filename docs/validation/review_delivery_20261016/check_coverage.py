"""Inventory saved coverage, without importing or executing the sorter."""
import sys

if sys.flags.optimize:
    raise RuntimeError("Run evidence checks without Python optimization")

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'docs/validation'


def require(condition, context):
    if not condition:
        raise ValueError(context)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify_manifest(directory, manifest):
    for name, expected in manifest.items():
        require(digest((directory / name).read_bytes()) == expected, str(directory / name))
    return len(manifest)


def saved_source(reference, mapping):
    for name, expected in mapping.items():
        data = subprocess.check_output(['git', 'show', reference + ':' + name], cwd=ROOT)
        require(digest(data) == expected, reference + ':' + name)
    return {'saved_commit': subprocess.check_output(
        ['git', 'rev-parse', reference], cwd=ROOT, text=True).strip(),
        'matched_source_hashes': len(mapping), 'source_sha256': mapping}


def check():
    operation = BASE / 'heterogeneous_split_20261013'
    v = read(operation / 'verification.json')
    op = saved_source('cc1aa2d', v['source_sha256'])
    op['verified_evidence_files'] = verify_manifest(operation, v['evidence_sha256'])
    op['recorded_base_commit'] = v['base_commit']
    op['test_methods'] = v['development_tests']
    require(op['test_methods'] == {'methods': 53, 'new_split_adopt_methods': 22,
                                 'skips': 0, 'exit_code': 0}, 'operation method counts')
    require('Ran 53 tests' in (operation / 'development_tests.log').read_text(), 'operation log')

    campaign = BASE / 'heterogeneous_work_modes_20261013/structural_campaign'
    provenance = read(campaign / 'provenance.json')
    structural = saved_source('84f7e13', provenance['source_sha256'])
    structural['recorded_parent_head'] = provenance['head']
    structural['verified_manifest_files'] = verify_manifest(campaign, read(campaign / 'manifest.json'))
    config = read(campaign / 'config.json')
    summary = read(campaign / 'summary.json')
    require(summary['accepted'] and summary['source_unchanged'], 'campaign acceptance')
    outcomes = {row['case']: row for row in summary['outcomes']}
    variants = ['ordinary_list', 'tree_work_on', 'tree_work_off']
    expected_runs = {name + '/' + mode for name in variants for mode in ['checked', 'minimal']}
    totals = {name: Counter() for name in variants}
    prefixes = Counter()
    smaller = {name: Counter() for name in variants}
    cases = []
    for spec in config['plan']:
        path = campaign / (spec['case'] + '.json.gz')
        row = json.loads(gzip.decompress(path.read_bytes()))
        require(row['status'] == outcomes[spec['case']]['status'] == 'PASS', spec['case'])
        require(row['spec'] == spec and len(row['values']) == spec['n'], 'input specification')
        require(row['input_sha256'] == digest(repr(row['values']).encode()), 'input hash')
        require(set(row['runs']) == expected_runs, 'six original runs')
        expected_coverage = outcomes[spec['case']]['coverage']
        for name in variants:
            for mode in ['checked', 'minimal']:
                run = row['runs'][name + '/' + mode]
                require(run['output'] == sorted(row['values']), 'saved external output')
                require(run['final_output_geometry_replay_passed'] is True, 'recorded final checks')
                if mode == 'checked':
                    require([p['n'] for p in run['prefixes']] == list(range(3, spec['n'] + 1)), 'prefix sequence')
                    coverage = run['coverage']
                    require(coverage == expected_coverage, 'coverage across reports/configurations')
                    require(len(coverage['nonempty_split_sizes']) == coverage['counts']['both_nonempty'], 'partition count')
                    totals[name].update(coverage['counts'])
                    prefixes[name] += len(run['prefixes'])
                    for sizes in coverage['nonempty_split_sizes']:
                        require(len(sizes) == 2 and all(type(x) is int and x > 0 for x in sizes), 'nonempty sizes')
                        smaller[name][str(min(sizes))] += 1
            for mode in ['checked', 'minimal']:
                on, off = (row['runs'][x + '/' + mode] for x in ['tree_work_on', 'tree_work_off'])
                require(on['state_digest'] == off['state_digest'] and on['prefixes'] == off['prefixes'], 'on/off snapshots')
        cases.append({'case': spec['case'], 'input_sha256': row['input_sha256'],
                      'report_sha256': digest(path.read_bytes()), 'counts': expected_coverage['counts'],
                      'nonempty_split_sizes': expected_coverage['nonempty_split_sizes']})
    require(len(cases) == len({c['input_sha256'] for c in cases}) == 18, 'unique inputs')
    for name in variants:
        require(prefixes[name] == 5349, 'prefix total')
        for key, expected in [('splits', 460), ('both_nonempty', 230),
                              ('insert_into_previous_split_output', 666), ('resplit_previous_output', 212)]:
            require(totals[name][key] == expected, key)
        require(smaller[name]['1'] == 224 and sum(smaller[name].values()) == 230, 'smaller sides')
    structural.update(inputs=18, original_executions=108, per_checked_configuration={
        name: {'counts': dict(totals[name]), 'prefixes': prefixes[name],
               'smaller_side_distribution': dict(smaller[name])} for name in variants}, cases=cases)
    recorded = {}
    for directory, filename in [('common_qualification_v2_20261015', 'coverage_audit.json'),
                                ('split_trace_followup_20261015', 'coverage_summary.json')]:
        path = BASE / directory / filename
        manifest = read(BASE / directory / 'SHA256SUMS.json')
        require(digest(path.read_bytes()) == manifest[filename], 'qualification coverage summary hash')
        recorded[directory] = {'sha256': digest(path.read_bytes()), 'saved_summary': read(path)}
    return {'scope': 'read_only_existing_archive_inventory; no sorter or tests executed',
            'base_commit': subprocess.check_output(['git', 'rev-parse', '1d3106d9'], cwd=ROOT, text=True).strip(),
            'operation_evidence': op, 'structural_evidence': structural,
            'qualification_coverage': recorded,
            'limitations': ['No complete event traces in the structural archive: insert/re-split counts are saved observations, not independently recomputed events.',
                            'Qualification coverage summaries were hash-checked and read, not reconstructed from all raw traces.',
                            'Saved source commits are not clean execution commits; recorded base HEADs precede the dirty executed changes.',
                            'No latest-version six-case regression, qualification or timing was run.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('PASS: 18 saved inputs / 108 original-run records; source snapshots and recorded coverage checked. No sorting executed.')
