"""Allowlisted Vita CV provider-error/check v1 consumer and user actions.

Never trust upstream prose, stdout, or stderr as public messages.
"""
try:
    from .diagnostics_contract import CATEGORIES, PROVIDERS, token, number
except ImportError:  # Direct ai_runner.py child
    from diagnostics_contract import CATEGORIES, PROVIDERS, token, number

ACTIONS = {
    'overloaded': ('Service temporarily busy', 'Wait a little, then retry this preparation. Changing your API key is not indicated.'),
    'rate_limit': ('Request limit reached', 'Wait for the provider limit to reset, then retry. Reduce simultaneous requests if needed.'),
    'server_error': ('Temporary service failure', 'Wait a little, then retry the same provider and model.'),
    'timeout': ('Request timed out', 'Check connectivity and retry. The provider may have processed the earlier request.'),
    'connection': ('Connection interrupted', 'Check your network connection, then retry.'),
    'authentication': ('Sign-in or API key rejected', 'Reconnect this provider or replace its API key, then explicitly choose the repaired setup when retrying.'),
    'permission': ('Model access denied', 'Check this account’s access to the selected model. Choose an accessible model explicitly if needed.'),
    'invalid_model': ('Model unavailable', 'Check the exact model ID and your account’s access. Update the setup explicitly before retrying.'),
    'configuration': ('AI setup needs attention', 'Check the selected provider, model, reasoning, and connection before retrying.'),
    'quota_exceeded': ('Provider quota exhausted', 'Check billing and usage limits with this provider before retrying.'),
    'invalid_request': ('Request rejected', 'Check model capabilities and the selected setup. Inspect execution details before retrying.'),
    'not_found': ('Provider endpoint not found', 'Check the configured endpoint and model ID before retrying.'),
    'invalid_json': ('Response was not valid JSON', 'Inspect execution details and retry. If repeated, choose a model supporting structured output.'),
    'schema_error': ('Response did not match the expected format', 'Inspect validation details. Retry or explicitly choose a model supporting the required format.'),
    'validation_error': ('Response failed validation', 'Inspect validation details and requirements before retrying. Existing application files are preserved.'),
    'unsupported_schema': ('Required format is unsupported', 'Explicitly choose a model supporting this structured format before retrying.'),
    'refusal': ('Provider declined the request', 'Review the provider restrictions and the application inputs before retrying.'),
    'empty_response': ('Provider returned no content', 'Inspect execution details and retry. Check the selected model if this repeats.'),
    'incomplete_response': ('Provider returned an incomplete response', 'Inspect execution details and the model limits before retrying.'),
}
DEFAULT = ('Preparation could not finish', 'Inspect execution details before retrying. No credential problem has been established.')


def provider_error(raw, secrets=()):
    """Read v1 or the same previously normalized v1; unknown versions fail closed."""
    if (not isinstance(raw, dict) or type(raw.get('schema_version')) is not int
            or raw['schema_version'] != 1 or raw.get('code') != 'provider_error'
            or not isinstance(raw.get('category'), str) or raw['category'] not in CATEGORIES
            or type(raw.get('retryable')) is not bool):
        return None
    result = {'schema_version': 1, 'code': 'provider_error', 'category': raw['category'],
              'provider': raw.get('provider') if isinstance(raw.get('provider'), str) and raw['provider'] in PROVIDERS else None,
              'model': token(raw.get('model'), secrets), 'retryable': raw['retryable']}
    for key in ('attempts', 'max_attempts'):
        value = raw.get(key)
        if type(value) is int and 0 <= value <= 5:
            result[key] = value
    if type(raw.get('status')) is int and 100 <= raw['status'] <= 599:
        result['status'] = raw['status']
    if type(raw.get('exhausted')) is bool:
        result['exhausted'] = raw['exhausted']
    delay = number(raw.get('retry_after_seconds'), 10**18)
    if delay is not None:
        result['retry_after_seconds'] = delay
    if raw.get('retry_stopped') == 'retry_after_exceeds_delay_cap':
        result['retry_stopped'] = raw['retry_stopped']
    return result


def failure(outcome):
    if not isinstance(outcome, dict) or outcome.get('status') != 'failed':
        return None
    native = outcome.get('backend') or {}
    error = provider_error(native.get('providerError')) or {}
    detail = native.get('errorDetails') or {}
    attempts = native.get('attempts') or []
    category = error.get('category') or detail.get('category') or (attempts[-1].get('category') if attempts else None)
    category = category if category in CATEGORIES else 'unclassified'
    title, action = ACTIONS.get(category, DEFAULT)
    retryable = error.get('retryable', detail.get('retryable'))
    return {'category': category, 'title': title, 'action': action,
            'provider': error.get('provider') or detail.get('effective_provider'),
            'model': error.get('model') or detail.get('effective_model'),
            'routeEvidence': 'backend' if error.get('provider') or detail.get('effective_provider') else 'unreported',
            'retryable': retryable if type(retryable) is bool else None,
            'attempts': error.get('attempts', len(attempts) if attempts else None),
            'httpStatus': error.get('status', detail.get('http_status')),
            'exhausted': error.get('exhausted'),
            'retryAfterSeconds': error.get('retry_after_seconds', detail.get('retry_after_seconds'))}


def generation_result(raw, secrets=()):
    if (not isinstance(raw, dict) or type(raw.get('schema_version')) is not int or raw['schema_version'] != 1
            or raw.get('check') != 'generation' or not isinstance(raw.get('status'),str) or raw['status'] not in {'success', 'failed'}
            or type(raw.get('generation_verified')) is not bool or raw.get('may_consume_usage') is not True):
        raise ValueError('Generation check evidence is unavailable. Update Vita CV to a version supporting provider-check v1.')
    error = provider_error(raw.get('error'), secrets)
    if raw['status'] == 'success' and (raw.get('error') is not None or raw['generation_verified'] is not True):
        raise ValueError('Generation check returned inconsistent success evidence.')
    verified = raw['status'] == 'success' and raw['generation_verified'] and error is None
    attempts = raw.get('attempts')
    return {'status': 'success' if verified else 'failed', 'generationVerified': verified,
            'provider': raw.get('provider') if isinstance(raw.get('provider'), str) and raw['provider'] in PROVIDERS else (error or {}).get('provider'),
            'model': token(raw.get('model'), secrets) or (error or {}).get('model'),
            'attempts': attempts if type(attempts) is int and 0 <= attempts <= 5 else None,
            'mayConsumeUsage': True,
            'failure': failure({'status':'failed','backend':{'providerError':error}}) if not verified else None}
