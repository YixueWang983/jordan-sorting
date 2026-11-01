"""Predeclared, separately identified host-stability diagnostic (not thesis data)."""
import copy
import random

from common_input_protocol import measurement_protocol
from input_suite_registry import canonical_cases, SOURCE_ORDER
from uninstrumented_protocol import BACKENDS

SCHEMA = 'host_stability_diagnostic_v1'
SEED = 20261101


def select_cases(suite, case_ids=()):
    entries = canonical_cases(suite)
    by_id = {e['case_id']: e for e in entries}
    if case_ids:
        if len(set(case_ids)) != len(case_ids) or set(case_ids) - set(by_id):
            raise ValueError('duplicate or unknown diagnostic case_id')
        wanted = set(case_ids)
    else:
        wanted = set()
        for source in SOURCE_ORDER:
            rows = [e for e in entries if e['source'] == source]
            if not rows:
                continue
            for n in (min(e['n'] for e in rows), max(e['n'] for e in rows)):
                wanted.add(min(e['case_id'] for e in rows if e['n'] == n))
    return [e for e in entries if e['case_id'] in wanted]


def rules():
    value = copy.deepcopy(measurement_protocol())
    value['schema'] = SCHEMA
    value['calibration']['batch_candidates'] = [2 ** i for i in range(13)]
    value['input_set'] = 'preselected diagnostic panel; never accepted as formal thesis evidence'
    return value


def session_order(entries, session):
    order = list(entries)
    random.Random(SEED + session).shuffle(order)
    return order
