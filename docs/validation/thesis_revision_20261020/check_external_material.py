"""Read supplied diagnostic summaries; does not execute their programs or sort."""
import sys
if sys.flags.optimize:
    raise RuntimeError('Run evidence checks without Python optimization')
import ast
import hashlib
import json
from pathlib import Path

base = Path(__file__).parent / 'external_review'
files = sorted(base.glob('*'))
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
for name in ('wrapper_overhead.py', 'random_jordan_stress2.py'):
    ast.parse((base / name).read_text(), filename=name)
variants = {}
for line in (base / 'wrapper.log').read_text().splitlines():
    label, _, tail = line.partition(' ')
    if label in ('list', 'tree', 'tree_nofa', 'tree_nowr') and tail.startswith('{'):
        if label in variants:
            raise ValueError('duplicate successful variant summary')
        variants[label] = json.loads(tail)
if set(variants) != {'list','tree','tree_nofa','tree_nowr'}:
    raise ValueError('missing summary')
ids = set(variants['list'])
if len(ids) != 15 or any(set(v) != ids for v in variants.values()):
    raise ValueError('case mismatch')
ratios = {case: {label: variants[label][case]/variants['list'][case]
                for label in ('tree','tree_nofa','tree_nowr')} for case in sorted(ids)}
rows = [json.loads(x) for x in (base / 'stress_big.log').read_text().splitlines() if x.strip()]
by_seed = {x['seed']: x for x in rows}
if len(by_seed) != len(rows) or set(by_seed) != {11,12,13,14,21,22}:
    raise ValueError('unexpected seeds')
groups = {}
for name, seeds in [('large_report',[11,12,13,14]),('checked_report',[21,22])]:
    selected=[by_seed[s] for s in seeds]
    groups[name] = {key: sum(x['totals'].get(key,0) for x in selected)
                    for key in ('inputs','checked_runs','splits','two_sided','inputs_with_two_sided')}
    groups[name]['reported_failures'] = sum(x['failures'] for x in selected)
    groups[name]['max_min_side'] = max(x['totals']['max_min_side'] for x in selected)
report = {
  'scope':'read_only_external_log_arithmetic_and_script_inspection',
  'executed_supplied_programs':False,
  'independent_production_rerun':False,
  'verified_execution_source_or_environment':False,
  'file_sha256':hashes,
  'wrapper_cases':15,
  'wrapper_ratios':ratios,
  'wrapper_contains_failed_attempt':'TypeError:' in (base/'wrapper.log').read_text(),
  'stress_reported_totals':groups,
  'limits':[
    'No command lines, source hashes, input hashes, runtime environment or raw batch durations supplied.',
    'Wrapper script validates all warmups but only the last output of each timed batch.',
    'Successful tree_nowr summary follows a failed attempt; the failed script version is not supplied.',
    'Stress log contains aggregates, not per-input traces; argument bounds and execution provenance are unbound.',
    'Both supplied scripts rely on assert without an optimization guard; interpreter flags are unrecorded.',
    'Related generator outputs do not estimate the population frequency of two-sided Jordan splits.',
    'These summaries do not replace qualification or formal measurements.'
  ]
}
print(json.dumps(report,indent=2,sort_keys=True))
