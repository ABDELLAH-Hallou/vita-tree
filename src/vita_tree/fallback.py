"""Vita CV's opt-in provider-fallback/1 boundary; never choose routes here."""
import json
import os
import subprocess
import re
import tempfile

from .diagnostics_contract import CATEGORIES, PROVIDERS, token

VERSION = 'provider-fallback/1'


def history_backup(value):
    """Keep the saved route schema, excluding arbitrary private history fields."""
    if not isinstance(value, dict):
        return None
    route = {key: clean for key in ('provider', 'reasoning')
             if (clean := token(value.get(key)))}
    model = value.get('model')
    if isinstance(model, str) and token(model.replace('@', '-')):
        route['model'] = model
    if route.get('provider') not in PROVIDERS or not route.get('model'):
        return None
    connection = value.get('connection', '')
    route['connection'] = connection if isinstance(connection, str) and re.fullmatch('[a-f0-9]{32}', connection) else ''
    route.setdefault('reasoning', '')
    categories = value.get('categories')
    if not isinstance(categories, list) or any(not isinstance(c, str) for c in categories):
        return None
    return {**route, 'categories': [c for c in categories[:20] if c in CATEGORIES]}


def capabilities(workspace):
    if hasattr(workspace, '_fallback_capabilities'):
        return workspace._fallback_capabilities
    result = None
    if workspace.vita_source and not (workspace.vita_source / 'vita/helpers/fallback.py').is_file():
        workspace._fallback_capabilities = None
        return None
    command = workspace.vita_command()
    if command:
        env = dict(os.environ, PYTHONUTF8='1')
        if workspace.vita_source:
            env['PYTHONPATH'] = str(workspace.vita_source) + os.pathsep + env.get('PYTHONPATH', '')
        try:
            with tempfile.TemporaryFile() as output:
                process = workspace.processes.run([*command, 'fallback', 'capabilities', '--json'],
                    cwd=workspace.repository, env=env, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.DEVNULL, timeout=10)
                output.seek(0)
                data = json.loads(output.read(100_001)) if process.returncode == 0 else {}
            if (isinstance(data, dict) and data.get('schema_version') == 1 and data.get('version') == VERSION
                    and data.get('max_backups') == 1
                    and isinstance(data.get('allowed_categories'), list)
                    and isinstance(data.get('default_categories'), list)
                    and all(isinstance(c, str) and c in CATEGORIES for c in data['allowed_categories'])
                    and all(c in data['allowed_categories'] for c in data['default_categories'])):
                result = {key: data[key] for key in ('version', 'allowed_categories', 'default_categories')}
        except (ValueError, OSError, subprocess.SubprocessError):
            pass
    workspace._fallback_capabilities = result
    return result


def environment(env, backup, prefixes=('VITA', 'EXTRACTION', 'ANALYSIS', 'ADAPT', 'REVIEW', 'COVER')):
    """Override inherited policies explicitly; adapters own eligibility and retries."""
    for name in list(env):
        if any(name.startswith(prefix + '_FALLBACK_') for prefix in prefixes):
            del env[name]
    for prefix in prefixes:
        env[prefix + '_FALLBACK_ENABLED'] = 'true' if backup else 'false'
    if backup:
        for prefix in prefixes:
            for key, value in {'PROVIDER': backup['provider'], 'MODEL': backup['model'],
                               'REASONING_EFFORT': backup['reasoning'],
                               'CATEGORIES': ','.join(backup['categories'])}.items():
                env[prefix + '_FALLBACK_' + key] = value
