"""Versioned native macOS/Windows observations, outside measured sorting calls.

No system setting is changed. Raw power observations remain part of the evidence.
The host declaration (for example a BIOS frequency) is separate from telemetry.
"""
import ctypes
import json
import platform
import re
import struct
import subprocess
import sys

SCHEMA = 'mac_windows_environment_v1'
PYTHON_VERSION = '3.12.14'
GUID = r'[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}'


def windows_console_encoding():
    # Native console output follows the console code page, not Python UTF-8
    # mode or the ANSI code page. Detached processes fall back to the OEM page.
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    for name in ('GetConsoleOutputCP', 'GetOEMCP'):
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = [], ctypes.c_uint
        codepage = fn()
        if codepage:
            return 'cp' + str(codepage)
    raise RuntimeError('Windows console encoding is unavailable')


def command(args):
    encoding = windows_console_encoding() if sys.platform == 'win32' else 'utf-8'
    return subprocess.check_output(args, encoding=encoding, timeout=30).strip()


def windows_power_status():
    class Status(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ubyte) for name in (
            'ACLineStatus', 'BatteryFlag', 'BatteryLifePercent', 'SystemStatusFlag')]
        _fields_ += [(name, ctypes.c_uint32) for name in ('BatteryLifeTime', 'BatteryFullLifeTime')]
    status = Status()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel.GetSystemPowerStatus
    fn.argtypes, fn.restype = [ctypes.POINTER(Status)], ctypes.c_int
    if not fn(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {name: getattr(status, name) for name, _ in Status._fields_}


def parse_windows_power(raw, settings):
    data = json.loads(raw)
    fields = {'ACLineStatus', 'BatteryFlag', 'BatteryLifePercent', 'SystemStatusFlag',
              'BatteryLifeTime', 'BatteryFullLifeTime'}
    if type(data) is not dict or set(data) != fields or any(type(v) is not int for v in data.values()):
        raise ValueError('invalid GetSystemPowerStatus evidence')
    if data['ACLineStatus'] not in (0, 1) or data['SystemStatusFlag'] not in (0, 1):
        raise ValueError('unknown Windows AC/battery-saver status')
    if not (0 <= data['BatteryFlag'] <= 255 and
            (0 <= data['BatteryLifePercent'] <= 100 or data['BatteryLifePercent'] == 255) and
            all(0 <= data[k] <= 0xffffffff for k in ('BatteryLifeTime', 'BatteryFullLifeTime'))):
        raise ValueError('invalid Windows power field range')
    schemes = re.findall(GUID, settings)
    if len(schemes) != 1:
        raise ValueError('cannot establish active Windows power scheme')
    return ('AC Power' if data['ACLineStatus'] == 1 else 'Battery Power',
            str(data['SystemStatusFlag']), schemes[0].lower())


def windows_power_observation():
    raw = json.dumps(windows_power_status(), sort_keys=True, separators=(',', ':'))
    settings = command(['powercfg', '/getactivescheme'])
    source, mode, scheme = parse_windows_power(raw, settings)
    return dict(power_platform='windows', power=raw, power_settings=settings,
                power_source=source, lowpowermode=mode, power_scheme=scheme)


def collect_hardware():
    base = dict(environment_schema=SCHEMA, host_name=platform.node(),
                architecture=platform.machine(), os_version=platform.version(),
                python_implementation=platform.python_implementation(),
                python_bits=str(struct.calcsize('P') * 8))
    if sys.platform == 'darwin':
        base['os_family'] = 'macos'
        for key, name in (('machdep.cpu.brand_string', 'cpu_model'), ('hw.physicalcpu', 'physical_cores'),
                          ('hw.logicalcpu', 'logical_cores'), ('hw.memsize', 'memory_bytes')):
            base[name] = command(['sysctl', '-n', key])
    elif sys.platform == 'win32':
        base['os_family'] = 'windows'
        script = ("[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
                  "$c=@(Get-CimInstance Win32_Processor); $s=Get-CimInstance Win32_ComputerSystem; "
                  "[ordered]@{cpu_model=($c.Name -join '; '); "
                  "physical_cores=($c | Measure-Object NumberOfCores -Sum).Sum; "
                  "logical_cores=($c | Measure-Object NumberOfLogicalProcessors -Sum).Sum; "
                  "memory_bytes=$s.TotalPhysicalMemory; hypervisor_present=$s.HypervisorPresent} "
                  "| ConvertTo-Json -Compress")
        raw = subprocess.check_output(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                                      encoding='utf-8-sig', timeout=30)
        data = json.loads(raw)
        base.update({k: str(v).strip() for k, v in data.items()})
        for key in ('physical_cores', 'logical_cores', 'memory_bytes'):
            if type(data[key]) not in (int, float) or int(data[key]) != data[key]:
                raise ValueError('nonintegral Windows hardware value')
            base[key] = str(int(data[key]))
    else:
        raise RuntimeError('evaluation supports native macOS and Windows only')
    # Late import keeps the public legacy power API and its test seams intact.
    from uninstrumented_protocol import power_observation
    base.update(power_observation())
    validate_hardware(base)
    return base


def validate_hardware(hardware):
    common = {'environment_schema', 'host_name', 'architecture', 'os_version', 'os_family',
              'python_implementation', 'python_bits', 'cpu_model', 'physical_cores',
              'logical_cores', 'memory_bytes', 'power', 'power_settings', 'power_source', 'lowpowermode'}
    family = hardware.get('os_family')
    extra = {'hypervisor_present', 'power_platform', 'power_scheme'} if family == 'windows' else set()
    if (family not in ('macos', 'windows') or set(hardware) != common | extra or
            hardware.get('environment_schema') != SCHEMA or
            any(type(v) is not str or not v.strip() for v in hardware.values())):
        raise ValueError('cross-platform hardware fields/schema')
    if any(not hardware[k].isdigit() or int(hardware[k]) <= 0
           for k in ('physical_cores', 'logical_cores', 'memory_bytes')):
        raise ValueError('cross-platform hardware numeric values')
    if int(hardware['logical_cores']) < int(hardware['physical_cores']):
        raise ValueError('inconsistent CPU core counts')
    if hardware['python_implementation'] != 'CPython' or hardware['python_bits'] != '64':
        raise RuntimeError('evaluation requires 64-bit CPython')
    if family == 'windows' and (hardware['power_platform'] != 'windows' or
                                hardware['hypervisor_present'] not in ('True', 'False')):
        raise ValueError('Windows hardware identity')
    from uninstrumented_protocol import require_power
    require_power(hardware)


def power_binding(observation):
    """Stable settings only; battery percentages and raw process lists may vary."""
    result = dict(power_platform=observation.get('power_platform', 'macos'),
                  power_source=observation['power_source'], lowpowermode=observation['lowpowermode'])
    if result['power_platform'] == 'windows':
        result['power_scheme'] = observation['power_scheme']
    return result


def require_power_binding(observation, expected):
    from uninstrumented_protocol import require_power
    require_power(observation)
    if power_binding(observation) != expected:
        raise ValueError('power settings changed from the bound environment')
