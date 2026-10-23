"""Private, immutable step checkpoints. No provider stdout is trusted or saved here."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import time
import threading

from .fileio import atomic_write_bytes
from .workflow import REPORTS, STEPS

ARTIFACTS = ('main.tex', 'cover-letter.tex', *dict.fromkeys(
    '.vita/results/' + name for names in REPORTS.values() for name in names))
MAX_CHECKPOINT_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_RUNS = 20
RETENTION_SECONDS = 7 * 86400
STORE_LOCK = threading.RLock()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def artifacts(folder):
    result = {}
    for name in ARTIFACTS:
        path = folder / name
        for parent in (path, *path.parents):
            if parent.is_symlink():
                raise ValueError('Linked checkpoint artifacts are not supported')
            if parent == folder:
                break
        if path.exists() and path.stat().st_size > 2_000_000:
            raise ValueError('Checkpoint artifact exceeds the file limit')
        result[name] = path.read_text(encoding='utf-8-sig') if path.is_file() else None
    return result


def signature(context, step, before):
    # The route is per step. Changing Cover's model preserves an Extract checkpoint,
    # but invalidates Cover and any later selected work. Session connection IDs
    # are handles, not configuration: the actual credentials are HMACed by
    # the workspace and never enter this record or the public API.
    route = context['stepConfig'].get(step, {})
    return fingerprint({'version': 1, 'inputs': context['checkpointInputs'], 'step': step,
                        'route': {k: v for k, v in route.items() if k not in {'connectionName', 'connection'}},
                        'language': context['language'] if step in ('adapt', 'cover') else None,
                        'credentials': context['credentialHashes'].get(step),
                        'skills': context['stepSkills'].get(step),
                        'dependencies': before})


def write_checkpoint(root, ident, step, key, files, outcome, pdf=None):
    with STORE_LOCK:
        return _write_checkpoint(root, ident, step, key, files, outcome, pdf)


def _write_checkpoint(root, ident, step, key, files, outcome, pdf=None):
    data = {'schemaVersion': 1, 'step': step, 'signature': key,
            'hashes': {name: fingerprint(content) for name, content in files.items()},
            'outcome': outcome, 'createdAt': time.time()}
    pdf_bytes = pdf['path'].read_bytes() if pdf else b''
    if step == 'cover' and not pdf_bytes.startswith(b'%PDF-'):
        return False
    size = sum(len((content or '').encode()) for content in files.values()) + len(pdf_bytes)
    if size > MAX_CHECKPOINT_BYTES:
        return False
    used = sum(path.stat().st_size for path in root.rglob('*') if path.is_file() and not path.is_symlink())
    if used + size + 100_000 > MAX_TOTAL_BYTES:
        return False
    folder = root / ident / step
    if any(path.is_symlink() for path in (root, root/ident, folder, folder/'files')):
        raise ValueError('Linked checkpoint folders are not supported')
    if pdf:
        data['pdf'] = {'sha256': hashlib.sha256(pdf_bytes).hexdigest(), 'engine': pdf['engine'], 'warnings': [str(warning)[:300] for warning in pdf['warnings'][:100]]}
        atomic_write_bytes(folder/'cover-letter.pdf', pdf_bytes)
    # Publish the manifest last; a crash before it cannot create a usable checkpoint.
    for name, content in files.items():
        if content is not None:
            atomic_write_bytes(folder / 'files' / name, content.encode('utf-8'))
    atomic_write_bytes(folder / 'manifest.json', json.dumps(data).encode())
    return True


def load_checkpoint(root, ident, step):
    if not re.fullmatch(r'[a-f0-9]{32}', ident) or step not in REPORTS:
        return None
    folder = root / ident / step
    if any(path.is_symlink() for path in (root, root/ident, folder, folder/'files')):
        return None
    try:
        manifest = folder / 'manifest.json'
        if manifest.is_symlink() or manifest.stat().st_size > 100_000:
            return None
        data = json.loads(manifest.read_text(encoding='utf-8'))
        if (data.get('schemaVersion') != 1 or data.get('step') != step or set(data['hashes']) != set(ARTIFACTS)
                or not isinstance(data.get('signature'), str) or not re.fullmatch(r'[a-f0-9]{64}',data['signature'])):
            return None
        files = artifacts(folder / 'files')
        if data['hashes'] != {name: fingerprint(content) for name, content in files.items()}:
            return None
        if data['outcome'].get('status') != 'success' or data['outcome'].get('verified') is not True:
            return None
        if step in {'extract','analyze','review'}:
            native = data['outcome'].get('backend')
            if not isinstance(native,dict) or native.get('status') != 'success' or not native.get('attempts') or native['attempts'][-1].get('category') != 'valid':
                return None
        if step == 'cover':
            pdf_path = folder/'cover-letter.pdf'
            if pdf_path.is_symlink() or pdf_path.stat().st_size > MAX_CHECKPOINT_BYTES:
                return None
            content = pdf_path.read_bytes()
            if not content.startswith(b'%PDF-') or hashlib.sha256(content).hexdigest() != data['pdf']['sha256']:
                return None
            if data['pdf']['engine'] not in {'pdflatex','xelatex','lualatex'} or not isinstance(data['pdf']['warnings'],list):
                return None
        return data, files
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def restore(folder, files):
    for name, content in files.items():
        path = folder / name
        if path.is_symlink():
            raise ValueError('Linked checkpoint artifacts are not supported')
        if content is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write_bytes(path, content.encode('utf-8'))


def resume_plan(root, parent, context):
    before = dict(context['initialArtifacts'])
    reuse, rerun, checkpoints = [], [], {}
    invalid = False
    for step in STEPS:
        if step not in context['selected'] or step == 'validating':
            continue
        saved = load_checkpoint(root, parent, step)
        if not invalid and saved and saved[0]['signature'] == signature(context, step, before):
            reuse.append(step)
            checkpoints[step] = saved
            before = saved[1]
        else:
            invalid = True
            rerun.append(step)
    return {'reuse': reuse, 'rerun': rerun, 'checkpoints': checkpoints}


def cleanup(root, jobs, now=None):
    """Only checkpoints expire. History, review results, and application drafts remain."""
    with STORE_LOCK:
        return _cleanup(root, jobs, now)


def _cleanup(root, jobs, now=None):
    now = time.time() if now is None else now
    protected = {j['id'] for j in jobs.values() if j.get('status') in {'running', 'queued'}}
    protected.update(j.get('parentRunId') for j in jobs.values() if j.get('status') in {'running', 'queued'})
    candidates = []
    for folder in root.glob('*'):
        if not re.fullmatch(r'[a-f0-9]{32}', folder.name) or folder.is_symlink() or not folder.is_dir():
            continue
        # Never follow directory links during cleanup or account for external files.
        if any(p.is_symlink() for p in folder.rglob('*')):
            continue
        size = sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
        stamp = jobs.get(folder.name, {}).get('finishedAt') or folder.stat().st_mtime
        candidates.append((stamp, folder, size))
    count, total, removed = len(candidates), sum(item[2] for item in candidates), []
    for stamp, folder, size in sorted(candidates):
        if folder.name in protected:
            continue
        if now - stamp > RETENTION_SECONDS or count > MAX_RUNS or total > MAX_TOTAL_BYTES:
            # Resolved path is checked before recursive deletion, on every platform.
            if folder.resolve().parent != root.resolve():
                continue
            shutil.rmtree(folder)
            removed.append(folder.name)
            total -= size
            count -= 1
    return {'removed': removed, 'retainedRuns': count, 'bytes': total,
            'maxRuns': MAX_RUNS, 'maxBytes': MAX_TOTAL_BYTES, 'retentionDays': 7}
