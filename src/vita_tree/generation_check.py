"""Explicit synthetic generation in a disposable, document-free workspace."""
import json
from pathlib import Path
import subprocess
import tempfile

from .ai_config import STEPS, clean_settings, effective_settings, stage_environment
from .provider_status import generation_result
from .diagnostics_contract import token
from .processes import run_owned


def invoke(args, **kwargs):
    return run_owned(args, **kwargs)


def run(workspace, name, step, raw, confirmed=False):
    # Validation and capture happen under the workspace lock. The paid operation
    # never holds it, blocks navigation, or changes saved settings/application data.
    if confirmed is not True:
        raise ValueError('Confirm that this synthetic generation may consume provider usage before checking.')
    if not isinstance(step, str) or step not in STEPS:
        raise ValueError('Select an AI step to check.')
    with workspace.lock:
        if workspace._closed:
            raise ValueError('Restart Vita Tree before checking generation.')
        workspace.branch(name)
        settings = clean_settings(workspace, name, raw)
        route = effective_settings(settings, {step})[step]
        key = workspace.connections.get(route['connection'], route['provider']) if route['connection'] else None
        command = workspace.vita_command()
        if not command:
            raise ValueError('Install or connect Vita CV before checking generation.')
        pending = getattr(workspace, '_generation_checks', set())
        workspace._generation_checks = pending
        identity = (name, step)
        if identity in pending:
            raise ValueError('A generation check is already running for this step.')
        # Existing worktree when present; no new checkout or captured CV/JD.
        location = workspace.location(name, create=False) or workspace.repository
        context = workspace._ai_context(location, '', '', command, route['provider'], route['model'], route['reasoning'])
        env = stage_environment(context['env'], route, key)
        secrets = [v for k, v in env.items() if any(part in k.upper() for part in ('KEY','TOKEN','SECRET','PASSWORD')) and v]
        pending.add(identity)
    try:
        with tempfile.TemporaryDirectory(prefix='vita-tree-generation-check-') as folder:
            stage = Path(folder)
            # Codex discovers instructions from its Git root. Keep checks in
            # an empty repository outside the CV checkout, even for older CLIs
            # that require a trusted Git directory before executing.
            for name in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE',
                         'GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES'):
                env.pop(name, None)
            if route['provider'] == 'codex':
                git = subprocess.run(['git','-c','init.defaultBranch=main','init','--quiet','--template=',str(stage)],
                                     cwd=stage,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL,timeout=15)
                if git.returncode:
                    raise ValueError('Could not prepare the isolated generation check. Check Git and temporary-folder access.')
            (stage/'.vita').mkdir()
            # Only the selected route crosses the boundary, never a CV, JD,
            # project instructions, provider output, or credentials on disk.
            config = {'llm_providers': {route['provider']: {'model':route['model'],
                      **({'reasoning_effort':route['reasoning']} if route['reasoning'] else {})}}}
            (stage/'.vita/extensions.json').write_text(json.dumps(config), encoding='utf-8')
            env.update(VITA_PROJECT_ROOT=str(stage), VITA_DIAGNOSTICS_DIR=str(stage/'.vita/logs/traces'),
                       VITA_DIAGNOSTIC_CONTENT='off')
            for name in ('VITA_TREE_EXECUTION_ID','VITA_TRACEPARENT','VITA_REQUIREMENTS_DIR'):
                env.pop(name, None)
            args = command + ['providers', 'check', '--provider', route['provider'], '--generate', '--json']
            if route['model']:
                args += ['--model', route['model']]
            try:
                with workspace.processes.scope():
                    process = invoke(args, cwd=stage, env=env, stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            except subprocess.TimeoutExpired:
                return {'status':'failed','generationVerified':False,'mayConsumeUsage':True,
                        'provider':None,'model':None,'attempts':None,
                        'failure':{'category':'timeout','title':'Generation check timed out',
                        'action':'Check connectivity before trying again. Provider usage may already have occurred.',
                        'retryable':None,'attempts':None}, 'requested':{k:token(route[k], secrets) for k in ('provider','model','reasoning')},
                        'origin':'step_override' if step in settings['steps'] else 'shared'}
            path = stage/'.vita/results/provider-check.json'
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 100_000:
                raise ValueError('Generation check evidence is unavailable. Update Vita CV to a version supporting provider-check v1.')
            raw = json.loads(path.read_text(encoding='utf-8'))
            result = generation_result(raw, secrets)
            if process.returncode and result['generationVerified']:
                raise ValueError('Generation check returned inconsistent evidence. Inspect the Vita CV installation.')
            # Verify identity before display redaction. A legitimate model ID
            # such as model@revision may be withheld from diagnostic views.
            if result['generationVerified'] and (raw.get('provider') != route['provider'] or (route['model'] and raw.get('model') != route['model'])):
                raise ValueError('Generation succeeded, but the selected route could not be verified. Check the Vita CV installation before relying on this result.')
            if result['provider'] and result['provider'] != route['provider'] or (
                    route['model'] and result['model'] and result['model'] != route['model']):
                raise ValueError('Generation check reported a different route. No successful check can be confirmed for the selected setup.')
            result.update(requested={k:token(route[k], secrets) for k in ('provider','model','reasoning')},
                          origin='step_override' if step in settings['steps'] else 'shared')
            return result
    except (json.JSONDecodeError, UnicodeError):
        raise ValueError('Generation check evidence could not be read. Update Vita CV and try again.') from None
    finally:
        key = None
        env.clear()
        secrets.clear()
        with workspace.lock:
            pending.discard(identity)
