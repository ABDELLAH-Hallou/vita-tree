"""Controlled local AI CLI fixture; never calls a provider or the network."""
import json
import os
from pathlib import Path
import sys
import time

step = sys.argv[1]
job = json.loads(Path('job.md').read_text())
control = Path(os.environ['VITA_TEST_CONTROL'])
label = job['label']
if step == 'analyze':
    (control / (label + '.started')).write_text(str(time.time()))
    deadline = time.monotonic() + 120
    while not (control / (label + '.release')).exists():
        if time.monotonic() > deadline:
            raise SystemExit(2)
        time.sleep(.04)
    if job.get('mode') == 'provider-fail':
        print(os.environ.get('VITA_TEST_SECRET', 'fixture-private-output'))
        raise SystemExit(1)
results = Path('.vita/results')
results.mkdir(parents=True, exist_ok=True)
(results / (step + '.md')).write_text('# ' + label + ' ' + step)
if step == 'adapt':
    source = Path('main.tex').read_text()
    Path('main.tex').write_text('invalid source' if job.get('mode') == 'invalid' else source.replace('reliable', label))
    (control / (label + '.finished')).write_text(str(time.time()))
