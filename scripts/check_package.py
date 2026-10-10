"""Check distributable completeness and import the isolated installed wheel."""
from pathlib import Path
import sys
import tarfile
import zipfile

with zipfile.ZipFile('dist/vita_tree-0.1.0-py3-none-any.whl') as package:
    names = package.namelist()
    for name in ('latex.py', 'pdf.py', 'workspace.py', 'static/app.js',
                 'static/vendor/pdf.mjs', 'static/vendor/pdf.worker.mjs',
                 'static/vendor/pdf_viewer.css', 'static/vendor/PDFJS-LICENSE'):
        assert 'vita_tree/' + name in names, name
    assert len([n for n in names if '/static/vendor/' in n]) == 202
    assert b'Requires-Dist: pylatexenc==2.10' in package.read('vita_tree-0.1.0.dist-info/METADATA')
with tarfile.open('dist/vita_tree-0.1.0.tar.gz') as package:
    names = package.getnames()
    for name in ('tests/support.py', 'tests/browser_check.py', 'scripts/vendor-pdf.mjs', 'package-lock.json'):
        assert any(n.endswith('/' + name) for n in names), name

installed = Path('.test-artifacts/package-smoke').resolve()
sys.path.insert(0, str(installed))
from vita_tree import server
from vita_tree.latex import parse_document

assert Path(server.__file__).is_relative_to(installed)
assert server.STATIC_ROOT.is_dir()
assert (server.STATIC_ROOT / 'vendor/pdf.worker.mjs').is_file()
assert parse_document(r'\begin{document}\textbf{Installed wheel}\end{document}')["error"] is None
print('PASS: wheel import, parser, all 202 vendor assets/licenses, dependency metadata, and source-distribution test/build inputs.')
