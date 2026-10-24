"""Recoverable multi-file publication, with rollback that preserves external edits."""
from contextlib import contextmanager
import json
import re

from .fileio import atomic_write_bytes
from .checkpoints import artifact_name


def targets(workspace, branch, entries):
    location = workspace.location(branch)
    if location is None or any(name != '@metadata' and not artifact_name(name) for name in entries):
        raise ValueError('Publication targets are no longer available')
    from .workspace import safe_path
    for values in entries.values():
        if not isinstance(values, dict) or set(values) != {'old','new'} or any(value is not None and not isinstance(value,str) for value in values.values()):
            raise ValueError('Invalid publication journal')
    return {name: safe_path(workspace.root, workspace.metadata_path(branch).relative_to(workspace.root).as_posix()) if name == '@metadata' else safe_path(location, name)
            for name in entries}


def content(path):
    return path.read_text(encoding='utf-8') if path.is_file() else None


def put(path, value):
    if value is None:
        path.unlink(missing_ok=True)
    else:
        atomic_write_bytes(path, value.encode('utf-8'))


def rollback(workspace, record):
    paths = targets(workspace, record['branch'], record['entries'])
    for name, values in record['entries'].items():
        current = content(paths[name])
        if current == values['new'] and current != values['old']:
            put(paths[name], values['old'])
        # A third-party edit is neither the old nor new value: keep it untouched.


@contextmanager
def publish(workspace, ident, branch, updates):
    paths = targets(workspace, branch, {name: {'old': None, 'new': value} for name,value in updates.items()})
    record = {'schemaVersion': 1, 'branch': branch,
              'entries': {name: {'old': content(paths[name]), 'new': value} for name, value in updates.items()}}
    journal = workspace.root / 'publications' / (ident + '.json')
    atomic_write_bytes(journal, json.dumps(record).encode())
    try:
        for name, values in record['entries'].items():
            if content(paths[name]) != values['old']:
                raise ValueError('Application changed during publication')
            put(paths[name], values['new'])
        yield
    except BaseException:
        try:
            rollback(workspace, record)
            journal.unlink(missing_ok=True)
        except OSError:
            workspace._pending_publications.add(branch)
            workspace._publishing.add(branch)
            raise
        raise
    else:
        try:
            journal.unlink(missing_ok=True)
        except OSError as error:
            # The succeeded history record is the durable commit marker. A later
            # startup can remove this journal without reverting published files.
            workspace.diagnostics.error('publication_cleanup_failed', error, operation='publication')


def recover(workspace):
    if (workspace.root/'publications').is_symlink():
        return
    for journal in (workspace.root / 'publications').glob('*.json'):
        record = {}
        try:
            if journal.is_symlink() or not re.fullmatch(r'[a-f0-9]{32}', journal.stem) or journal.stat().st_size > 64_000_000:
                continue
            record = json.loads(journal.read_text(encoding='utf-8'))
            if not isinstance(record,dict):
                raise ValueError('Invalid publication journal')
            history = workspace.root / 'job-history' / journal.name
            status = json.loads(history.read_text(encoding='utf-8')).get('status') if history.is_file() else None
            if record.get('schemaVersion') != 1:
                continue
            if status != 'succeeded':
                rollback(workspace, record)
            journal.unlink()
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            if isinstance(record,dict) and isinstance(record.get('branch'),str):
                workspace._pending_publications.add(record['branch'])
                workspace._publishing.add(record['branch'])
            workspace.diagnostics.error('publication_recovery_failed', error, operation='publication')
