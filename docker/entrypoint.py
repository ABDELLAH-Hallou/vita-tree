#!/usr/local/bin/python
"""Start a persistent container workspace; never modify incompatible worktrees."""
import os
import json
from pathlib import Path
import subprocess
import sys


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def main():
    if len(sys.argv) > 1:
        os.execvp(sys.argv[1], sys.argv[1:])
    root = Path.cwd()
    subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', str(root)], check=True)
    if not any(root.iterdir()):
        subprocess.run(['git', 'init', '-b', 'main'], check=True)
        subprocess.run(['vita', 'init'], check=True)
        config_path = root/'.vita/config.json'
        config = json.loads(config_path.read_text(encoding='utf-8'))
        config.update(default_base_branch='main', author='Your_Name')
        config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
        (root/'main.tex').write_text(
            r'\documentclass{article}\begin{document}' '\n'
            r'\begin{center}\Large Your Name\end{center}' '\n'
            r'\section*{Summary}Replace this starter with your own CV.' '\n'
            r'\end{document}' '\n', encoding='utf-8')
        (root/'.gitignore').write_text('.vita/\nout/\n*.pdf\n*.aux\n*.log\n*.out\n', encoding='utf-8')
        subprocess.run(['git', 'add', 'main.tex', '.gitignore'], check=True)
        subprocess.run(['git', '-c', 'user.name=Vita Tree', '-c', 'user.email=local@example.invalid',
                        'commit', '-m', 'Create starter CV'], check=True)
    if not (root/'.git').is_dir():
        raise ValueError('Mount a complete repository with its .git directory, not a linked worktree. Your files were not changed.')
    # Existing native worktree records use absolute host paths. Do not repair,
    # prune or reinterpret them inside a different filesystem namespace.
    records = git('worktree', 'list', '--porcelain', '-z')
    for field in records.split('\0'):
        if field.startswith('worktree ') and not Path(field[9:]).is_dir():
            raise ValueError('Existing Git worktrees are not accessible inside this container. Use a separate container-owned clone; preserve native drafts first. Your Git metadata was not repaired or pruned.')
    if not (root/'main.tex').is_file():
        raise ValueError('The mounted project needs main.tex at its root. Copy the complete LaTeX project, then restart.')
    os.execvp('vt', ['vt', 'run', str(root), '--container', '--host', '0.0.0.0',
                     '--public-port', os.environ.get('VITA_TREE_PUBLIC_PORT', '8765'), '--no-browser',
                     '--log-dir', os.environ.get('VITA_TREE_LOG_DIR', str(root/'.git/vita-tree/container-logs'))])


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'Container setup: {error}', file=sys.stderr)
        sys.exit(1)
