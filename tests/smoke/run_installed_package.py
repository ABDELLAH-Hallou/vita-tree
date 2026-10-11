"""Install real artifacts in a fresh venv, outside the source tree."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def run(command, cwd):
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env['PYTHONUTF8'] = '1'
    result = subprocess.run([str(c) for c in command], cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stdout + '\n' + result.stderr)
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('distribution', type=Path, help='Wheel or source archive to install')
    parser.add_argument('--ai', action='store_true', help='Also verify the published vita-cv extra')
    args = parser.parse_args()
    artifact = args.distribution.resolve()
    if not artifact.is_file():
        raise SystemExit(f'Missing distribution: {artifact}')
    check = Path(__file__).with_name('installed_check.py').resolve()
    with tempfile.TemporaryDirectory(prefix='vita-tree-release-') as directory:
        root = Path(directory)
        venv.EnvBuilder(with_pip=True).create(root / 'venv')
        python = root / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        requirement = str(artifact) + ('[ai]' if args.ai else '')
        run([python, '-m', 'pip', 'install', '--disable-pip-version-check', requirement], root)
        run([python, '-m', 'pip', 'check'], root)
        command = [python, '-I', check]
        if args.ai:
            command.append('--expect-ai')
        print(run(command, root), end='')
    print(f'PASS: isolated {artifact.name}' + (' with [ai]' if args.ai else ''))


if __name__ == '__main__':
    main()
