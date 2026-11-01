"""Separate identities and environment gates for the preregistered rerun."""
import re
import subprocess
import hashlib
from common_input_protocol import ROOT

from common_input_protocol import measurement_protocol
from common_qualification_v2_protocol import frozen_selection, plan
from split_qualification_protocol import split_selection, split_plan

BACKENDS = ('ordinary_list', 'heterogeneous_finger_uninstrumented')
QUALIFICATION_SCHEMAS = {
    'common': 'uninstrumented_common_qualification_v1',
    'targeted_split': 'uninstrumented_targeted_qualification_v1',
}
MEASUREMENT_SCHEMA = 'uninstrumented_measurement_tools_v1'
POWER_FIELDS = {'power', 'power_settings', 'power_source', 'lowpowermode'}
PREREGISTRATION_COMMIT = '4aaf0022603e1abd9550b956c51da98ae89c29cf'
PREREGISTRATION_PATH = 'docs/plan/uninstrumented_rerun_protocol_20261101.md'


def registration():
    original = subprocess.check_output(['git','show',PREREGISTRATION_COMMIT+':'+PREREGISTRATION_PATH],cwd=ROOT)
    if (ROOT/PREREGISTRATION_PATH).read_bytes() != original:
        raise ValueError('preregistered protocol changed; cannot reuse the registration')
    return dict(commit=PREREGISTRATION_COMMIT,path=PREREGISTRATION_PATH,
                sha256=hashlib.sha256(original).hexdigest())


def qualification_config(dataset):
    if dataset == 'common':
        cfg, selected = plan(), frozen_selection()
    elif dataset == 'targeted_split':
        cfg, selected = split_plan(), split_selection()
    else:
        raise ValueError('uninstrumented rerun only includes common and targeted_split')
    cfg.update(schema=QUALIFICATION_SCHEMAS[dataset],
               preregistration=registration(),
               configuration='ordinary_list and heterogeneous_finger_uninstrumented; detailed_work=False, instrumented=False; same configuration in every replay')
    return cfg, selected, measurement_protocol()


def parsed_power(power, settings):
    source = re.search(r"Now drawing from '([^']+)'", power)
    modes = re.findall(r'^\s*lowpowermode\s+(\d+)\s*$', settings, re.MULTILINE)
    if source is None or len(modes) != 1:
        raise ValueError('cannot establish power source/low-power mode from pmset')
    return source.group(1), modes[0]


def power_observation(power=None):
    if power is None:
        power = subprocess.check_output(['pmset', '-g', 'batt'], text=True).strip()
    settings = subprocess.check_output(['pmset', '-g'], text=True).strip()
    source, mode = parsed_power(power, settings)
    return dict(power=power, power_settings=settings, power_source=source, lowpowermode=mode)


def require_power(observation):
    if not POWER_FIELDS <= set(observation):
        raise ValueError('missing recorded AC/low-power observations')
    source, mode = parsed_power(observation['power'], observation['power_settings'])
    if (source, mode) != (observation['power_source'], observation['lowpowermode']):
        raise ValueError('power fields disagree with raw pmset evidence')
    if source != 'AC Power' or mode != '0':
        raise RuntimeError('Connect AC power and disable Low Power Mode before measurement.')


def require_machine(execution):
    require_power(execution['hardware'])
    if (execution['hardware'].get('machdep.cpu.brand_string') != 'Apple M4'
            or not execution['python'].startswith('3.12.14 ')
            or execution['python_optimize'] != 0):
        raise RuntimeError('preregistered machine requires Apple M4 and CPython 3.12.14 without optimization')


def hardware_binding(hardware):
    # Battery percentage and pmset's transient sleep-preventer list may change;
    # parsed AC source/low-power mode and all fixed machine fields must match.
    return {k:v for k,v in hardware.items() if k not in {'power', 'power_settings'}}
