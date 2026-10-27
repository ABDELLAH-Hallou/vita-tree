"""Validate the exact wheel/sdist contents before publication (no upload)."""
from email.parser import BytesParser
from email.utils import getaddresses
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import zipfile


def check(directory):
    wheels, sdists = list(directory.glob('*.whl')), list(directory.glob('*.tar.gz'))
    if len(wheels) != 1 or len(sdists) != 1:
        raise ValueError('Use a clean dist directory containing exactly one wheel and one sdist.')
    root = Path(__file__).resolve().parents[1]
    expected = {str(p.relative_to(root / 'src')).replace('\\', '/'): p
                for p in (root / 'src/vita_tree').rglob('*')
                if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = set(wheel.namelist())
        missing = expected.keys() - names
        if missing:
            raise ValueError(f'Wheel missing files: {sorted(missing)}')
        for name, path in expected.items():
            if wheel.read(name) != path.read_bytes():
                raise ValueError(f'Stale or changed wheel file: {name}')
        metadata = BytesParser().parsebytes(wheel.read(next(n for n in names if n.endswith('.dist-info/METADATA'))))
        assert metadata['Name'] == 'vita-tree'
        assert getaddresses(metadata.get_all('Author-email') or []) == [
            ('Abdellah HALLOU', 'abdeallahhallou33@gmail.com')
        ], 'Package must credit the approved project author'
        assert not metadata['Maintainer-email'], 'Unexpected maintainer contact metadata'
        assert metadata['License-Expression'] == 'MIT'
        assert metadata['Requires-Python'] == '>=3.10'
        requirements = metadata.get_all('Requires-Dist') or []
        assert any(r.startswith('pylatexenc==2.10') for r in requirements)
        assert any(r.startswith('vita-cv') and 'ai' in r for r in requirements)
        assert len(metadata.get_all('License-File') or []) >= 12
        version = metadata['Version']
        assert wheels[0].name == f'vita_tree-{version}-py3-none-any.whl'
        assert sdists[0].name == f'vita_tree-{version}.tar.gz'
        entries = wheel.read(next(n for n in names if n.endswith('.dist-info/entry_points.txt'))).decode()
        assert 'vt = vita_tree.cli:main' in entries and 'vita-tree = vita_tree.cli:main' in entries
    with tarfile.open(sdists[0]) as sdist:
        source_names = set(sdist.getnames())
        for path in ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'README.md', 'CHANGELOG.md', 'pyproject.toml',
                     'scripts/check_package.py', 'scripts/check_privacy.py', 'scripts/validate_release.py',
                     'scripts/vendor-pdf.mjs', 'tests/support.py', 'tests/browser_check.py',
                     'tests/smoke/run_installed_package.py', 'tests/smoke/installed_check.py', 'package-lock.json']:
            assert f'vita_tree-{version}/{path}' in source_names, path
        for name in expected:
            assert f'vita_tree-{version}/src/{name}' in source_names, name
        # The source archive must contain the exact licensed corpus needed to
        # reproduce compatibility evidence; test assets stay out of the wheel.
        corpus = root/'tests/fixtures/template_matrix'
        manifest = json.loads((corpus/'manifest.json').read_text(encoding='utf-8'))
        for fixture in manifest['fixtures']:
            for ref in fixture['files'].values():
                name = f'vita_tree-{version}/tests/fixtures/template_matrix/'+ref['fixture']
                assert name in source_names, name
                assert hashlib.sha256(sdist.extractfile(name).read()).hexdigest() == ref['sha256'], name
    for name in names | source_names:
        parts = PurePosixPath(name).parts
        assert not set(parts) & {'.env', '.git', '.venv', '.pypirc', '.test-artifacts', 'node_modules', '__pycache__'}, name
        assert not name.endswith(('.pdf', '.tex', '.pyc')), name
    for path in [wheels[0], sdists[0]]:
        print(f'{path.name}  sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}')
    print(f'PASS: {version} metadata, entry points, licenses, all {len(expected)} package files, and source inputs.')


if __name__ == '__main__':
    check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('dist'))
