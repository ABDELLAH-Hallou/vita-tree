"""Controlled local AI CLI fixture; never calls a provider or the network."""
import atexit
import json
import hashlib
import os
from pathlib import Path
import sys
import time

step = sys.argv[1]
job = json.loads(Path('job.md').read_text())
control = Path(os.environ['VITA_TEST_CONTROL'])
label = job['label']
success = False

def outcome():
    if job.get('legacy_cli') or not os.environ.get('VITA_TREE_EXECUTION_ID'):
        return
    results = Path('.vita/results'); results.mkdir(parents=True, exist_ok=True)
    native = {'schema_version': 1, 'run_id': 'a'*32, 'step': step,
              'status': 'success' if success else 'failed',
              'attempts': [{'number': 1, 'category': 'valid' if success else 'provider_error', 'mode': 'validated_prompt'}],
              'error': None if success else {'code': 'provider_error'}}
    backend = {'status': native['status'], 'backendRunId': native['run_id'], 'attempts': native['attempts'],
               'errorCode': None if success else 'provider_error'} if step in {'extract','analyze','review'} else None
    (results/(step+'.outcome.json')).write_text(json.dumps(native))
    (results/('tree-'+step+'.outcome.json')).write_text(json.dumps({
        'schemaVersion': 1, 'adapter': 'vita-python-api-v1', 'executionId': os.environ['VITA_TREE_EXECUTION_ID'],
        'step': step, 'status': native['status'], 'verified': success, 'backend': backend}))

atexit.register(outcome)
with (control/(label+'.'+step+'.calls')).open('a') as calls:
    calls.write(hashlib.sha256(Path('main.tex').read_text(encoding='utf-8').encode()).hexdigest()+'\n')
if (control/(label+'.'+step+'.fail')).exists():
    raise SystemExit(1)
expected_ai = control / (label + '.' + step + '.expected-ai.json')
if expected_ai.exists():
    expected = json.loads(expected_ai.read_text())
    assert sys.argv[sys.argv.index('--provider') + 1] == expected['provider']
    config = json.loads(Path('.vita/extensions.json').read_text())
    assert config['llm_providers'][expected['provider']]['model'] == expected['model']
    assert os.environ['VITA_TREE_REASONING'] == expected.get('reasoning', '')
    assert os.environ[expected['provider'].upper() + '_API_KEY'] == expected['key']
    for prefix in ('EXTRACTION', 'ANALYSIS', 'ADAPT', 'REVIEW', 'COVER'):
        assert os.environ[prefix + '_PROVIDER'] == expected['provider']
        assert os.environ[prefix + '_MODEL'] == expected['model']
    (control / (label + '.' + step + '.verified-ai')).touch()
if job.get('pipeline'):
    (control / (label + '.' + step + '.started')).write_text(str(time.time()))
    if job.get('hold') == step:
        deadline = time.monotonic() + 120
        while not (control / (label + '.' + step + '.release')).exists():
            if time.monotonic() > deadline:
                raise SystemExit(2)
            time.sleep(.04)
    if job.get('fail') == step:
        raise SystemExit(1)
    assert os.environ['ENABLE_JD_EXTRACTION'] == 'false'
    if step in ('analyze', 'review') and job.get('extraction'):
        assert Path('.vita/results/job.json').is_file()
    if step == 'review' and job.get('require_adapted'):
        assert label + ' systems' in Path('main.tex').read_text()
    if step in ('adapt', 'review') and job.get('require_analysis'):
        assert Path('.vita/results/analysis.json').is_file()
    if step in ('adapt', 'review') and job.get('forbid_analysis'):
        assert not Path('.vita/results/analysis.json').exists()
        assert not Path('.vita/results/analyze.md').exists()
    if job.get('modify_cv') == step:
        Path('main.tex').write_text(Path('main.tex').read_text() + '\n% unexpected change')
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
if job.get('pipeline'):
    if step == 'extract':
        (results / 'job.json').write_text(json.dumps({'source_sha256': hashlib.sha256(Path('job.md').read_bytes()).hexdigest(), 'jobs': [{'id': 'job-1', 'title': 'Platform engineer'}]}))
        (results / 'job.toon').write_text('jobs[1]: Platform engineer')
    if step == 'analyze':
        (results / 'analysis.md').write_text('# Initial analysis\n\n## Evidence\n- **Python** services and automated tests.\n- Add more detail about delivery.\n\n| Category | Score |\n|---|---:|\n| Experience | 72 |\n| Skills | 80 |\n')
        (results / 'analysis.json').write_text(json.dumps({'overall_score': 76, 'metadata': {'job_sha256': hashlib.sha256(Path('job.md').read_bytes()).hexdigest()}}))
    if step == 'review':
        (results / 'review.json').write_text('{"overall_score":84}')
        if (results / 'analysis.json').is_file():
            (results / 'delta.json').write_text('{"delta":8}')
            (results / 'delta.md').write_text('# Evaluation changes\n\n| Score | Before | After | Delta |\n|---|---:|---:|---:|\n| Overall | 76 | 84 | +8 |\n')
    if step == 'cover':
        Path('cover-letter.tex').write_text('invalid' if job.get('invalid_cover') else r'\documentclass{article}\begin{document}Dear hiring team, I build reliable services.\end{document}')
if step == 'adapt':
    source = Path('main.tex').read_text()
    Path('main.tex').write_text('invalid source' if job.get('mode') == 'invalid' else source.replace('reliable', label))
    (control / (label + '.finished')).write_text(str(time.time()))

success = True
