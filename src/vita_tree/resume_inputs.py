"""Capture non-secret provenance and isolate canonical criteria for a preparation."""
from datetime import date
from pathlib import Path
import hashlib
import hmac
import json
import os
import re

from .ai_config import stage_environment
from .checkpoints import ARTIFACTS, fingerprint
from .fileio import atomic_write_bytes
from .security import snapshot_excluded


def capture(workspace, context, record):
    from .workspace import safe_path, read_text, digest
    from .server import run_git
    location = context['location']
    names = run_git(location, 'ls-files', '-z', '--cached', '--others', '--exclude-standard', strip=False)
    assets = {}
    total = 0
    for name in sorted(set(names.split('\0')) - {''}):
        if snapshot_excluded(name) or name in {'main.tex', 'job.md', 'cover-letter.tex'}:
            continue
        path = safe_path(location, name)
        if path.is_file():
            total += path.stat().st_size
            if total > 200_000_000:
                raise ValueError('Application inputs exceed the snapshot limit')
            assets[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    criteria = {}
    from . import requirements_review
    store, _, marker = requirements_review.paths(workspace, context)
    if context.get('requirementsBackend'):
        review = requirements_review.state(workspace, context)
        context['requirementsToken'] = review['token']
        criteria['tree-review-token.json'] = json.dumps({'token':review['token']})
        if marker.is_file():
            criteria['tree-review.json'] = read_text(marker)
    approval = store / 'approved' / (digest(context['job']) + '.json')
    if approval.is_file():
        if approval.is_symlink():
            raise ValueError('Linked criteria are not supported')
        text = read_text(approval)
        criteria['approved/' + approval.name] = text
        revision = json.loads(text).get('revision', '')
        if not isinstance(revision, str) or not re.fullmatch(r'[a-f0-9]{64}', revision):
            raise ValueError('The approved requirements revision is invalid')
        path = store / 'revisions' / (revision + '.json')
        if path.is_symlink():
            raise ValueError('Linked criteria are not supported')
        criteria['revisions/' + path.name] = read_text(path)
        if not criteria['revisions/' + path.name]:
            raise ValueError('The approved requirements revision is missing')
    backend = {}
    if workspace.vita_source:
        root = workspace.vita_source / 'vita'
        for path in root.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in {'.py', '.md', '.json', '.yaml'}:
                backend[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('ai_runner.py', 'outcomes.py', 'checkpoints.py', 'resume_inputs.py', 'workspace.py', 'execution.py', 'diagnostics_contract.py', 'provider_status.py', 'factual_contract.py', 'factual_backend.py', 'factual_review.py', 'requirements_backend.py', 'requirements_review.py','security.py','pdf.py','preflight.py'):
        backend['tree-adapter/' + name] = hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    configs = dict(context['config'])
    extensions = json.loads(configs.get('extensions.json', '{}'))
    # Models are supplied explicitly per step; do not invalidate Extract merely
    # because the shared default or Cover-only model changed.
    extensions.pop('llm_providers', None)
    configs['extensions.json'] = json.dumps(extensions, sort_keys=True)
    context['checkpointInputs'] = {'source': digest(context['source']), 'job': digest(context['job']),
                                   'assets': assets, 'config': fingerprint(configs),
                                   'criteria': fingerprint(criteria),
                                   'backend': fingerprint(backend), 'command': context['command'], 'date': date.today().isoformat(),
                                   'compiler': record.get('compileEngine') or 'auto'}
    salt = workspace.root / 'checkpoint-key'
    if not salt.exists():
        atomic_write_bytes(salt, os.urandom(32))
    context['stepSkills'] = {step: fingerprint({name: content for name, content in context['skills'].items() if name.startswith('.vita/skills/' + step + '/')}) for step in context['stepConfig']}
    context['credentialHashes'] = {}
    for step, route in context['stepConfig'].items():
        env = stage_environment(context['env'], route, context['keys'].get(step))
        relevant = {key: value for key, value in env.items() if
                    re.search(r'(?:KEY|TOKEN|BASE_URL|ENDPOINT)$', key) or
                    key.startswith(('OPENAI_', 'ANTHROPIC_', 'GEMINI_', 'CODEX_', 'GOOGLE_')) or
                    key in {'VITA_CODEX','HTTP_PROXY','HTTPS_PROXY','NO_PROXY'} or (route['provider']=='codex' and key=='PATH')}
        # Only a keyed digest is retained, never keys, endpoints, or raw env.
        context['credentialHashes'][step] = hmac.new(salt.read_bytes(), json.dumps(relevant, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    context['criteria'] = criteria
    context['language'] = record['language']
    initial = {name: None for name in ARTIFACTS}
    initial = {name: (context['dependencies'].get(name) if name.startswith('.vita/results/') else
                     context['source'] if name == 'main.tex' else context.get('coverBefore') if name == 'cover-letter.tex' else None) for name in initial}
    context['initialArtifacts'] = initial
