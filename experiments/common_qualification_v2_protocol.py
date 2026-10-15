"""Frozen full-set qualification v2, separate from v1 and from measurement."""
import sys
if sys.flags.optimize != 0:
    raise RuntimeError('Qualification v2 requires optimization level 0')
import json
from common_input_protocol import ROOT, digest, SIZES, TARGETS

SCHEMA = 'common_input_qualification_v2'
QUALIFICATION_SCHEMA = 'synchronous_checked_prefixes_v2'
SELECTION_SHA256 = 'c8d8f34f7dce619a87d54cffd8567255c80340742f00de072eb5ca771991b17b'
FROZEN_SELECTION = ROOT/'docs/validation/common_qualification_20261015/qualification/selected.json'
MODES = ('synchronous_v2', 'fresh_minimal')


def frozen_selection():
    selection = json.loads(FROZEN_SELECTION.read_text())
    if (selection['selection_sha256'] != SELECTION_SHA256
            or digest(selection['cases']) != SELECTION_SHA256
            or len(selection['cases']) != 140 or selection['deficits'] != []):
        raise ValueError('original frozen 140-input selection changed')
    return selection


def plan():
    return dict(schema=SCHEMA, qualification_schema=QUALIFICATION_SCHEMA,
        selection_sha256=SELECTION_SHA256, sizes=list(SIZES), targets=TARGETS,
        selection='reuse original selected.json exactly, including order, values, mirror origins and classification; no regeneration or replacement',
        case_seconds=180, campaign_seconds=1800,
        coverage='per backend: two independent CHECKED instances compared and audited at every completed prefix; third fresh CHECKED final replay; then independent public minimal call',
        change_from_v1='not fresh construction at every prefix; fewer repeated early updates; v1 archive retained unchanged',
        records='synchronous prefix comparisons n-2; final fresh checked replays 1; actual checked initializations 3; separate fresh minimal initialization 1',
        configuration='ordinary_list and heterogeneous_finger with detailed_work=False; same backend/config in all instances',
        order='original descending-size input order; backend first alternates by selected case index',
        failure='first ERROR/TIMEOUT stops later inputs; retain committed mode records; remaining NOT_RUN; no retries or replacements',
        resource_scope='180 seconds shared by both backends and all checks/startup/persistence per case; 1800 seconds campaign; resource observations are not sorting times',
        performance_eligible=False, efficient_backend_accepted=False)
