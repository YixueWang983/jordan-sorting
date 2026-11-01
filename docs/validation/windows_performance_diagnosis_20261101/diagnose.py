"""Bounded component probes and per-test timing; diagnostic, never thesis data.

Run from the repository with the same native CPython 3.12.14 on both hosts.
No power, affinity, security, production-code or measurement-policy changes.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gc
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import struct
import subprocess
import sys
import sysconfig
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / p) for p in ('src', 'experiments', 'tests')]
from common_input_protocol import source_identity, digest
from committed_records import atomic_bytes, canonical
from input_suite_registry import load_suite
from stability_protocol import select_cases
from matched_backend_fixture import backend_spec
from paper_jordan_sort import paper_jordan_sort_valid
from platform_environment import collect_hardware
from uninstrumented_protocol import BACKENDS, power_observation, require_power

SCHEMA = 'host_performance_decomposition_v1'
SEED = 20261101


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def metadata():
    config_keys = ('Py_DEBUG', 'WITH_PYMALLOC', 'Py_ENABLE_SHARED', 'Py_GIL_DISABLED',
                   'CONFIG_ARGS', 'CC', 'CFLAGS', 'PY_CFLAGS', 'PY_CFLAGS_NODIST',
                   'PGO_PROF_USE_FLAG', 'LDFLAGS', 'CONFIGURE_LDFLAGS', 'SOABI')
    return dict(schema=SCHEMA, performance_eligible=False,
                captured_utc=datetime.now(timezone.utc).isoformat(),
                head=git('rev-parse', 'HEAD'), dirty=bool(git('status', '--porcelain')),
                source_sha256=source_identity(), script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                python=sys.version, executable=sys.executable, base_prefix=sys.base_prefix,
                implementation=platform.python_implementation(), architecture=platform.machine(),
                pointer_bits=struct.calcsize('P') * 8, platform=platform.platform(),
                optimize=sys.flags.optimize, has_gettotalrefcount=hasattr(sys, 'gettotalrefcount'),
                trace_active=sys.gettrace() is not None, profiler_active=sys.getprofile() is not None,
                gc_enabled=gc.isenabled(), gc_thresholds=gc.get_threshold(),
                config={k:sysconfig.get_config_var(k) for k in config_keys},
                clocks={k:vars(time.get_clock_info(k)) for k in ('perf_counter', 'process_time')},
                hardware=collect_hardware())


def measured(fn, operations):
    gc.collect()
    cpu_start = time.process_time_ns()
    start = time.perf_counter_ns()
    result = fn()
    elapsed = time.perf_counter_ns() - start
    cpu_elapsed = time.process_time_ns() - cpu_start
    return result, dict(wall_ns=elapsed, cpu_ns=cpu_elapsed, operations=operations,
                        wall_ns_per_operation=elapsed / operations,
                        cpu_ns_per_operation=cpu_elapsed / operations)


def components(output):
    before = metadata()
    require_power(before['hardware'])
    if before['dirty']:
        raise RuntimeError('commit the diagnostic before measuring')
    save(output / 'environment.json', before)
    start = time.perf_counter()
    records = []
    suite = load_suite()
    cases = select_cases(suite)
    values = list(range(4096))
    random.Random(SEED).shuffle(values)
    blob = random.Random(SEED).randbytes(8192)
    hash_payload = blob * 128
    json_payload = [{'i':i, 'values':list(range(32))} for i in range(128)]
    scopes = {}

    def integer_loop():
        total = 0
        for i in range(1_000_000):
            total += i
        return total

    class Node:
        __slots__ = ('value',)
        def __init__(self, value):
            self.value = value
    nodes = {i:Node(i) for i in range(256)}

    def object_loop():
        total = 0
        for i in range(262144):
            total += nodes[i & 255].value
        return total

    def builtin_sort():
        for _ in range(64):
            answer = sorted(values)
        return answer

    def hash_loop():
        for _ in range(32):
            answer = hashlib.sha256(hash_payload).hexdigest()
        return answer

    def codec_loop():
        for _ in range(8):
            answer = json.loads(gzip.decompress(gzip.compress(canonical(json_payload), mtime=0)))
        return answer

    def clock_loop():
        for _ in range(100_000):
            time.perf_counter_ns()
        return True

    def gc_loop():
        for _ in range(20):
            gc.collect()
        return True

    def child(code):
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(str(ROOT / p) for p in ('src','experiments','tests')),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=30)
        return True

    probes = [
        ('python_integer_loop', integer_loop, 1_000_000, lambda x:x==999999*1000000//2),
        ('python_dict_attribute_loop', object_loop, 262144, lambda x:x==1024*sum(range(256))),
        ('builtin_sort_4096', builtin_sort, 64, lambda x:x==list(range(4096))),
        ('sha256_1MiB', hash_loop, 32, lambda x:x==hashlib.sha256(hash_payload).hexdigest()),
        ('json_gzip_roundtrip', codec_loop, 8, lambda x:x==json_payload),
        ('perf_counter_calls', clock_loop, 100_000, bool),
        ('gc_collect_loaded_process', gc_loop, 20, bool),
        ('python_process_start', lambda:child('pass'), 1, bool),
        ('python_project_import', lambda:child('import paper_jordan_sort'), 1, bool),
        ('git_status', lambda:git('status','--porcelain'), 1, lambda x:x==''),
        ('source_hash_157_files', source_identity, 1, lambda x:x==before['source_sha256']),
        ('native_hardware_capture', collect_hardware, 1, lambda x:x['cpu_model']==before['hardware']['cpu_model']),
        ('native_power_capture', power_observation, 1, lambda x:x['power_source']=='AC Power'),
    ]
    with tempfile.TemporaryDirectory(prefix='performance-probe-', dir=output) as tmp:
        scratch = Path(tmp)
        write_index = 0
        def write_files(kind):
            nonlocal write_index
            for _ in range(32):
                path = scratch / f'{kind}-{write_index}.bin'
                write_index += 1
                if kind == 'atomic':
                    atomic_bytes(path, blob)
                else:
                    with path.open('wb') as stream:
                        stream.write(blob)
                        if kind == 'fsync':
                            stream.flush()
                            os.fsync(stream.fileno())
            return True
        probes += [(f'write_8KiB_{k}', lambda k=k:write_files(k),32,bool) for k in ('buffered','fsync','atomic')]
        for round_index in range(5):
            order = list(probes)
            random.Random(SEED + round_index).shuffle(order)
            for name, fn, n, check in order:
                if time.perf_counter() - start > 240:
                    raise TimeoutError('component budget 240 seconds exhausted')
                result, row = measured(fn, n)
                if not check(result):
                    raise ValueError('probe correctness: ' + name)
                records.append(dict(probe=name, round=round_index, **row))
            print(f'components round {round_index + 1}/5 passed', flush=True)
    # Same B on both hosts controls the adaptive-B difference in the first study.
    # Initialization, fresh public sort and output append remain inside the clock.
    specs = {name:backend_spec(name) for name in BACKENDS}
    for case in cases:
        expected = sorted(case['values'])
        for name in BACKENDS:
            for _ in range(2):
                assert paper_jordan_sort_valid(case['values'], 'minimal', backend=specs[name]) == expected
        for round_index in range(7):
            for name in (BACKENDS if round_index % 2 == 0 else BACKENDS[::-1]):
                def sort_batch():
                    answers = []
                    for _ in range(16):
                        answers.append(paper_jordan_sort_valid(case['values'],'minimal',backend=specs[name]))
                    return answers
                answers, row = measured(sort_batch, 16)
                if len(answers)!=16 or any(a!=expected for a in answers) or digest(case['values'])!=case['input_sha256']:
                    raise ValueError('fixed-B sort correctness/input mutation')
                records.append(dict(probe='fixed_B16_sort', case_id=case['case_id'], backend=name,
                                    input_sha256=case['input_sha256'], n=case['n'], round=round_index, **row))
        print('fixed B16 passed: ' + case['case_id'], flush=True)
    if source_identity()!=before['source_sha256'] or git('status','--porcelain'):
        raise ValueError('source/worktree changed')
    power_after = power_observation()
    require_power(power_after)
    groups = defaultdict(list)
    for r in records:
        groups[(r['probe'],r.get('case_id'),r.get('backend'))].append(r)
    summary = []
    for (probe,cid,backend), group in groups.items():
        summary.append(dict(probe=probe,case_id=cid,backend=backend,samples=len(group),
                            median_wall_ns_per_operation=statistics.median(r['wall_ns_per_operation'] for r in group),
                            median_cpu_ns_per_operation=statistics.median(r['cpu_ns_per_operation'] for r in group)))
    report = dict(schema=SCHEMA, performance_eligible=False, mode='components',
                  elapsed_seconds=time.perf_counter()-start, rounds=5, fixed_sort_rounds=7,
                  fixed_batch_size=16, source_unchanged=True, power_after=power_after,
                  notes=['Parent process CPU time excludes subprocesses.',
                         'Small Windows process_time values may be quantized; interpret large aggregates only.',
                         'File probes compare native API costs, not identical power-loss guarantees.',
                         'No attempt to attribute differences to OS versus CPU versus compiler in isolation.'],
                  records=records, summary=summary)
    save(output / 'components.json', report)
    return report


def suite_profile(output):
    before = metadata()
    if before['dirty']:
        raise RuntimeError('commit diagnostic before profiling tests')
    save(output / 'environment.json', before)
    entries = []
    class TimedResult(unittest.TextTestResult):
        def startTest(self, test):
            super().startTest(test)
            self.started = (time.perf_counter_ns(), time.process_time_ns())
        def stopTest(self, test):
            wall,cpu = self.started
            entries.append(dict(test_id=test.id(),module=test.__class__.__module__,
                                wall_seconds=(time.perf_counter_ns()-wall)/1e9,
                                parent_cpu_seconds=(time.process_time_ns()-cpu)/1e9))
            super().stopTest(test)
    start = time.perf_counter()
    tests = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    discovery = time.perf_counter()-start
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1, resultclass=TimedResult).run(tests)
    modules = defaultdict(lambda:dict(tests=0,wall_seconds=0.0,parent_cpu_seconds=0.0))
    for row in entries:
        group = modules[row['module']]
        group['tests'] += 1
        for k in ('wall_seconds','parent_cpu_seconds'):
            group[k] += row[k]
    report = dict(schema=SCHEMA,performance_eligible=False,mode='suite-profile',
                  elapsed_seconds=time.perf_counter()-start,discovery_seconds=discovery,
                  tests_run=result.testsRun,successful=result.wasSuccessful(),
                  error_entries=len(result.errors),failure_entries=len(result.failures),skipped=len(result.skipped),
                  source_unchanged=source_identity()==before['source_sha256'],
                  dirty_after=bool(git('status','--porcelain')),tests=entries,modules=dict(modules),
                  note='Whole-test timings; no per-function profiler. Parent CPU excludes child processes.')
    save(output / 'suite-profile.json',report)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('components','suite-profile'))
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if sys.version_info[:3]!=(3,12,14) or sys.flags.optimize!=0:
        raise RuntimeError('use native CPython 3.12.14, optimization level zero')
    args.output=args.output.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    try:
        result=components(args.output) if args.mode=='components' else suite_profile(args.output)
    except Exception as exc:
        save(args.output/'failure.json',dict(type=type(exc).__name__,error=str(exc),performance_eligible=False))
        raise
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','summary','tests','modules')},indent=2))
    if args.mode=='suite-profile' and not result['successful']:
        raise SystemExit(1)
