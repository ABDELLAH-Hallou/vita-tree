"""Local, bounded diagnostics: controlled events, no request/provider payloads."""
from collections import Counter, deque
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import threading
import time
import traceback
import uuid

request_context = ContextVar('vita_tree_request_id', default=None)

ROUTES = {'/api/session', '/api/workspace', '/api/providers', '/api/job', '/api/jobs', '/api/connections', '/api/connections/remove', '/api/ai-settings', '/api/generation-check',
          '/api/job-result', '/api/pdf-file', '/api/branches', '/api/branch-content', '/health',
          '/api/release-worktree', '/api/job-reviewed', '/api/jobs-reviewed', '/api/save', '/api/commit-preview',
          '/api/commit-push', '/api/create', '/api/adapt', '/api/parse', '/api/lint', '/api/pdf',
          '/api/pdf-save', '/api/diagnostics', '/api/executions', '/api/execution',
          '/api/execution-artifact', '/api/execution-export', '/api/resume', '/api/resume-preview', '/metrics'}
EVENTS = {'server_started', 'server_stopped', 'logging_failed', 'request_finished', 'request_failed',
          'client_disconnected', 'history_write_failed', 'history_load_failed',
          'run_started', 'run_error', 'run_finished', 'step_started', 'step_finished',
          'review_saved', 'provider_failed', 'pdf_compiled', 'pdf_saved', 'pdf_failed',
          'execution_phase', 'checkpoint_cleanup_failed', 'publication_cleanup_failed', 'publication_recovery_failed'}
STEPS = {'extract', 'analyze', 'adapt', 'review', 'cover', 'validating', 'preparing', 'preflight'}


def default_log_directory(repository):
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    else:
        base = Path(os.environ.get('XDG_STATE_HOME', Path.home() / '.local/state'))
    key = hashlib.sha256(str(Path(repository).resolve()).encode()).hexdigest()[:12]
    return base / 'vita-tree' / 'logs' / key


class QuietRotatingHandler(RotatingFileHandler):
    def handleError(self, record):
        raise  # The owner keeps memory diagnostics available if the disk fails.


class Diagnostics:
    def __init__(self, directory=None, level='INFO'):
        self.lock = threading.RLock()
        self.started = time.monotonic()
        self.level = getattr(logging, level.upper())
        self.events = deque(maxlen=200)
        self.requests = Counter()
        self.request_seconds = Counter()
        self.runs = Counter()
        self.steps = Counter()
        self.step_seconds = Counter()
        self.errors = 0
        self.path = None
        self.file_error = None
        self.handler = None
        if directory is not None:
            try:
                directory = Path(directory).expanduser().resolve()
                directory.mkdir(parents=True, exist_ok=True)
                self.path = directory / ('vita-tree-' + str(os.getpid()) + '-' + uuid.uuid4().hex[:8] + '.jsonl')
                self.handler = QuietRotatingHandler(self.path, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
                self.handler.setFormatter(logging.Formatter('%(message)s'))
            except OSError as error:
                self.file_error = 'File logging is unavailable. Choose a writable folder with --log-dir.'
                self.error('logging_failed', error, operation='log_file')

    def record(self, event, level='INFO', **fields):
        if not isinstance(event, str) or event not in EVENTS:
            event = 'request_failed'
        if 'request_id' not in fields and request_context.get():
            fields['request_id'] = request_context.get()
        row = {'time': datetime.now(timezone.utc).isoformat(), 'level': level, 'event': event}
        for key, value in fields.items():
            if key in {'request_id', 'run_id', 'trace_id'} and isinstance(value, str) and re.fullmatch(r'[a-f0-9]{12,32}', value):
                row[key] = value
            elif key == 'step' and isinstance(value, str) and value in STEPS:
                row[key] = value
            elif key == 'route':
                route = str(value).split('?')[0]
                row[key] = route if route in ROUTES else 'other'
            elif key in {'operation', 'error_type', 'location', 'method'} and isinstance(value, str) and re.fullmatch(r'[a-zA-Z0-9_./:-]{1,100}', value):
                row[key] = value
            elif key == 'status' and (type(value) is int or isinstance(value, str) and value in {'running', 'succeeded', 'failed', 'interrupted', 'skipped', 'blocked', 'ok', 'error', 'reused', 'not_retained'}):
                row[key] = value
            elif key in {'errno', 'winerror', 'duration_ms', 'exit_code'} and type(value) in (int, float):
                row[key] = round(value, 3)
        with self.lock:
            if level == 'ERROR':
                self.errors += 1
            if getattr(logging, level) < self.level:
                return
            self.events.append(row)
            if self.handler:
                try:
                    entry = logging.LogRecord('vita_tree', getattr(logging, level), '', 0, json.dumps(row), (), None)
                    self.handler.handle(entry)
                except (OSError, ValueError) as error:
                    handler,self.handler=self.handler,None
                    try:
                        handler.close()
                    except OSError:
                        pass
                    self.file_error = 'File logging stopped. Check disk space and permissions or use --log-dir.'
                    self.error('logging_failed', error, operation='log_file')

    def error(self, event, error, level='ERROR', **fields):
        cause = error
        for _ in range(5):
            if cause.__cause__ is None:
                break
            cause = cause.__cause__
        frames = traceback.extract_tb(cause.__traceback__)
        location = None
        if frames:
            frame = frames[-1]
            location = Path(frame.filename).name + ':' + str(frame.lineno) + ':' + frame.name
        self.record(event, level, error_type=type(cause).__name__, errno=getattr(cause, 'errno', None),
                    winerror=getattr(cause, 'winerror', None), location=location, **fields)

    def request(self, method, route, status, seconds, request_id):
        route = route if route in ROUTES else 'other'
        key = (method, route, status)
        with self.lock:
            self.requests[key] += 1
            self.request_seconds[(method, route)] += seconds
        self.record('request_finished', 'INFO' if method == 'POST' or status >= 400 else 'DEBUG',
                    method=method, route=route, status=status, duration_ms=seconds*1000, request_id=request_id)

    def workflow(self, record, previous=None):
        previous = previous or {}
        ident = record['id']
        if not previous:
            with self.lock:
                self.runs['started'] += 1
            self.record('run_started', run_id=ident, trace_id=record.get('traceId'), status='running')
        old = {stage['id']: stage for stage in previous.get('stages') or []}
        for stage in record.get('stages') or []:
            before = old.get(stage['id'], {})
            if stage['status'] == before.get('status'):
                continue
            if stage['status'] == 'running':
                self.record('step_started', run_id=ident, trace_id=record.get('traceId'), step=stage['id'], status='running')
            elif before.get('status') == 'running':
                seconds = max(0, (stage.get('finishedAt') or time.time()) - (stage.get('startedAt') or time.time()))
                with self.lock:
                    self.steps[(stage['id'], stage['status'])] += 1
                    self.step_seconds[stage['id']] += seconds
                self.record('step_finished', run_id=ident, trace_id=record.get('traceId'), step=stage['id'], status=stage['status'], duration_ms=seconds*1000)
        if record['status'] != previous.get('status') and record['status'] in {'succeeded', 'failed', 'interrupted'}:
            with self.lock:
                self.runs[record['status']] += 1
            self.record('run_finished', 'ERROR' if record['status']=='failed' else 'INFO', run_id=ident, trace_id=record.get('traceId'), status=record['status'])

    def snapshot(self):
        with self.lock:
            total = sum(self.requests.values())
            return {'uptimeSeconds': round(time.monotonic()-self.started, 2), 'errors': self.errors,
                    'requests': {'total': total, 'failed': sum(n for (_, _, status), n in self.requests.items() if status >= 400),
                                 'meanMs': round(1000*sum(self.request_seconds.values())/total, 2) if total else 0},
                    'workflows': dict(self.runs), 'events': list(reversed(self.events)),
                    'logging': {'path': str(self.path) if self.path else None, 'enabled': bool(self.handler), 'error': self.file_error}}

    def prometheus(self, active=0):
        with self.lock:
            lines = ['# TYPE vita_tree_uptime_seconds gauge', f'vita_tree_uptime_seconds {time.monotonic()-self.started:.3f}',
                     '# TYPE vita_tree_active_runs gauge', f'vita_tree_active_runs {active}',
                     '# TYPE vita_tree_errors_total counter', f'vita_tree_errors_total {self.errors}',
                     '# TYPE vita_tree_http_requests_total counter']
            for (method, route, status), value in sorted(self.requests.items()):
                labels = 'method="'+method+'",route="'+route+'",status="'+str(status)+'"'
                lines.append('vita_tree_http_requests_total{'+labels+'} '+str(value))
            lines.append('# TYPE vita_tree_http_request_duration_seconds_sum counter')
            for (method, route), value in sorted(self.request_seconds.items()):
                lines.append('vita_tree_http_request_duration_seconds_sum{method="'+method+'",route="'+route+'"} '+str(value))
            lines.append('# TYPE vita_tree_workflow_runs_total counter')
            for status, value in sorted(self.runs.items()):
                lines.append('vita_tree_workflow_runs_total{status="'+status+'"} '+str(value))
            lines.append('# TYPE vita_tree_workflow_steps_total counter')
            for (step, status), value in sorted(self.steps.items()):
                lines.append('vita_tree_workflow_steps_total{step="'+step+'",status="'+status+'"} '+str(value))
            lines.append('# TYPE vita_tree_workflow_step_duration_seconds_sum counter')
            for step, value in sorted(self.step_seconds.items()):
                lines.append('vita_tree_workflow_step_duration_seconds_sum{step="'+step+'"} '+str(value))
            return '\n'.join(lines)+'\n'

    def close(self):
        with self.lock:
            if self.handler:
                self.handler.close()
                self.handler = None
