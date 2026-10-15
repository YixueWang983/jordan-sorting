"""Preselected targeted two-sided split set; separate from the original 140."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Split qualification requires optimization level 0')
from common_input_protocol import digest, measurement_protocol
from common_qualification_v2_protocol import plan, frozen_selection
from validate_finger_middle_splits import values_for
from oracle import oracle
from stats import structure_profile

SPLIT_SCHEMA = 'targeted_split_qualification_v1'


def split_selection():
    cases=[]
    for n in (128,129):
        for k in (3,7,19):
            for mirror in (False,True):
                values=values_for(n,k,mirror);cert=oracle(values);profile=structure_profile(values,oracle_result=cert)
                if not cert['valid'] or sorted(values)!=list(range(1,n+1)):
                    raise ValueError('invalid preselected split construction')
                base=f'split-n{n}-k{k}'
                spec=dict(case=base+('-mirror' if mirror else ''),base_id=base,n=n,k=k,mirror=mirror,
                          requested_category=profile['category'],construction='validate_finger_middle_splits.values_for')
                cases.append(dict(spec=spec,values=values,input_sha256=digest(values),rank_sha256=digest(values),
                    status='SELECTED',duplicate_of=None,profile=profile,oracle={k:v for k,v in cert.items() if k!='sorted'}))
    if len({c['input_sha256'] for c in cases})!=12:raise ValueError('duplicate targeted split input')
    return dict(cases=cases,selection_sha256=digest(cases),deficits=[])


def split_plan():
    result=plan();selection=split_selection()
    result.update(schema=SPLIT_SCHEMA,selection_sha256=selection['selection_sha256'],sizes=[128,129],
        targets=dict(k=[3,7,19],directions=['original','mirror'],inputs=12),campaign_seconds=180,
        selection='fixed existing values_for(n,k,mirror), n=128/129, k=3/7/19, both directions; no timing-based choices',
        order='n then k then original/mirror; backend first alternates by selected index',
        coverage_gate='each input and backend must record a performed split with both sides nonempty and actual min(left_size,right_size)==k',
        coverage_report='all primary splits: source/outputs/smaller-side sizes, source/output owners; subsequent direct output-list insertions and next split, no inferred full lineage',
        resource_scope='180 seconds per case shared by both backends; 180 seconds entire small campaign; no retry/replacement',
        interpretation='targeted dependent constructions, not random or independent samples; original 140 remains separate',
        original_common_selection_sha256=frozen_selection()['selection_sha256'])
    return result


def split_measurement_protocol():
    return dict(schema='targeted_split_measurement_protocol_v1',dataset='targeted_split',
        selection_sha256=split_selection()['selection_sha256'],rules=measurement_protocol(),
        interpretation='separate descriptive results for preselected two-sided splits; do not pool with 140 as independent samples',
        resources='same numerical calibration/formal limits applied separately to this dataset; no samples authorized by qualification',
        performance_eligible=False)
