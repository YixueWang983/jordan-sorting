import copy
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from common_input_protocol import source_identity
from committed_records import atomic_bytes, atomic_json, commit_record, read_records, run_bounded
import platform_environment as platform_env
import uninstrumented_protocol as protocol
from validate_matched_measurement import check_review
from input_suite_protocol import environment_equal

SCHEME='381b4222-f694-41f0-9685-ff5bb260df2e'


def windows_power(ac=1,saver=0):
    raw=dict(ACLineStatus=ac,BatteryFlag=128,BatteryLifePercent=255,SystemStatusFlag=saver,
             BatteryLifeTime=4294967295,BatteryFullLifeTime=4294967295)
    return dict(power_platform='windows',power=json.dumps(raw),
                power_settings='电源方案 GUID: '+SCHEME+' (平衡)',power_scheme=SCHEME,
                power_source='AC Power' if ac==1 else 'Battery Power',lowpowermode=str(saver))


def windows_execution():
    hardware=dict(environment_schema=platform_env.SCHEMA,host_name='TEST ONLY',architecture='AMD64',
        os_version='TEST',os_family='windows',python_implementation='CPython',python_bits='64',
        cpu_model='AMD TEST',physical_cores='6',logical_cores='12',memory_bytes='34359738368',
        hypervisor_present='True',**windows_power())
    return dict(hardware=hardware,platform='Windows TEST',machine='AMD64',python='3.12.14 TEST',python_optimize=0)


class PlatformEnvironmentTests(unittest.TestCase):
    def test_windows_raw_observations_and_machine_are_accepted_without_m4(self):
        env=windows_execution()
        protocol.require_machine(env)
        with patch.object(platform_env,'windows_power_status',return_value=json.loads(env['hardware']['power'])), \
                patch.object(platform_env,'command',return_value=env['hardware']['power_settings']):
            observed=platform_env.windows_power_observation()
        protocol.require_power(observed)
        self.assertEqual(observed['power_scheme'],SCHEME)

    def test_unknown_battery_saver_power_and_falsified_fields_fail_closed(self):
        for value in (windows_power(ac=0),windows_power(saver=1),windows_power(ac=255),windows_power(saver=255)):
            with self.subTest(value=value),self.assertRaises((RuntimeError,ValueError)):
                protocol.require_power(value)
        for key,value in (('power_source','Battery Power'),('lowpowermode','1'),('power_scheme','f'*36)):
            data=windows_power();data[key]=value
            with self.assertRaises(ValueError):protocol.require_power(data)
        data=windows_power();data['power_settings']='unknown scheme'
        with self.assertRaises(ValueError):protocol.require_power(data)

    def test_power_plan_change_and_machine_mix_are_rejected(self):
        first=windows_power();second=windows_power()
        other='8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
        second.update(power_scheme=other,power_settings=other)
        protocol.require_power(second)
        with self.assertRaisesRegex(ValueError,'power settings changed'):
            platform_env.require_power_binding(second,platform_env.power_binding(first))
        env=windows_execution()
        for key,value in (('python','3.15.2 TEST'),('python_optimize',1),('platform','macOS TEST')):
            bad=copy.deepcopy(env);bad[key]=value
            with self.assertRaises(RuntimeError):protocol.require_machine(bad)
        bad=copy.deepcopy(env);bad['hardware']['environment_schema']='unknown'
        with self.assertRaises(ValueError):protocol.require_machine(bad)

    def test_legacy_mac_remains_strict(self):
        from test_uninstrumented_protocol import power
        env=dict(hardware=dict(power(),**{'machdep.cpu.brand_string':'Apple M4'}),
                 python='3.12.14 TEST',python_optimize=0)
        protocol.require_machine(env)
        env['hardware']['machdep.cpu.brand_string']='another CPU'
        with self.assertRaises(RuntimeError):protocol.require_machine(env)

    def test_paths_and_empty_production_receipts(self):
        self.assertEqual(PureWindowsPath('src/a.py').as_posix(),'src/a.py')
        sources=source_identity()
        self.assertTrue(any(p.startswith('src/') for p in sources))
        self.assertTrue(all('\\' not in p for p in sources))
        receipt=dict(schema='representation_locality_cost_review_v1',approved=True,
                     production_sha256={},review_references=['TEST ONLY'])
        for sources in ({},{'src\\a.py':'0'*64}):
            with self.assertRaisesRegex(ValueError,'production source inventory'):
                check_review(receipt,sources)

    def test_atomic_record_replacement_and_io_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'file.json'
            with patch('committed_records.sys.platform','win32'):
                atomic_bytes(path,b'old')
                with patch('committed_records.os.replace',side_effect=PermissionError('TEST ONLY')):
                    with self.assertRaises(PermissionError):atomic_bytes(path,b'new')
                self.assertEqual(path.read_bytes(),b'old')
                self.assertEqual(list(path.parent.glob('*.partial')),[])
                atomic_json(path,{'text':'测试'})
                self.assertEqual(json.loads(path.read_bytes()),{'text':'测试'})
                commit_record(path.parent,0,{'status':'PASS'})
                (path.parent/'records'/'.abandoned.partial').write_bytes(b'not a record')
                self.assertEqual(read_records(path.parent),[{'status':'PASS'}])

    def test_real_timeout_preserves_committed_record(self):
        from common_input_protocol import ROOT
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'job'
            script=root/'child.py'
            script.write_text('import sys,time\nfrom pathlib import Path\n'
                'sys.path.insert(0,sys.argv[1])\nfrom committed_records import atomic_json,commit_record\n'
                'p=Path(sys.argv[2]);p.mkdir()\ncommit_record(p,0,{"status":"PASS"})\n'
                'atomic_json(p/"progress.json",{"status":"RUNNING"})\ntime.sleep(30)\n',encoding='utf-8')
            self.assertEqual(run_bounded([sys.executable,'-B',str(script),str(ROOT/'experiments'),str(out)],out,2),2)
            self.assertEqual(read_records(out),[{'status':'PASS'}])
            failure=json.loads((out/'failure.json').read_bytes())
            self.assertEqual(failure['status'],'RESOURCE_TIMEOUT')
            self.assertEqual(failure['committed_records'],1)
            self.assertFalse(failure['performance_eligible'])

    def test_real_worker_nonzero_exit_is_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'job'
            self.assertEqual(run_bounded([sys.executable,'-c','raise SystemExit(7)'],out,5),2)
            self.assertEqual(json.loads((out/'failure.json').read_bytes())['worker_exit_code'],7)
