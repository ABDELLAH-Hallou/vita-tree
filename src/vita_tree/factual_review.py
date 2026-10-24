"""Revision-bound human review of private, retained preparation drafts."""
import json
import hashlib
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from . import checkpoints
from .factual_contract import validate, resolve_document, REASONS
from .fileio import atomic_write_bytes


def _folder(workspace, ident):
    from .workspace import safe_path
    return safe_path(workspace.root, 'factual-reviews/' + ident)


def _read(path):
    if path.is_symlink() or path.stat().st_size > 32_000_000:
        raise ValueError('Invalid factual-review record')
    return json.loads(path.read_text(encoding='utf-8'))


def _write(path, value):
    atomic_write_bytes(path, json.dumps(value, ensure_ascii=False).encode('utf-8'))


def summary(workspace, ident):
    folder = None
    try:
        folder = _folder(workspace, ident)
        value = _read(folder/'manifest.json')
        if (not isinstance(value, dict) or value.get('schemaVersion') != 1 or value.get('state') not in {'pending', 'resolved'}
                or value.get('step') not in {'adapt', 'cover'}
                or not re.fullmatch(r'fc-[a-f0-9]{64}', str(value.get('revision', '')))
                or type(value.get('count')) is not int or not 1 <= value['count'] <= 500):
            return {'state': 'unavailable'}
        if value['state'] == 'resolved' and (not re.fullmatch(r'fc-[a-f0-9]{64}', str(value.get('resolvedRevision', '')))
                or type(value.get('decidedAt')) not in (int, float) or not 0 <= value['decidedAt'] < 1e12):
            return {'state': 'unavailable'}
        return {k: value.get(k) for k in ('state', 'step', 'revision', 'resolvedRevision', 'count', 'decidedAt')}
    except FileNotFoundError:
        return {'state': 'unavailable'} if folder and (folder/'proposal.json').exists() else None
    except (OSError, ValueError, TypeError):
        return {'state': 'unavailable'}


def capture(workspace, record, context, stage, step, execution_id, before, key):
    """Only the backend's validated, execution-bound contract opens a review."""
    from .workspace import safe_path
    path = safe_path(stage, '.vita/results/' + step + '.facts.json')
    if not path.exists():
        return False  # Legacy backend: verification is not recorded.
    envelope = _read(safe_path(stage, '.vita/results/tree-' + step + '.facts.json'))
    if envelope.get('schemaVersion') != 1 or envelope.get('executionId') != execution_id:
        raise ValueError('Unverified factual-change evidence')
    report = validate(envelope['report'])
    if _read(path) != report or report['step'] != step:
        raise ValueError('Factual-change evidence changed')
    if report['status'] != 'confirmation_required':
        if report['status'] not in {'applied', 'approved'} or report['application_status'] != 'applied':
            raise ValueError('Factual changes were not applied by the backend')
        return False
    folder = _folder(workspace, record['id'])
    _write(folder/'proposal.json', report)
    input_names = (set(context['checkpointInputs']['assets']) | set(context['skills'])
                   | {'.vita/'+name for name in context['config']}
                   | {'.vita/criteria-snapshot/'+name for name in context['criteria']})
    input_hashes = {name: hashlib.sha256(safe_path(stage, name).read_bytes()).hexdigest() for name in input_names}
    manifest = {'schemaVersion': 1, 'state': 'pending', 'step': step, 'revision': report['revision'],
                'count': len(report['changes']), 'proposalHash': checkpoints.fingerprint(report),
                'stageHash': checkpoints.fingerprint(checkpoints.artifacts(stage)),
                'inputs': context['checkpointInputs'], 'head': context['baseCommit'],
                'reports': context['reports'], 'key': key, 'before': before, 'stageInputs': input_hashes}
    _write(folder/'manifest.json', manifest)
    return True


def _load(workspace, ident):
    from .workspace import ConflictError
    workspace.get_job(ident)
    folder = _folder(workspace, ident)
    try:
        manifest = _read(folder/'manifest.json')
        report = validate(_read(folder/'proposal.json'))
        if ((summary(workspace, ident) or {}).get('state') not in {'pending', 'resolved'} or manifest['proposalHash'] != checkpoints.fingerprint(report)
                or manifest['revision'] != report['revision']):
            raise ValueError('Changed review')
        return manifest, report
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ConflictError('This factual review is unavailable or changed. Regenerate the proposal; your application is unchanged.') from error


def view(workspace, ident):
    with workspace.lock:
        manifest, report = _load(workspace, ident)
        facts = {fact['id']: fact['source_ref'] for fact in report['source_facts']}
        sources = {source['id']: source['path'] for source in report['candidate_sources']['sources']}
        items = []
        for item in report['changes']:
            refs = [{**facts[key], 'path': sources[facts[key]['source_id']]} for key in item['source_fact_ids'] if key in facts]
            items.append({**item, 'sources': refs, 'unresolvedMeaning': REASONS[item['reason']]})
        result = {'runId': ident, 'step': report['step'], 'revision': report['revision'],
                  'state': manifest['state'], 'token': checkpoints.fingerprint(manifest), 'items': items,
                  'target': report['target'], 'original': report['target_before'], 'proposed': report['document']}
        if manifest['state'] == 'resolved':
            result['provenance'] = _read(_folder(workspace, ident)/'decisions.json')
        return result


def _matching(workspace, record, manifest):
    from .workspace import ConflictError, digest, read_text, safe_path
    from .resume_inputs import capture as capture_inputs
    branch = record['branch']
    workspace.busy(branch)
    location = workspace.location(branch, create=True)
    source, job = workspace.read(branch, workspace.document_path), workspace.read(branch, 'job.md')
    if (workspace.head(branch) != manifest['head'] or digest(source) != manifest['inputs']['source']
            or digest(job) != manifest['inputs']['job']
            or any(digest(read_text(safe_path(location, name))) != expected for name, expected in manifest['reports'].items())):
        raise ConflictError('The application changed after this proposal was captured. Your edits were preserved. Start a new preparation.')
    fresh = workspace._ai_context(location, source, job, workspace.vita_command(), record['provider'], record['model'], record['reasoning'])
    fresh.update(stepConfig=record.get('stepConfig') or {}, keys={}, dependencies={})
    capture_inputs(workspace, fresh, record)
    if any(fresh['checkpointInputs'][key] != manifest['inputs'][key] for key in ('assets', 'criteria', 'backend', 'config', 'command')):
        raise ConflictError('The application inputs or configuration changed. Regenerate this proposal before applying decisions.')


def backend(workspace, stage, request):
    """Use the connected backend's Python contract; never parse provider prose."""
    request_path, response_path = stage/'.vita/tree-review-request.json', stage/'.vita/tree-review-response.json'
    _write(request_path, request)
    env = os.environ.copy()
    for name in list(env):
        if any(part in name.upper() for part in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD')) or name.startswith('VITA_'):
            env.pop(name, None)
    if workspace.vita_source:
        env['PYTHONPATH'] = str(workspace.vita_source) + os.pathsep + env.get('PYTHONPATH', '')
    env.update(VITA_PROJECT_ROOT=str(stage), VITA_REQUIREMENTS_DIR=str(stage/'.vita/criteria-snapshot'), PYTHONUTF8='1')
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('factual_backend.py')), str(request_path), str(response_path)],
                            cwd=stage, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    if result.returncode or not response_path.is_file():
        raise ValueError('Vita CV could not validate these decisions. Check the proposal, source files, and factual-change contract support; your application is unchanged.')
    return _read(response_path)


def _stage_matches(stage, manifest):
    from .workspace import safe_path
    try:
        return (checkpoints.fingerprint(checkpoints.artifacts(stage)) == manifest['stageHash']
                and all(hashlib.sha256(safe_path(stage, name).read_bytes()).hexdigest() == expected
                        for name, expected in manifest['stageInputs'].items()))
    except (OSError, ValueError, KeyError):
        return False


def apply(workspace, ident, revision, token, decisions, confirmed=False):
    from .workspace import ConflictError, safe_path, read_text
    from .latex import parse_document
    from .pdf import compile_document
    if confirmed is not True:
        raise ValueError('Confirm that you reviewed the factual meaning of every decision.')
    with workspace.lock:
        manifest, report = _load(workspace, ident)
        if manifest['state'] != 'pending' or revision != manifest['revision'] or token != checkpoints.fingerprint(manifest):
            raise ConflictError('This factual review changed or was already applied. Reload the review.')
        expected, omitted = resolve_document(report, decisions)
        record = workspace.jobs[ident]
        _matching(workspace, record, manifest)
        stage = safe_path(workspace.root, 'runs/' + ident)
        if not _stage_matches(stage, manifest):
            raise ConflictError('The captured draft changed. Regenerate this proposal; your application is unchanged.')
        # Work only on a disposable copy. The immutable checkpoint and final
        # manifest are published last; cancellation/failure cannot alter the draft.
        parent = safe_path(workspace.root, 'review-work'); parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent, prefix='review-') as folder:
            scratch = Path(folder)
            if any(path.is_symlink() for path in stage.rglob('*')):
                raise ValueError('Linked review files are not supported')
            shutil.copytree(stage, scratch, dirs_exist_ok=True)
            result = backend(workspace, scratch, {'step': report['step'], 'revision': revision, 'decisions': decisions})
            resolved = validate(result['report'])
            actual = read_text(safe_path(scratch, report['target'])) if safe_path(scratch, report['target']).is_file() else None
            if (actual != expected or result.get('omitted') is not omitted or resolved['step'] != report['step']
                    or resolved['status'] not in {'approved', 'applied', 'rejected'}):
                raise ValueError('The backend did not apply the reviewed document. Your application is unchanged.')
            if expected is not None and (parse_document(expected)['error'] or r'\begin{document}' not in expected):
                raise ValueError('The reviewed text is not a valid LaTeX document. Adjust the edited wording before applying.')
            provenance = {'schemaVersion': 1, 'method': 'explicit_ui_review', 'actor': 'local_user',
                          'runId': ident, 'step': report['step'], 'revision': revision,
                          'resolvedRevision': resolved['revision'], 'decidedAt': time.time(),
                          'decisions': decisions, 'documentHash': checkpoints.fingerprint(expected)}
            _write(scratch/('.vita/results/' + report['step'] + '.decisions.json'), provenance)
            pdf = None
            if report['step'] == 'cover' and not omitted:
                built = compile_document(scratch, report['target'])
                pdf = {'path': built['pdf'], 'engine': built['engine'], 'warnings': built['warnings']}
            _matching(workspace, record, manifest)
            if not _stage_matches(stage, manifest):
                raise ConflictError('The captured draft changed while saving the review. Your edits were preserved.')
            files = checkpoints.artifacts(scratch)
            outcome = {'status': 'success', 'verified': True, 'backend': None,
                       'factualApproval': {'runId': ident, 'revision': revision}}
            if not checkpoints.write_checkpoint(workspace.root/'checkpoints', ident, report['step'], manifest['key'],
                                                files, outcome, pdf, omitted):
                raise ValueError('The reviewed draft exceeds the checkpoint limit. Your application is unchanged.')
            _write(_folder(workspace, ident)/'decisions.json', provenance)
            # A pending manifest always blocks Retry, even if checkpoint writing
            # succeeded before a crash. This one atomic write commits the review.
            _write(_folder(workspace, ident)/'manifest.json', {**manifest, 'state': 'resolved',
                   'resolvedRevision': resolved['revision'], 'decidedAt': provenance['decidedAt'],
                   'artifactHash': checkpoints.fingerprint(files)})
        return view(workspace, ident)
