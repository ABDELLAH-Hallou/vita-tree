"""Shared immutable job definitions, explicit approval, and run provenance."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

from .checkpoints import fingerprint
from .fileio import atomic_write_bytes


def read(path):
    if path.is_symlink() or path.stat().st_size > 4_000_000:
        raise ValueError('Invalid requirements record')
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    atomic_write_bytes(path, json.dumps(value, ensure_ascii=False).encode('utf-8'))


def supported(workspace):
    return bool(workspace.vita_source and (workspace.vita_source/'vita/helpers/requirements.py').is_file())


def paths(workspace, context):
    from .workspace import digest
    configured = context['env'].get('VITA_REQUIREMENTS_DIR')
    store = Path(configured).expanduser() if configured else workspace.root.parent/'vita/requirements'
    if not store.is_absolute():
        store = context['location']/store
    key = digest(context['job'])
    marker = workspace.root/'requirements-reviews'/(fingerprint(os.path.normcase(str(store.resolve()))) + '-' + key + '.json')
    return store, store/'approved'/(key+'.json'), marker


def state(workspace, context):
    from .workspace import digest
    store, approval, marker = paths(workspace, context)
    pointer = read(approval) if approval.is_file() else None
    if pointer is not None and (not isinstance(pointer, dict) or set(pointer) != {'schema_version','source_sha256','revision'}
            or type(pointer['schema_version']) is not int or pointer['schema_version'] != 1 or pointer['source_sha256'] != digest(context['job'])):
        raise ValueError('Invalid requirements approval record')
    approved = pointer['revision'] if pointer else None
    review = read(marker) if marker.is_file() else {}
    if not isinstance(review, dict) or (marker.is_file() and (review.get('state') not in {'pending','approved'} or not re.fullmatch('[a-f0-9]{64}',str(review.get('revision',''))))):
        raise ValueError('Invalid requirements review record')
    # A CLI-created draft already lives in the canonical shared store. Display
    # it directly instead of making an extra AI call to rediscover the same job.
    native = None
    if not review and not approved and context['config'].get('requirements-state.json'):
        native = json.loads(context['config']['requirements-state.json'])
        if not isinstance(native,dict):
            raise ValueError('Invalid Vita CV requirements state')
        if native.get('source_sha256') == digest(context['job']):
            review = {'state':'pending','revision':native.get('revision')}
    revision = review.get('revision') if review.get('state') == 'pending' else approved
    for value in (revision, approved):
        if value is not None and not re.fullmatch('[a-f0-9]{64}', str(value)):
            raise ValueError('Invalid requirements revision')
    return {'revision': revision, 'approvedRevision': approved,
            'state': 'pending' if review.get('state') == 'pending' else 'approved' if approved else 'missing',
            'originBranch': review.get('originBranch'), 'parentRevision': review.get('parentRevision'),
            'token': fingerprint({'approval': pointer, 'review': review, 'nativeState':native})}


def backend(workspace, request):
    parent = workspace.root/'requirements-work'; parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as folder:
        stage = Path(folder)
        write(stage/'request.json', request)
        env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ('KEY','TOKEN','SECRET','PASSWORD')) and not k.startswith('VITA_')}
        env.update(PYTHONUTF8='1', VITA_REQUIREMENTS_DIR=str(stage/'store'))
        if workspace.vita_source:
            env['PYTHONPATH'] = str(workspace.vita_source) + os.pathsep + env.get('PYTHONPATH','')
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('requirements_backend.py')), str(stage/'request.json'), str(stage/'response.json')],
                                cwd=stage, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        if result.returncode or not (stage/'response.json').is_file():
            raise ValueError('Vita CV canonical requirements are unavailable. Update the connected Vita CV installation.')
        response = read(stage/'response.json')
        if response.get('error'):
            raise ValueError(response['error'])
        return response['definition']


def definition(workspace, context, revision):
    if not re.fullmatch('[a-f0-9]{64}', str(revision)):
        raise ValueError('No canonical definition is available. Run Extract first.')
    store, pointer, _ = paths(workspace, context)
    data = read(store/'revisions'/(revision+'.json'))
    if data['revision'] != revision:
        raise ValueError('The requirements revision changed.')
    approval = read(pointer) if pointer.is_file() else None
    return backend(workspace, {'action':'validate', 'source':context['job'], 'definition':data,
                              'approval': approval if approval and approval.get('revision') == revision else None})


def context_for(workspace, branch):
    return workspace._ai_context(workspace.location(branch), workspace.read(branch, 'main.tex'), workspace.read(branch, 'job.md'), [], '', None, '')


def view(workspace, branch, run_id=None):
    with workspace.lock:
        context = context_for(workspace, branch)
        current = state(workspace, context)
        if run_id:
            record = workspace.jobs.get(run_id)
            if not record or record['branch'] != branch:
                raise ValueError('Select a run belonging to this application.')
            data = read(workspace.root/'run-requirements'/(run_id+'.json'))
            if data['revision'] != (record.get('requirementsRevision') or record.get('requirementsDraft')):
                raise ValueError('The captured requirements evidence changed.')
            backend(workspace, {'action':'validate','source':data['source_text'],'definition':data})
            return {**current,'definition':data,'readOnly':True,'runId':run_id}
        data = definition(workspace, context, current['revision']) if current['revision'] else None
        return {**current, 'definition':data, 'readOnly':False, 'source':context['job'], 'available':supported(workspace)}


def retain(store, data):
    path = store/'revisions'/(data['revision']+'.json')
    if path.exists() and read(path) != data:
        raise ValueError('An immutable requirement revision was modified.')
    write(path, data)


def retain_run(workspace, record, context, data):
    _, approval, marker = paths(workspace, context)
    write(workspace.root/'run-requirements'/(record['id']+'.json'), data)
    # Paths are private. Polling history needs no Git checkout or provider call.
    write(workspace.root/'run-requirements'/(record['id']+'.binding.json'),
          {'revision':data['revision'],'sourceHash':data['source_sha256'],
           'approval':str(approval.resolve()),'review':str(marker.resolve())})


def run_status(workspace, record):
    """Public status contains no source text or private store paths."""
    try:
        binding = read(workspace.root/'run-requirements'/(record['id']+'.binding.json'))
        if binding['revision'] != record['requirementsRevision']:
            return 'unavailable'
        approval, marker = Path(binding['approval']), Path(binding['review'])
        review = read(marker) if marker.is_file() else {}
        if review.get('state') == 'pending':
            return 'pending'
        pointer = read(approval)
        if (type(pointer['schema_version']) is not int or pointer['schema_version'] != 1 or
                pointer['source_sha256'] != binding['sourceHash'] or not re.fullmatch('[a-f0-9]{64}',str(pointer['revision']))):
            return 'unavailable'
        return 'current' if pointer['revision'] == binding['revision'] else 'superseded'
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return 'unavailable'


def change(workspace, branch, token, revision, items=None, approve=False, confirmed=False, *, automatic=False):
    from .workspace import ConflictError, digest
    with workspace.lock:
        workspace.busy(branch)
        context = context_for(workspace, branch)
        current = state(workspace, context)
        if current['token'] != token or revision != current['revision']:
            raise ConflictError('The job definition changed. Reload requirements before saving.')
        if approve and confirmed is not True:
            raise ValueError('Confirm that you reviewed this exact revision before approval.')
        if approve and current['state'] == 'approved':
            raise ConflictError('This revision is already approved. Save corrections as a new draft before approving again.')
        data = definition(workspace, context, revision)
        data = backend(workspace, {'action':'approve' if approve else 'edit', 'definition':data, 'source':context['job'], 'items':items})
        if (state(workspace, context_for(workspace, branch))['token'] != token or workspace.read(branch, 'job.md') != context['job']):
            raise ConflictError('The job definition changed while validating. Reload requirements before saving.')
        store, approval, marker = paths(workspace, context)
        retain(store, data)
        # Marker is published last. A partial approval stays blocked until retried.
        if approve:
            write(approval, {'schema_version':1,'source_sha256':digest(context['job']), 'revision':data['revision']})
        write(marker, {'state':'approved' if approve else 'pending', 'revision':data['revision'],
                       'parentRevision':revision if revision != data['revision'] else current['parentRevision'],
                       'originBranch':branch, 'decidedAt':time.time(), 'method':('automatic_run_policy' if automatic else 'explicit_ui_review') if approve else 'ui_correction'})
        # Immutable provenance survives future approvals for the same source.
        write(workspace.root/'requirements-history'/(data['revision']+'-'+str(time.time_ns())+'.json'),
              {'revision':data['revision'], 'parentRevision':revision, 'branch':branch,'approved':approve,'at':time.time(),'actor':'automatic_policy' if automatic else 'local_user'})
        return view(workspace, branch)


def capture(workspace, record, context, stage, execution_id):
    """Import only a backend-validated, execution-bound Extract definition."""
    from .workspace import AIRunError
    if not context.get('requirementsBackend'):
        return
    if context.get('requirementsRevision'):
        return
    envelope = read(stage/'.vita/results/tree-requirements.json')
    if envelope.get('executionId') != execution_id:
        raise ValueError('Unverified canonical requirements')
    data = backend(workspace, {'action':'validate','source':context['job'],'definition':envelope['definition']})
    with workspace.lock:
        if state(workspace, context)['token'] != context['requirementsToken'] or workspace.read(record['branch'],'job.md') != context['job']:
            raise AIRunError('The job definition changed during Extract. Review the current application before retrying.')
        store, _, marker = paths(workspace, context)
        retain(store, data)
        write(marker, {'state':'pending','revision':data['revision'],'originBranch':record['branch'],'parentRevision':None})
        retain_run(workspace, record, context, data)
        workspace._job_update(record, requirementsDraft=data['revision'])


def require_approval(workspace, record, context):
    from .workspace import AIRunError
    if context.get('requirementsBackend') and not context.get('requirementsRevision'):
        stages = [dict(item, status='succeeded', finishedAt=time.time()) if item['id']=='extract' and item['status']!='skipped' else item for item in record['stages']]
        workspace._job_update(record, stages=stages)
        raise AIRunError('Review and approve the job requirements from Extract, then retry to continue. Your application is unchanged.')
