"""Child-process adapter for the source VITA CLI; never changes its installation."""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys
import argparse
import inspect
import subprocess
import json
import tempfile
import shutil


def extract_requirements(invoke, provider, execution_id):
    """Canonical extraction sees only the job description, never the candidate CV."""
    if not invoke():
        return False
    try:
        from vita.helpers import requirements
    except ImportError:
        return True  # Legacy backends are never labelled as canonically approved.
    raw = Path('job.md').read_text(encoding='utf-8')
    if requirements.approved_revision(raw):
        return True
    from vita.commands.requirements import run
    origin = Path.cwd()
    trace = origin/'.vita/results/tree-requirements-native.json'
    trace.unlink(missing_ok=True)
    old_store = os.environ.get('VITA_REQUIREMENTS_DIR')
    with tempfile.TemporaryDirectory(prefix='vita-requirements-') as directory:
        scratch = Path(directory)
        (scratch/'job.md').write_text(raw, encoding='utf-8')
        (scratch/'.vita').mkdir()
        for name in ('extensions.json','config.json'):
            if (origin/'.vita'/name).is_file():
                shutil.copyfile(origin/'.vita'/name, scratch/'.vita'/name)
        # Codex requires a repository; no application files are copied into it.
        subprocess.run(['git','init','--quiet',str(scratch)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            os.chdir(scratch)
            os.environ['VITA_REQUIREMENTS_DIR'] = str(scratch/'store')
            success = run('draft', auto=True, provider=provider)
            native = scratch/'.vita/results/requirements.outcome.json'
            if native.is_file():
                shutil.copyfile(native, trace)
            if success:
                pointer = json.loads(requirements.STATE.read_text(encoding='utf-8'))
                data = requirements.read_revision(pointer['revision'])
                (origin/'.vita/results/tree-requirements.json').write_text(
                    json.dumps({'executionId':execution_id,'definition':data}, ensure_ascii=False), encoding='utf-8')
            return success
        finally:
            os.chdir(origin)
            if old_store is None:
                os.environ.pop('VITA_REQUIREMENTS_DIR', None)
            else:
                os.environ['VITA_REQUIREMENTS_DIR'] = old_store


def call_codex(llm, system_prompt, user_prompt, model='', reasoning=''):
    executable = llm._find_codex_cli()
    if not executable:
        raise RuntimeError('Codex CLI is unavailable. Install Codex and sign in first.')
    output = Path('.vita/tmp/codex-output.md')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    command = [executable, 'exec', '--sandbox', 'read-only', '--output-last-message', str(output)]
    if model:
        command += ['--model', model]
    if reasoning:
        command += ['-c', 'model_reasoning_effort="' + reasoning + '"']
    command += ['-']
    try:
        result = subprocess.run(command, input=system_prompt + '\n\n==== TASK ====\n' + user_prompt,
                                capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Codex execution failed. Check authentication and model access.')
        return output.read_text(encoding='utf-8').strip()
    finally:
        output.unlink(missing_ok=True)


AUTO_DOCUMENT_CONTEXT = """VITA TREE AUTONOMOUS GENERATION:
The host has captured the current factual sources before this request. Generate
the requested complete LaTeX response from the supplied inputs. Do not run
`vita facts capture`, `vita facts check`, or any other command; do not read or
write files. Instructions for generated-prompt/manual execution in skills are
host responsibilities in this mode. The host validates your response, stages
the proposal and requires factual approval; you must not approve or bypass it.
Use only analysis explicitly supplied for this job. Historical report files are
not evidence of the current job or candidate facts. If matching analysis is not
supplied, use the current job requirements and captured CV directly; do not search
for another job's report or stop solely because optional analysis is absent.
Preserve the output contract.
"""


def configure(llm, step=None):
    original_load = llm.load_env
    # VITA normally returns only .vita/.env entries. Keys supplied by the parent
    # process must also be visible, without writing a second credentials file.
    llm.load_env = lambda: {**original_load(), **os.environ}
    if step in {'adapt', 'cover'}:
        original_generate = llm.generate
        def generate_document(system_prompt, user_prompt, *args, **kwargs):
            return original_generate(AUTO_DOCUMENT_CONTEXT + '\n' + system_prompt,
                                     user_prompt, *args, **kwargs)
        llm.generate = generate_document
    reasoning = os.environ.get('VITA_TREE_REASONING', '')
    if reasoning:
        original_codex = llm._call_codex_cli
        if 'reasoning_effort' in inspect.signature(original_codex).parameters:
            def configured_codex(system, user, model='', **options):
                options['reasoning_effort'] = reasoning
                return original_codex(system, user, model, **options)
            llm._call_codex_cli = configured_codex
        else:
            def legacy_codex(system, user, model='', **options):
                if options.get('response_schema') is not None:
                    from vita.helpers.provider_errors import UnsupportedSchema
                    raise UnsupportedSchema()
                return call_codex(llm, system, user, model, reasoning)
            llm._call_codex_cli = legacy_codex


def main():
    from vita.helpers import env, llm
    original_load = env.load_env
    env.load_env = lambda: {**original_load(), **os.environ}
    configure(llm, sys.argv[1] if len(sys.argv)>1 else None)
    if os.environ.get('VITA_TREE_EXECUTION_ID') and len(sys.argv) > 1 and sys.argv[1] in {'extract','analyze','adapt','review','cover'}:
        from vita.commands.ai_step import run
        if __package__:
            from .outcomes import execute
        else:
            from outcomes import execute
        parser = argparse.ArgumentParser()
        parser.add_argument('step')
        parser.add_argument('--auto', action='store_true')
        parser.add_argument('--provider')
        parser.add_argument('--language')
        args = parser.parse_args()
        invoke = lambda: run(args.step, auto=args.auto, provider=args.provider, language=args.language)
        if args.step == 'extract':
            original_invoke = invoke
            invoke = lambda: extract_requirements(original_invoke, args.provider, os.environ['VITA_TREE_EXECUTION_ID'])
        success = execute(args.step, invoke,
                          os.environ['VITA_TREE_EXECUTION_ID'])
        if not success:
            raise SystemExit(1)
    else:
        runpy.run_module('vita', run_name='__main__')


if __name__ == '__main__':
    main()
