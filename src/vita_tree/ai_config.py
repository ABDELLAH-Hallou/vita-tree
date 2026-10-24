"""Workflow settings and session connections. Secrets never enter saved settings."""
from __future__ import annotations

import re
import uuid

from .providers import SUPPORTED, discover, resolve
from .security import credential_name

STEPS = ('extract', 'analyze', 'adapt', 'review', 'cover')
PREFIXES = dict(zip(STEPS, ('EXTRACTION', 'ANALYSIS', 'ADAPT', 'REVIEW', 'COVER')))
FIELDS = {'provider', 'model', 'reasoning', 'connection'}


class Connections:
    """Owned by one Workspace and protected by its lock; cleared on shutdown."""
    def __init__(self):
        self.items = {}

    def list(self):
        return [{'id': ident, 'name': item['name'], 'provider': item['provider']}
                for ident, item in self.items.items()]

    def add(self, name, provider, api_key):
        if not isinstance(provider, str) or provider not in SUPPORTED - {'codex'}:
            raise ValueError('Choose an API service. Codex uses your local CLI login.')
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80 or any(ord(c) < 32 for c in name):
            raise ValueError('Give this connection a name of up to 80 characters.')
        if not isinstance(api_key, str) or not api_key.strip() or len(api_key) > 4096 or any(ord(c) < 32 for c in api_key):
            raise ValueError('Enter a valid API key without line breaks.')
        if len(self.items) >= 100:
            raise ValueError('Remove an unused connection before adding another (maximum 100).')
        ident = uuid.uuid4().hex
        self.items[ident] = {'name': name.strip(), 'provider': provider, 'key': api_key.strip()}
        return next(item for item in self.list() if item['id'] == ident)

    def get(self, ident, provider):
        item = self.items.get(ident)
        if not item or item['provider'] != provider:
            raise ValueError('This connection is unavailable for this service. Add or select a connection again.')
        return item['key']

    def remove(self, ident):
        if not isinstance(ident, str) or ident not in self.items:
            raise ValueError('This connection is no longer available.')
        del self.items[ident]


def clean_settings(workspace, branch, raw, default=None):
    """Validate every draft field, retaining only an explicit, secret-free schema."""
    if not isinstance(raw, dict) or set(raw) - {'default', 'steps'}:
        raise ValueError('Choose a shared AI setup and optional step overrides.')
    shared = raw.get('default', default or {})
    steps = raw.get('steps', {})
    if not isinstance(steps, dict) or set(steps) - set(STEPS):
        raise ValueError('AI overrides must refer to a supported workflow step.')
    catalog = discover(workspace, branch)

    def route(value, base=None):
        if not isinstance(value, dict) or set(value) - FIELDS:
            raise ValueError('AI setup accepts service, model, reasoning, and connection only.')
        merged = {**(base or {}), **value}
        if base and value.get('provider', base['provider']) != base['provider']:
            merged = {**{'model': '', 'reasoning': '', 'connection': ''}, **value}
        provider, model, reasoning = resolve(workspace, branch, merged.get('provider', ''), merged.get('model'), merged.get('reasoning', ''), catalog)
        connection = merged.get('connection', '')
        if not isinstance(connection, str) or (connection and not re.fullmatch(r'[a-f0-9]{32}', connection)):
            raise ValueError('Choose a connection from the list.')
        if connection and provider == 'codex':
            raise ValueError('Codex uses your local CLI login. Choose the local connection.')
        return dict(provider=provider, model=model, reasoning=reasoning, connection=connection)

    shared = route(shared)
    return {'default': shared, 'steps': {step: route(value, shared) for step, value in steps.items()}}


def effective_settings(settings, selected):
    return {step: dict(settings['steps'].get(step, settings['default'])) for step in STEPS if step in selected}


def stage_environment(base, route, key=None):
    """A fresh environment per process prevents credentials leaking between steps."""
    provider = route['provider'].upper()
    aliases = {provider}
    if provider in {'GEMINI','GOOGLE'}:
        aliases.update({'GEMINI','GOOGLE'})
    if provider == 'CODEX':
        aliases.add('OPENAI')  # Explicit Codex API authentication remains supported.
    allowed_keys = {alias+'_API_KEY' for alias in aliases}
    env = {name:value for name,value in base.items()
           if (not credential_name(name) or name.upper() in allowed_keys)
           and not any(name.upper().startswith(other.upper()+'_') for other in SUPPORTED if other.upper() not in aliases)}
    env['ENABLE_JD_EXTRACTION'] = 'false'
    env['VITA_TREE_REASONING'] = route['reasoning']
    # Nested helper calls, if any, must use this step's explicit route too.
    for prefix in PREFIXES.values():
        env[prefix + '_PROVIDER'] = route['provider']
        env[prefix + '_MODEL'] = route['model']
    if key is not None:
        for alias in aliases:
            env.pop(alias+'_API_KEY', None)
        env[route['provider'].upper() + '_API_KEY'] = key
    return env
