"""Read provider/model names across Git refs without exposing configuration secrets."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import re
import subprocess


SUPPORTED = {'codex', 'gemini', 'google', 'openai', 'anthropic', 'groq', 'mistral',
             'deepseek', 'xai', 'together', 'perplexity', 'cohere', 'openrouter'}
EFFORTS = ('none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')


def configured(raw):
    try:
        data = json.loads(raw).get('llm_providers', {})
        if not isinstance(data, dict):
            return []
        result = []
        for provider, config in data.items():
            if not isinstance(config, dict) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_.-]{0,63}', provider):
                continue
            model = config.get('model', '')
            if isinstance(model, str) and len(model) <= 160 and (not model or re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_./:@+-]*', model)):
                result.append((provider.lower(), model))
        return result
    except (ValueError, AttributeError, TypeError):
        return []


def codex_efforts():
    """Use the installed client's model catalog; do not guess model capabilities."""
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    try:
        models = json.loads((home / 'models_cache.json').read_text(encoding='utf-8')).get('models', [])
        return {m['slug']: [r['effort'] for r in m.get('supported_reasoning_levels', [])
                            if isinstance(r, dict) and r.get('effort') in EFFORTS]
                for m in models if isinstance(m, dict) and isinstance(m.get('slug'), str)}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {}


def discover(workspace, branch):
    from .server import run_git
    refs = [ref for ref in run_git(workspace.repository, 'for-each-ref', '--format=%(refname)',
                                   'refs/heads', 'refs/remotes').splitlines() if not ref.endswith('/HEAD')]
    # A single cat-file process reads every branch. Duplicate blobs are parsed once.
    requests = ''.join(ref + ':.vita/extensions.json\n' for ref in refs).encode()
    process = subprocess.run(['git', '-C', str(workspace.repository), 'cat-file', '--batch'],
                             input=requests, capture_output=True, check=True, timeout=30)
    stream = io.BytesIO(process.stdout)
    blobs, found = {}, {}

    def add(pairs, source):
        for pair in pairs:
            found.setdefault(pair, set()).add(source)

    for ref in refs:
        header = stream.readline().rstrip(b'\n').split()
        if not header or header[-1] == b'missing':
            continue
        size = int(header[-1]); raw = stream.read(size); stream.read(1)
        blob = header[0]
        if blob not in blobs:
            blobs[blob] = configured(raw) if header[1] == b'blob' and size < 2_000_000 else []
        add(blobs[blob], ref)
    # Include ignored/uncommitted settings in every linked checkout as well.
    records = run_git(workspace.repository, 'worktree', 'list', '--porcelain', '-z', strip=False)
    for record in records.split('\0\0'):
        fields = dict(part.split(' ', 1) for part in record.split('\0') if ' ' in part)
        if 'worktree' in fields:
            path = Path(fields['worktree']) / '.vita/extensions.json'
            try:
                add(configured(path.read_text(encoding='utf-8-sig')), fields.get('branch', 'detached') + ' (working tree)')
            except OSError:
                pass
    current = configured(workspace.read(branch, '.vita/extensions.json'))
    if not current:
        try:
            current = configured((workspace.repository / '.vita/extensions.json').read_text(encoding='utf-8-sig'))
        except OSError:
            pass
    current = current or [('openai', '')]  # VITA's own fallback when no providers are configured.
    add(current, 'Selected branch configuration')
    efforts = codex_efforts() if workspace.ai_bridge() else {}
    options = []
    for (provider, model), sources in sorted(found.items()):
        options.append({'provider': provider, 'model': model, 'sources': sorted(sources),
                        'supported': provider in SUPPORTED,
                        'reasoning': efforts.get(model, []) if provider == 'codex' else []})
    return {'options': options, 'default': {'provider': current[0][0], 'model': current[0][1]},
            'refCount': len(refs), 'reasoningBridge': workspace.ai_bridge()}


def resolve(workspace, branch, provider, model, reasoning):
    if (model is not None and not isinstance(model, str)) or not isinstance(reasoning, str):
        raise ValueError('Choose a supported AI model and thinking level.')
    catalog = discover(workspace, branch)
    provider = provider or catalog['default']['provider']
    if model is None:
        model = next((o['model'] for o in catalog['options'] if o['provider'] == provider), '')
        if provider == catalog['default']['provider']:
            model = catalog['default']['model']
    option = next((o for o in catalog['options'] if o['provider'] == provider and o['model'] == model), None)
    if not option or not option['supported']:
        raise ValueError('Choose an available AI service and model from the list.')
    if reasoning and reasoning not in option['reasoning']:
        raise ValueError('This thinking level is not available for the selected AI model.')
    return provider, model, reasoning
