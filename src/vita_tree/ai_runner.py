"""Child-process adapter for the source VITA CLI; never changes its installation."""
from __future__ import annotations

import os
from pathlib import Path
import runpy
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
        llm._call_codex_cli = lambda system, user, model='': call_codex(llm, system, user, model, reasoning)


def main():
    from vita.helpers import env, llm
    original_load = env.load_env
    env.load_env = lambda: {**original_load(), **os.environ}
    configure(llm)
    runpy.run_module('vita', run_name='__main__')


if __name__ == '__main__':
    main()
