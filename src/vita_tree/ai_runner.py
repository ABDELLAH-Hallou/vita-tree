"""Child-process adapter for the source VITA CLI; never changes its installation."""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys
import argparse
import inspect
import subprocess


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


def configure(llm):
    original_load = llm.load_env
    # VITA normally returns only .vita/.env entries. Keys supplied by the parent
    # process must also be visible, without writing a second credentials file.
    llm.load_env = lambda: {**original_load(), **os.environ}
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
    configure(llm)
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
        success = execute(args.step, lambda: run(args.step, auto=args.auto, provider=args.provider, language=args.language),
                          os.environ['VITA_TREE_EXECUTION_ID'])
        if not success:
            raise SystemExit(1)
    else:
        runpy.run_module('vita', run_name='__main__')


if __name__ == '__main__':
    main()
