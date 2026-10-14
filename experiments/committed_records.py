"""Small process-timeout-safe record store for bounded development runs.

Only final *.json.gz files are committed records. Each is a complete gzip
member, closed and fsynced before rename. *.partial files are uncommitted.
The guarantee concerns worker termination on a writable local filesystem;
I/O failures propagate, and this is not a power-loss/distributed-store claim.
"""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if sys.flags.optimize != 0:
    raise RuntimeError('Evidence checks require optimization level 0')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def atomic_bytes(path, data):
    path=Path(path)
    fd,temporary=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.partial',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        # On SIGKILL this may not execute. Readers ignore the partial file.
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_bytes(path,canonical(value)+b'\n')


def commit_record(output, index, row):
    directory=Path(output)/'records'
    directory.mkdir(exist_ok=True)
    path=directory/f'{index:06d}.json.gz'
    if path.exists():
        raise FileExistsError(path)
    atomic_bytes(path,gzip.compress(canonical(row)+b'\n',mtime=0))


def read_records(output):
    paths=sorted((Path(output)/'records').glob('*.json.gz'))
    rows=[]
    for index,path in enumerate(paths):
        if path.name!=f'{index:06d}.json.gz' or path.is_symlink() or not path.is_file():
            raise ValueError('non-contiguous or non-regular committed records')
        with gzip.open(path,'rt') as stream:
            rows.append(json.load(stream))
    return rows


def run_bounded(command, output, seconds):
    """Parent records timeout/current action after subprocess.run kills and waits."""
    output=Path(output)
    try:
        result=subprocess.run(command,timeout=seconds,check=False)
        if result.returncode==0:
            return 0
        status='WORKER_ERROR'
        details={'worker_exit_code':result.returncode}
    except subprocess.TimeoutExpired:
        status='RESOURCE_TIMEOUT'
        details={'budget_seconds':seconds}
    output.mkdir(parents=True,exist_ok=True)
    current=None
    if (output/'progress.json').exists():
        current=json.loads((output/'progress.json').read_text())
    previous={}
    if (output/'failure.json').exists():
        previous=json.loads((output/'failure.json').read_text())
    failure={**previous,**details,'accepted':False,'status':status,'current':current,
             'committed_records':len(read_records(output)),'performance_eligible':False}
    atomic_json(output/'failure.json',failure)
    # Timeout wins even if the worker wrote its summary just before termination.
    if (output/'summary.json').exists():
        summary=json.loads((output/'summary.json').read_text())
        summary.update(accepted=False,completed_successfully=False,status=status)
        atomic_json(output/'summary.json',summary)
    return 2
