"""Predeclared timing extension for the existing 18 structural inputs.

The original structural campaign supplies constructions, not timing evidence.
This dataset is qualified and measured separately from common and targeted_split.
"""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Structural split evidence requires optimization level 0')

from common_input_protocol import digest, measurement_protocol
from common_qualification_v2_protocol import plan
from oracle import oracle
from stats import structure_profile
from validate_finger_work_modes import sequence

STRUCTURAL_SCHEMA = 'structural_split_qualification_v1'
SIZES = (128, 129, 256, 257, 512, 513)
SHAPES = ('balanced', 'skew', 'repeated')


def structural_selection():
    cases = []
    for n in SIZES:
        for shape in SHAPES:
            mirror = bool(n % 2)
            values = sequence(n, shape, mirror)
            cert = oracle(values)
            profile = structure_profile(values, oracle_result=cert)
            if not cert['valid'] or sorted(values) != list(range(1, n + 1)):
                raise ValueError('invalid predeclared structural input')
            cid = f'{shape}-{n}'
            spec = dict(case=cid, base_id=f'{shape}-{n-n%2}', n=n, shape=shape,
                        mirror=mirror, requested_category=profile['category'],
                        construction='validate_finger_work_modes.sequence')
            cases.append(dict(spec=spec, values=values, input_sha256=digest(values),
                              rank_sha256=digest(values), status='SELECTED',
                              duplicate_of=None, profile=profile,
                              oracle={k: v for k, v in cert.items() if k != 'sorted'}))
    if len({c['input_sha256'] for c in cases}) != 18:
        raise ValueError('duplicate structural input')
    return dict(cases=cases, selection_sha256=digest(cases), deficits=[])


def structural_plan():
    result = plan()
    selected = structural_selection()
    result.update(
        schema=STRUCTURAL_SCHEMA, selection_sha256=selected['selection_sha256'],
        sizes=list(SIZES), targets=dict(shapes=list(SHAPES), inputs=18),
        selection='all 18 existing structural constructions; n=128/129/256/257/512/513; balanced/skew/repeated; odd n mirrored; no timing-based choices',
        order='ascending n then balanced/skew/repeated; backend first alternates by case index',
        coverage_gate='primary checked traces on both backends: one finite-owner two-sided split of size m=(even_n-6)/2 with smaller side floor(m/2) or 1 for balanced/skew; repeated has floor((even_n-4)/8) finite-owner two-sided splits and at least that count minus one re-splits of earlier outputs',
        coverage_report='actual split source/output sizes, owners, smaller sides and direct later output updates up to the next split; no inferred full lineage',
        interpretation='separate descriptive timing extension; existing structural checks are not timing samples; related constructions and parity/mirror pairs are dependent',
    )
    return result


def structural_measurement_protocol():
    return dict(schema='structural_split_measurement_protocol_v1', dataset='structural_split',
                selection_sha256=structural_selection()['selection_sha256'],
                rules=measurement_protocol(),
                interpretation='separate dataset with unchanged numerical timing rules; do not pool old and new campaigns as independent random inputs',
                performance_eligible=False)


def coverage_summary(coverage):
    """Summarize independently reconstructed primary trace events only."""
    splits = coverage['splits']
    nonempty = [s for s in splits if s['left_size'] > 0 and s['right_size'] > 0]
    outputs = set()
    resplits = 0
    updates = dict(retained_inserts=0, acquired_inserts=0,
                   retained_resplits=0, acquired_resplits=0)
    both_updated = 0
    for split in splits:
        resplits += split['source_list_id'] in outputs
        outputs.update(lid for lid in (split['left_list_id'], split['right_list_id'])
                       if lid is not None)
        follow = split['subsequent_updates_before_next_split']
        if split['smaller_side'] > 0:
            both_updated += bool(follow['left']) and bool(follow['right'])
        for side, events in follow.items():
            role = 'acquired' if side == split['acquired_side'] else 'retained'
            for event in events:
                if event['kind'] == 'boundary_insert':
                    updates[role + '_inserts'] += 1
                elif event['kind'] == 'split_source':
                    updates[role + '_resplits'] += 1
                else:
                    raise ValueError('unknown direct split-output update')
    return dict(performed_splits=len(splits), two_sided_splits=len(nonempty),
                finite_owner_two_sided=sum(s['finite_owner'] for s in nonempty),
                resplit_previous_output=resplits,
                source_sizes=sorted({s['input_size'] for s in nonempty}),
                smaller_sides=sorted({s['smaller_side'] for s in nonempty}),
                two_sided_with_both_outputs_updated=both_updated, **updates)


def require_structural_coverage(spec, coverage):
    summary = coverage_summary(coverage)
    n, shape = spec['n'], spec['shape']
    if type(n) is not int or shape not in SHAPES:
        raise ValueError('invalid structural coverage specification')
    m = (n - n % 2 - 6) // 2
    if shape in ('balanced', 'skew'):
        smaller = m // 2 if shape == 'balanced' else 1
        if (summary['two_sided_splits'] != 1 or summary['finite_owner_two_sided'] != 1
                or summary['source_sizes'] != [m] or summary['smaller_sides'] != [smaller]):
            raise ValueError('missing actual balanced/skew split coverage')
    else:
        count = (n - n % 2 - 4) // 8
        if (summary['two_sided_splits'] != count
                or summary['finite_owner_two_sided'] != count
                or summary['resplit_previous_output'] < count - 1):
            raise ValueError('missing actual repeated split/update coverage')
    return summary
