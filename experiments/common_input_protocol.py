"""Predeclared common-input selection and matched measurement rules (not a gate)."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification evidence requires optimization level 0')

from pathlib import Path
import hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'experiments')]
from committed_records import canonical
from generators import generate_nested
from preflight_next_stage import block_sequence

SIZES = (32, 33, 64, 65, 128, 129, 256, 257, 512, 513)
CATEGORIES = ('strict_flat', 'low_nesting_valid', 'medium_nesting_valid', 'nested_heavy_valid')
TARGETS = dict(zip(CATEGORIES, (2, 4, 4, 4)))
BACKENDS = ('ordinary_list', 'heterogeneous_finger')
SEED = 20261015
SCHEMA = 'common_input_qualification_v1'


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def source_identity():
    # Bind every Python helper/test as well as the production modules. Later
    # evidence tools must be run from this producing revision, not a newer one.
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('src', 'experiments', 'tests')
            for p in sorted((ROOT/folder).glob('*.py'))}


def candidate_specs():
    for n in SIZES:
        for category in CATEGORIES:
            for index in range(1 if category == 'strict_flat' else 16):
                base = f'n{n}-{category}-{index:02d}'
                for mirror in (False, True):
                    yield dict(case=base+('-mirror' if mirror else ''), base_id=base,
                               n=n, requested_category=category, candidate_index=index,
                               seed=SEED+n*100+index, mirror=mirror)


def generate(spec):
    n, category, index = spec['n'], spec['requested_category'], spec['candidate_index']
    if category == 'strict_flat':
        values = list(range(1, n+1))
    elif category in CATEGORIES[1:3]:
        values = block_sequence(n, spec['seed'], 'low' if category == CATEGORIES[1] else 'medium')
    else:
        # Increasing even-length prefix, followed by a nested suffix.
        # Classification and validity are measured; neither is presumed.
        prefix = min(2*index, 2*((n-8)//2))
        values = list(range(1, prefix+1))+[prefix+x for x in generate_nested(n-prefix)]
    return [n+1-x for x in values] if spec['mirror'] else values


def qualification_plan():
    return dict(schema=SCHEMA, sizes=list(SIZES), targets=TARGETS, seed=SEED,
                candidates=list(candidate_specs()), case_seconds=180,
                campaign_seconds=1800, selection_seconds=180,
                selection='first valid, correctly classified, globally rank-unique candidates; stop a cell at target; no backend runs during selection',
                dedup='SHA-256 of canonical rank permutation; confirm permutation 1..n; mirrors carry base_id and are dependent',
                category_rule='src/stats.py: zero nesting; else depth<=1 and ratio<=.35; else depth<=3 and ratio<=.70; else heavy',
                qualification='both backends: checked public diagnostics with audit/replay at every completed prefix, then fresh public minimal output; detailed_work=False for tree',
                order='descending n then category order then candidate order; backend order alternates by selected case index',
                failure='first correctness, execution or resource failure stops later cases; retain selected failing case and mark remainder NOT_RUN; no retry or replacement',
                resource_scope='worker wall budget, including audit/replay/startup/persistence, NOT sorting performance',
                performance_eligible=False)


def measurement_protocol():
    return dict(schema='matched_measurement_protocol_20261015_v1', status='rules_frozen_gates_pending',
        performance_eligible=False, execution_mode='minimal', tree_detailed_work=False,
        input_set='entire frozen selected set after every selected case passes both backends; report cell deficits, never filter legal backend failures',
        calibration=dict(batch_candidates=[1, 2, 4, 8, 16, 32, 64, 128], repetitions=3,
                         target_batch_ns=10_000_000, budget_seconds=600,
                         rule='per input choose first common B where both backend medians reach target; test candidates ascending, alternating backend first; if none, stop and revise protocol before formal measurements',
                         scope='separate calibration identity; no calibration observations in performance table'),
        warmups_per_backend=5, repetitions=20, campaign_seconds=1800, input_seconds=120,
        order=dict(case_shuffle_seed=SEED, backend_first='alternate by shuffled case index plus round; 10 first positions per backend over 20 sample rounds'),
        gc='enabled with recorded default thresholds; gc.collect outside each batch; do not disable cyclic GC',
        clock='perf_counter_ns; record implementation/resolution and 1000 consecutive read deltas',
        boundary='fresh public sorting call including initialization/core/output recovery, batch loop and output append inside; expected comparison, gc.collect, serialization and persistence outside',
        statistics=dict(unit='timing batch; calls within a batch are not independent samples',
                        per_call='batch elapsed_ns / B', per_input='median and IQR of 20 per-call batch observations; linear quantiles at .25/.75 (R7)',
                        comparison='ratio of tree and list per-input medians; report all inputs and descriptive strata distributions, no independent-sample inference for mirrors',
                        exclusions='none for slow or extreme durations; failed/timeout runs remain failed, no silent trimming/retry'),
        environment='freeze commit, all source hashes, exact input/config hashes, Python executable/version/flags, OS/architecture, CPU/cores/RAM, power state, GC and clock; single idle host, no concurrent checked validation or development loads',
        gates=['common qualification archive independently validated against producing source/config',
               'calibration complete and per-input B frozen before any formal sample',
               'manual representation/locality/cost claims, assumptions and open obligations reviewed; efficient-backend minimum not certified by this protocol',
               'formal runner/validator tested and exact measurement-source revision frozen; source/config changes require affected requalification'],
        historical='rollback 60-input/3600-row results and development pilot remain separate')
