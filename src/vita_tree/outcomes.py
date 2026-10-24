"""Normalize Vita CV's boolean command API and structured format outcomes.

The adapter is versioned separately from Vita CV's schema_version=1 format trace.
It never examines stdout or provider prose. Unsupported CLI integrations can still
run normally, but cannot create verified resumable checkpoints.
"""
import json
import os
from pathlib import Path
import re
try:
    from .diagnostics_contract import details, CATEGORIES as DIAGNOSTIC_CATEGORIES
    from .provider_status import provider_error
except ImportError:  # ai_runner.py also runs directly in the isolated child.
    from diagnostics_contract import details, CATEGORIES as DIAGNOSTIC_CATEGORIES
    from provider_status import provider_error

CATEGORIES = {'valid', 'invalid_json', 'schema_error', 'validation_error', 'unsupported_schema',
              'provider_error', 'authentication', 'rate_limit', 'timeout', 'started'} | DIAGNOSTIC_CATEGORIES
MODES = {'native_schema', 'validated_prompt', 'schema_requested'}
CODES = {'structured_output_invalid', 'provider_error', 'artifact_error', 'backend_error'}


def safe_outcome(data, secrets=()):
    secrets = tuple(secrets) + tuple(v for k,v in os.environ.items() if any(part in k.upper() for part in ('KEY','TOKEN','SECRET','PASSWORD')) and v)
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        return None
    if data.get('status') not in {'success', 'failed', 'running'}:
        return None
    items = data.get('attempts')
    if not isinstance(items, list) or len(items) > 100:
        return None
    attempts = []
    for item in items:
        if not isinstance(item, dict) or type(item.get('number')) is not int or not 1 <= item['number'] <= 100:
            return None
        attempts.append({'number': item['number'],
                         'category': item.get('category') if item.get('category') in CATEGORIES else 'provider_error',
                         'mode': item.get('mode') if item.get('mode') in MODES else None})
        technical = details({**(item.get('details') if isinstance(item.get('details'), dict) else {}),
                             **{key: item[key] for key in ('http_status','retryable','retry_after_seconds') if key in item},
                             **({'delay_seconds':item['retry_delay_seconds']} if 'retry_delay_seconds' in item else {})}, secrets)
        if technical:
            attempts[-1]['details'] = technical
    error = data.get('error')
    if isinstance(error, dict) and 'schema_version' in error and (type(error['schema_version']) is not int or error['schema_version'] != 1):
        error = None
    technical_error = details({**error, **({'http_status':error['status']} if 'status' in error else {}),
                               **({'effective_provider':error['provider']} if 'provider' in error else {}),
                               **({'effective_model':error['model']} if 'model' in error else {})}, secrets) if isinstance(error, dict) else {}
    return {'status': data['status'], 'attempts': attempts,
            'backendRunId': data.get('run_id') if re.fullmatch(r'[a-f0-9]{32}', str(data.get('run_id', ''))) else None,
            'errorDetails': technical_error, 'providerError': provider_error(error, secrets),
            'errorCode': error.get('code') if isinstance(error, dict) and error.get('code') in CODES else None}


def execute(step, invoke, execution_id):
    """Invoke exactly the API used by Vita CV's CLI, retaining its typed trace."""
    folder = Path('.vita/results')
    native = folder / (step + '.outcome.json')
    native.unlink(missing_ok=True)
    requirements_trace = folder/'tree-requirements-native.json'
    if step == 'extract':
        requirements_trace.unlink(missing_ok=True)
    result = False
    api_result = None
    try:
        api_result = invoke()
        result = api_result is not False
        return result
    finally:
        if step in {'adapt', 'cover'}:
            try:
                from .factual_backend import capture
            except ImportError:
                from factual_backend import capture
            capture(step, execution_id)
        trace = None
        expected_step = step
        if step == 'extract' and requirements_trace.is_file():
            native, expected_step = requirements_trace, 'requirements'
        if native.is_file() and native.stat().st_size < 200_000:
            try:
                raw = json.loads(native.read_text(encoding='utf-8'))
                if raw.get('step') == expected_step:
                    trace = safe_outcome(raw, [v for k,v in os.environ.items() if any(part in k.upper() for part in ('KEY','TOKEN','SECRET','PASSWORD'))])
            except (OSError, ValueError, AttributeError):
                pass
        structured = step in {'extract', 'analyze', 'review'}
        verified = result and api_result is True and (not structured or bool(trace and trace['status'] == 'success'))
        value = {'schemaVersion': 1, 'adapter': 'vita-python-api-v1', 'step': step,
                 'executionId': execution_id, 'status': 'success' if result else 'failed',
                 'verified': verified, 'backend': trace}
        folder.mkdir(parents=True, exist_ok=True)
        # This child is the sole writer; checkpoints are published atomically by
        # the parent only after the process exits and output checks pass.
        (folder / ('tree-' + step + '.outcome.json')).write_text(json.dumps(value), encoding='utf-8')


def read_outcome(folder, step, execution_id):
    path = folder / '.vita/results' / ('tree-' + step + '.outcome.json')
    try:
        if path.is_symlink() or path.stat().st_size > 200_000:
            return None
        data = json.loads(path.read_text(encoding='utf-8'))
        if (data.get('schemaVersion') != 1 or data.get('adapter') != 'vita-python-api-v1'
                or data.get('executionId') != execution_id or data.get('step') != step
                or data.get('status') not in {'success', 'failed'}):
            return None
        native = data.get('backend')
        # Sanitize again at the parent trust boundary. Never expose raw traces.
        if native is not None:
            native = safe_outcome({'schema_version': 1, 'status': native.get('status'),
                                   'attempts': native.get('attempts'), 'run_id': native.get('backendRunId'),
                                   'error': {**(native.get('providerError') or {}), **(native.get('errorDetails') if isinstance(native.get('errorDetails'),dict) else {}), 'code': native.get('errorCode')}})
        return {'status': data['status'], 'verified': data.get('verified') is True and (step not in {'extract','analyze','review'} or bool(native and native['status'] == 'success' and native['attempts'] and native['attempts'][-1]['category'] == 'valid')),
                'backend': native}
    except (OSError, ValueError, AttributeError, TypeError):
        return None
