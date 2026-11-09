"""Defensive reader for Vita CV diagnostics v1 (not its business outcomes).

Vocabulary and structural artifacts follow vita.helpers.diagnostics_contract
and the upstream fixtures pinned in tests/fixtures/diagnostics. No terminal
output, source files, environment dictionaries, or provider prose are accepted.
"""
import json
import math
import re
from datetime import datetime, timezone

VERSION = 1
CAPTURES = {'captured', 'redacted', 'disabled', 'suppressed', 'truncated', 'unavailable'}
PHASES = {'workflow', 'step', 'configuration', 'context', 'prompt', 'provider_request', 'decoding', 'validation', 'persistence'}
EVENTS = {'span_start', 'span_end', 'attempt', 'retry', 'route', 'capture', 'error', 'cache'}
CATEGORIES = {'configuration', 'authentication', 'permission', 'overloaded', 'rate_limit', 'server_error',
              'timeout', 'connection', 'tls', 'invalid_model', 'quota_exceeded', 'invalid_request', 'not_found',
              'unsupported_schema', 'refusal', 'incomplete_response', 'empty_response', 'provider_error',
              'response_shape', 'response_decode', 'invalid_json', 'schema_error', 'validation_error',
              'artifact_error', 'unclassified', 'interrupted'}
PROVIDERS = {'openai', 'openrouter', 'gemini', 'google', 'codex', 'anthropic', 'groq', 'mistral', 'deepseek', 'xai', 'together', 'perplexity', 'cohere'}
STEPS = {'extract', 'requirements', 'analyze', 'adapt', 'review', 'cover', 'analyze-qualitative', 'review-qualitative', 'provider-check', 'provider-discovery', 'operation'}
KINDS = {'request', 'response', 'http_response', 'provider_error', 'schema', 'instructions'}
ORIGINS = {'process', 'project_env', 'extensions', 'explicit', 'default', 'cli_inherited', 'absent', 'unreported'}
PROVIDER_CODES = {'UNAVAILABLE', 'RESOURCE_EXHAUSTED', 'UNAUTHENTICATED', 'PERMISSION_DENIED', 'NOT_FOUND', 'INVALID_ARGUMENT', 'model_not_found', 'invalid_model', 'invalid_api_key', 'insufficient_quota', 'rate_limit_exceeded', 'unclassified'}
EXCEPTIONS = {'RuntimeError','AttributeError','IndexError','RecursionError','ValueError','TypeError','KeyError',
              'OSError','PermissionError','FileNotFoundError','TimeoutError','JSONDecodeError','UnicodeDecodeError',
              'HTTPError','URLError','SSLError','SSLCertVerificationError','ProviderError','UnsupportedSchema',
              'StructuredOutputError','KeyboardInterrupt','SystemExit','unclassified_exception'}
FIELDS = {'schema_version','overall_score','category_scores','executive_summary','strengths','gaps','recommendations',
          'metrics','criteria','id','job_id','category','criterion','importance','status','evidence','evidence_kind',
          'evidence_refs','feedback','source_id','quote','line_start','line_end','matched_count','partial_count',
          'missing_count','total_count','source_sha256','jobs','title','company','location','requirements','answer'}
SHAPE_FIELDS = {'error','code','status','message','choices','candidates','content','parts','text','finish_reason',
                'finishReason','refusal','model','schema_version','overall_score','category_scores','metrics','criteria',
                'id','evidence','strengths','gaps','recommendations','jobs','title','company','[REDACTED_FIELD]'}
SCHEMA_FIELDS = FIELDS | {'date_posted','hard_skills','soft_skills','must_have','nice_to_have','responsibilities','summary','[CUSTOM_FIELD]'}
REASONS = {'not_observed','sensitive_sections_replaced','host_safe_summary','schema_structure_only','no_model_response_produced',
           'no_http_response','content_capture_off','all_source_values_removed','cannot_establish_safe_structure',
           'artifact_size_limit','logging_failure'}

class UnsupportedContract(ValueError):
    pass


def ident(value, length=32):
    return value if isinstance(value, str) and re.fullmatch('[0-9a-f]{'+str(length)+'}', value) and int(value, 16) else None


def number(value, maximum=10**12):
    # Check the integer bound before float conversion inside isfinite: a
    # tampered JSON integer can exceed a float's range even in a small file.
    return value if type(value) in (int, float) and 0 <= value <= maximum and math.isfinite(value) else None


def timestamp(value):
    if isinstance(value, str) and len(value) <= 40:
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if parsed.tzinfo:
                return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    return None


def token(value, secrets=()):
    if (isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:+/-]{0,159}', value)
            and not re.search(r'://|\\|@|sk-|AIza|Bearer|api[_-]?key|^[A-Za-z]:|^/', value, re.I)
            and not any(secret and secret in value for secret in secrets)):
        return value
    return None


def details(raw, secrets=()):
    if not isinstance(raw, dict):
        return {}
    result = {}
    for key, value in raw.items():
        if key in {'attempt','attempts','max_attempts','http_status','line','column','offset','bytes','chars'}:
            if type(value) is int and number(value) is not None:
                result[key] = value
        elif key in {'duration_ms','delay_seconds','retry_after_seconds'}:
            if number(value, 10**18) is not None:
                result[key] = round(value, 3)
        elif key in {'requested_provider','effective_provider'}:
            result[key] = value if isinstance(value, str) and value in PROVIDERS else None
        elif key in {'requested_model','effective_model','reasoning'}:
            result[key] = token(value, secrets)
        elif key in {'prompt_sha256','schema_sha256','adapter_sha256','request_id_sha256'}:
            if ident(value, 64):
                result[key] = value
        elif key == 'outcome_run_id' and ident(value):
            result[key] = value
        elif key == 'category':
            result[key] = value if isinstance(value, str) and value in CATEGORIES else 'unclassified'
        elif key in {'retryable','credential_present','response_exists','http_response_exists','reused'}:
            if type(value) is bool or value is None:
                result[key] = value
        elif key == 'credential_variable':
            if isinstance(value, str) and value in {p.upper()+'_API_KEY' for p in PROVIDERS}:
                result[key] = value
        elif key.endswith('_origin') and key in {'credential_origin','provider_origin','model_origin','reasoning_origin'}:
            result[key] = value if isinstance(value, str) and value in ORIGINS else 'unreported'
        elif key == 'provider_code':
            result[key] = value if isinstance(value, str) and value in PROVIDER_CODES else 'unclassified'
        elif key == 'location' and isinstance(value, str) and re.fullmatch(r'\$(?:\.[a-z_]{1,40}|\[\d{1,6}\]){0,12}', value):
            if all(field in FIELDS for field in re.findall(r'\.([a-z_]+)', value)):
                result[key] = value
        elif key == 'exception_type':
            result[key] = value if isinstance(value, str) and value in EXCEPTIONS else 'unclassified_exception'
    return result


def frames(raw):
    result = []
    for item in raw[:8] if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        module = item.get('module')
        if (module == 'external' or isinstance(module, str) and re.fullmatch(r'(?:helpers|commands)/[a-z_]+\.py', module)):
            if type(item.get('line')) is int and number(item['line']) is not None:
                result.append({'module': module, 'line': item['line']})
    return result


def reference(raw, process_id):
    if not isinstance(raw, dict) or not ident(raw.get('id')) or raw.get('kind') not in KINDS or raw.get('capture_status') not in CAPTURES:
        raise ValueError('Invalid diagnostic artifact reference')
    path = raw.get('path')
    expected = 'artifacts/'+process_id+'-'+raw['id']+'.json'
    if path is not None and path != expected:
        raise ValueError('Invalid diagnostic artifact location')
    size = raw.get('bytes')
    if type(size) is not int or not 0 <= size <= 16384:
        raise ValueError('Invalid diagnostic artifact size')
    return {'id': raw['id'], 'processId': process_id, 'kind': raw['kind'], 'capture_status': raw['capture_status'],
            'step_id': ident(raw.get('step_id')), 'attempt_id': ident(raw.get('attempt_id')),
            'reason': raw.get('reason') if isinstance(raw.get('reason'), str) and raw['reason'] in REASONS else 'not_observed',
            'content_exists': raw.get('content_exists') if type(raw.get('content_exists')) is bool else None,
            'path': path, 'bytes': size}


def check(raw, trace_id):
    if not isinstance(raw, dict) or type(raw.get('schema_version')) is not int or raw.get('schema_version') != VERSION:
        raise UnsupportedContract('Unsupported diagnostics contract version')
    if raw.get('trace_id') != trace_id:
        raise ValueError('Inconsistent diagnostic trace identity')


def event(raw, trace_id, process_id, secrets=()):
    check(raw, trace_id)
    if raw.get('process_id') != process_id or raw.get('event') not in EVENTS or raw.get('phase') not in PHASES:
        raise ValueError('Invalid diagnostic event')
    if type(raw.get('sequence')) is not int or not 0 <= raw['sequence'] <= 10**12 or not timestamp(raw.get('timestamp')):
        raise ValueError('Invalid diagnostic event ordering')
    if raw.get('status') not in {'ok','error','running','interrupted'}:
        raise ValueError('Invalid diagnostic event status')
    if not ident(raw.get('workflow_id')):
        raise ValueError('Invalid diagnostic workflow identity')
    for key in ('step_id','attempt_id','span_id','parent_span_id'):
        if raw.get(key) is not None and not ident(raw[key],16 if 'span' in key else 32):
            raise ValueError('Invalid diagnostic correlation identity')
    return {'schema_version': 1, 'trace_id': trace_id, 'process_id': process_id,
            **{key: ident(raw.get(key), 16 if 'span' in key else 32) for key in ('workflow_id','step_id','attempt_id','span_id','parent_span_id')},
            'step': raw.get('step') if isinstance(raw.get('step'), str) and raw['step'] in STEPS else None,
            'sequence': raw['sequence'], 'timestamp': timestamp(raw['timestamp']), 'event': raw['event'],
            'phase': raw['phase'], 'status': raw['status'], 'details': details(raw.get('details'), secrets)}


def process(raw, trace_id, process_id, secrets=()):
    check(raw, trace_id)
    if raw.get('process_id') != process_id or raw.get('status') not in {'running','success','failed','interrupted','incomplete'}:
        raise ValueError('Invalid diagnostic process identity or status')
    refs = raw.get('diagnostic_artifacts')
    if not isinstance(refs, list) or len(refs) > 100:
        raise ValueError('Invalid diagnostic artifact list')
    if (type(raw.get('capture_enabled')) is not bool or type(raw.get('logging_complete')) is not bool
            or not timestamp(raw.get('updated_at')) or not token(raw.get('product_version'),secrets)):
        raise ValueError('Incomplete diagnostic process contract')
    failure = raw.get('failure')
    safe_failure = None
    if isinstance(failure, dict):
        if failure.get('phase') not in PHASES:
            raise ValueError('Invalid diagnostic failure phase')
        safe_failure = {'phase': failure.get('phase') if failure.get('phase') in PHASES else 'step',
                        'details': details(failure.get('details'), secrets), 'frames': frames(failure.get('frames'))}
    return {'schema_version': 1, 'process_id': process_id,
            'product_version': token(raw.get('product_version'), secrets),
            'status': raw['status'] if raw['status'] != 'running' else 'incomplete_or_running',
            'updated_at': timestamp(raw.get('updated_at')), 'failure': safe_failure,
            'capture_enabled': raw.get('capture_enabled') is True, 'logging_complete': raw.get('logging_complete') is True,
            'diagnostic_artifacts': [reference(item, process_id) for item in refs]}


def shape(value, depth=0):
    """Reconstruct only the backend's value-free structural capture grammar."""
    if depth > 10 or not isinstance(value, dict):
        raise ValueError('Unsafe diagnostic structure')
    if value.get('capture_status') in {'suppressed','truncated'}:
        return {'capture_status': value['capture_status']}
    kind = value.get('type')
    if kind == 'object':
        fields = value.get('fields')
        if not isinstance(fields, list) or len(fields) > 30:
            raise ValueError('Unsafe diagnostic fields')
        result = []
        for item in fields:
            if not isinstance(item, dict) or item.get('field') not in SHAPE_FIELDS:
                raise ValueError('Unsafe diagnostic field')
            result.append({'field': item['field'], 'value': shape(item.get('value'), depth+1)})
        return {'type': 'object', 'fields': result, 'field_count': number(value.get('field_count'))}
    if kind == 'array':
        items = value.get('items')
        if not isinstance(items, list) or len(items) > 10:
            raise ValueError('Unsafe diagnostic array')
        return {'type': 'array', 'length': number(value.get('length')), 'items': [shape(v, depth+1) for v in items]}
    if kind in {'str','int','float','bool','NoneType','unknown'} and value.get('value') == '[REDACTED]':
        return {'type': kind, 'value': '[REDACTED]', 'chars': number(value.get('chars'))}
    raise ValueError('Unsafe diagnostic scalar')


def schema_view(value, depth=0):
    if depth > 10 or not isinstance(value, dict):
        raise ValueError('Unsafe schema capture')
    if value.get('capture_status') == 'suppressed':
        return {'capture_status': 'suppressed'}
    types = value.get('type')
    if not isinstance(types, list) or len(types) > 7 or any(t not in {'string','object','array','number','integer','boolean','null'} for t in types):
        raise ValueError('Unsafe schema types')
    result = {'type': types, 'required_count': number(value.get('required_count'))}
    if 'properties' in value:
        props = value['properties']
        if not isinstance(props, list) or len(props) > 100:
            raise ValueError('Unsafe schema fields')
        result['properties'] = []
        for item in props:
            if not isinstance(item, dict) or item.get('field') not in SCHEMA_FIELDS:
                raise ValueError('Unsafe schema field')
            result['properties'].append({'field': item['field'], 'schema': schema_view(item.get('schema'), depth+1)})
    if 'items' in value:
        result['items'] = schema_view(value['items'], depth+1)
    return result


def artifact(raw, ref):
    if (not isinstance(raw, dict) or type(raw.get('schema_version')) is not int or raw['schema_version'] != 1
            or raw.get('kind') != ref['kind'] or raw.get('capture_status') != ref['capture_status']):
        raise ValueError('Inconsistent diagnostic artifact')
    data = raw.get('data')
    if raw['capture_status'] == 'truncated' and data == {'content':'[SUPPRESSED_SIZE_LIMIT]'}:
        safe = data
    elif raw['kind'] == 'request':
        sections = data.get('sections') if isinstance(data, dict) else None
        if not isinstance(sections, list) or len(sections) > 30 or data.get('exact_prompt_captured') is not False:
            raise ValueError('Unsafe request structure')
        safe = {'sections': [], 'exact_prompt_captured': False}
        for section in sections:
            if not isinstance(section, dict) or section.get('label') not in {'system','user','sensitive_section'} or section.get('content') != '[SENSITIVE_CONTENT]':
                raise ValueError('Unsafe request section')
            safe['sections'].append({'label': section['label'], 'content':'[SENSITIVE_CONTENT]',
                                     'chars': number(section.get('chars')), 'lines': number(section.get('lines'))})
    elif raw['kind'] == 'instructions':
        # The host-authored summary is a fixed contract, never user prose.
        safe = {'source':'diagnostic-summary-not-exact-prompt',
                'instructions':['Use the supplied evidence only.','Follow the host output contract and validation.']}
        if data != safe:
            raise ValueError('Unrecognized instruction summary')
    elif raw['kind'] == 'schema':
        safe = schema_view(data)
    else:
        safe = shape(data)
    return {'schema_version':1, 'kind':raw['kind'], 'capture_status':raw['capture_status'], 'data':safe}


def load(path, maximum):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('Diagnostic artifact is missing, linked, or too large')
    with path.open('rb') as stream:
        content = stream.read(maximum+1)
    if len(content) > maximum:
        raise ValueError('Diagnostic artifact exceeds the limit')
    return json.loads(content.decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON')))
