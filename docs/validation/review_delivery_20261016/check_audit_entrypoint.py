"""Check the real auxiliary script's entrypoint, without running sorting."""
import sys

if sys.flags.optimize:
    raise RuntimeError("Run evidence checks without Python optimization")

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SCRIPT = ROOT / 'docs/validation/join_proof_correction_20261016/audit_crosscheck.py'
EXPECTED = ROOT / 'docs/validation/join_proof_correction_20261016/crosscheck_report.json'


def require(value, context):
    if not value:
        raise RuntimeError(context)


env = dict(os.environ)
env.pop('PYTHONOPTIMIZE', None)
rows = []
with tempfile.TemporaryDirectory() as directory:
    sandbox = Path(directory)
    # Byte-identical script in a directory with no archives: the optimization
    # rejection must occur before any evidence read could succeed.
    isolated = sandbox / 'repo/docs/validation/join_proof_correction_20261016/audit_crosscheck.py'
    isolated.parent.mkdir(parents=True)
    isolated.write_bytes(SCRIPT.read_bytes())
    modes = [('flag-O', ['-O'], None), ('flag-OO', ['-OO'], None),
             ('env-1', [], '1'), ('env-2', [], '2')]
    for name, flags, setting in modes:
        output = sandbox / (name + '.json')
        config = dict(env)
        if setting is not None:
            config['PYTHONOPTIMIZE'] = setting
        process = subprocess.run([sys.executable, *flags, str(isolated), '--output', str(output)],
                                 env=config, capture_output=True, text=True)
        require(process.returncode != 0, name + ': unexpected success')
        require('Run evidence checks without Python optimization' in process.stderr, name + ': wrong rejection')
        require('FileNotFoundError' not in process.stderr and not process.stdout and not output.exists(), name + ': I/O before rejection')
        rows.append({'mode': name, 'exit_code': process.returncode, 'stdout': process.stdout,
                     'stderr': process.stderr, 'report_created': output.exists()})
    control = subprocess.run([sys.executable, str(isolated)], env=env, capture_output=True, text=True)
    require(control.returncode != 0 and 'FileNotFoundError' in control.stderr, 'missing-archive control')
    destination = sandbox / 'normal-report.json'
    process = subprocess.run([sys.executable, str(SCRIPT), '--output', str(destination)],
                             cwd=ROOT, env=env, capture_output=True, text=True)
    require(process.returncode == 0, process.stderr)
    require(destination.read_bytes() == EXPECTED.read_bytes(), 'normal report changed')
    with (HERE / 'audit_crosscheck_report.json').open('xb') as stream:
        stream.write(destination.read_bytes())
    result = {'script_sha256': hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
              'python': sys.version, 'optimized_entrypoints': rows,
              'missing_archive_normal_control_exit': control.returncode,
              'normal_actual_archive_exit': process.returncode,
              'normal_report_byte_identical_to_prior': True,
              'subprocesses': 6, 'sorting_runs': 0,
              'scope': 'Four optimized executions of a byte-identical isolated script, one missing-archive control, one normal full saved-evidence check.'}
    with (HERE / 'entrypoint_checks.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
print('PASS: four optimization modes rejected before archive reads/report writes; normal full check matches the prior report.')
