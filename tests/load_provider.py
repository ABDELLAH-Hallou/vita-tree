"""Deterministic local provider: measured wait/gates plus existing typed outcomes."""
import atexit
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time

job=json.loads(Path('job.md').read_text(encoding='utf-8'))
control=Path(os.environ['VITA_TEST_CONTROL'])
step=sys.argv[1]
options=job.get('load',{})
ident=os.environ['VITA_TREE_EXECUTION_ID']
record=dict(label=job['label'],step=step,pid=os.getpid(),startedNs=time.monotonic_ns(),
            startedAt=time.time(),waitMs=0,barrierMs=0,credentialValid=False)
expected=options.get('keySha256')
record['credentialValid']=expected is None or hashlib.sha256(os.environ.get('OPENAI_API_KEY','').encode()).hexdigest()==expected
if not record['credentialValid']:raise SystemExit(9)
if options.get('spawnChild'):
    child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'],stdin=subprocess.DEVNULL)
    record['childPid']=child.pid
(control/(ident+'.started.json')).write_text(json.dumps(record),encoding='utf-8')

def finish():
    result=Path('.vita/results')/('tree-'+step+'.outcome.json')
    record.update(finishedNs=time.monotonic_ns(),finishedAt=time.time(),status=json.loads(result.read_text())['status'] if result.exists() else 'missing_outcome',
                  sourceSha256=hashlib.sha256(Path('main.tex').read_bytes()).hexdigest())
    (control/(ident+'.timing.json')).write_text(json.dumps(record),encoding='utf-8')

atexit.register(finish)
gate=options.get('gate')
if gate:
    started=time.monotonic()
    while not (control/(gate+'.release')).is_file():
        if time.monotonic()-started>options.get('gateSeconds',60):raise SystemExit(8)
        time.sleep(.01)
    record['barrierMs']=(time.monotonic()-started)*1000
started=time.monotonic()
time.sleep(options.get('delayMs',150)/1000)
record['waitMs']=(time.monotonic()-started)*1000
runpy.run_path(str(Path(__file__).with_name('fake_ai_process.py')),run_name='__main__')
