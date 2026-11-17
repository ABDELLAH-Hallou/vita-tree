"""Native job-context preparation followed by controlled, offline generation."""
import json
import os
from pathlib import Path
import runpy
import socket

from vita.helpers import env
from vita.helpers.job_extraction import prepare_job
from vita.helpers.pipeline_config import load_pipeline_settings


def forbidden(*args, **kwargs):
    raise AssertionError('No network calls in independent-step tests')


socket.create_connection = forbidden
socket.socket.connect = forbidden
original_load = env.load_env
env.load_env = lambda: {**original_load(), **os.environ}
settings = load_pipeline_settings()
assert not settings.extraction_enabled
job = prepare_job(settings, auto=True)
label = json.loads(Path('job.md').read_text(encoding='utf-8'))['label']
captured = {'jobHash': job.source_sha256, 'structured': job.structured,
            'revision': job.requirements['revision'] if job.requirements else None}
(Path(os.environ['VITA_TEST_CONTROL']) / (label + '.context.json')).write_text(json.dumps(captured))
runpy.run_path(str(Path(__file__).with_name('factual_ai.py')), run_name='__main__')
