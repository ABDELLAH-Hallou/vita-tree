"""Ensure stable release tags match the package's single version source."""
import ast
from pathlib import Path
import re
import sys


def package_version():
    module = ast.parse((Path(__file__).resolve().parents[1] / 'src/vita_tree/__init__.py').read_text(encoding='utf-8'))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('Missing __version__')


def validate(tag, version):
    if not re.fullmatch(r'v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', tag):
        raise ValueError('Release tags must use stable vX.Y.Z format.')
    if tag[1:] != version:
        raise ValueError(f'Tag {tag} does not match package version {version}.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/validate_release.py vX.Y.Z')
    try:
        validate(sys.argv[1], package_version())
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print('Validated vita-tree release ' + sys.argv[1])
