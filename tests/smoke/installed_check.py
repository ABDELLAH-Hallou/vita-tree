"""Exercise an installed distribution; run with Python -I outside the checkout."""
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.request import Request, urlopen

import vita_tree
from vita_tree.latex import parse_document
from vita_tree.server import STATIC_ROOT, VitaTreeServer


def main():
    version = importlib.metadata.version('vita-tree')
    assert vita_tree.__version__ == version
    assert Path(vita_tree.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    for command in ('vt', 'vita-tree'):
        entry = Path(sys.executable).parent / (command + ('.exe' if os.name == 'nt' else ''))
        output = subprocess.check_output([str(entry), '--version'], text=True).strip()
        assert output == f'vita-tree {version}', output
    subprocess.run([sys.executable, '-I', '-m', 'vita_tree', '--help'], check=True, capture_output=True)
    source = r'\documentclass{article}\begin{document}\textbf{Installed CV}\end{document}'
    assert parse_document(source)['error'] is None
    repo = Path.cwd() / 'cv'
    repo.mkdir()
    def git(*args):
        subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)
    git('init', '-b', 'master')
    git('config', 'user.name', 'Package test'); git('config', 'user.email', 'test@example.invalid')
    (repo / 'main.tex').write_text(source, encoding='utf-8')
    git('add', 'main.tex'); git('commit', '-m', 'Fixture')
    server = VitaTreeServer(('127.0.0.1', 0), repo, 'main.tex')
    if '--expect-ai' in sys.argv:
        assert server.workspace.ai_bridge(), 'Installed [ai] extra was not discovered'
        assert server.workspace.vita_source.is_relative_to(Path(sys.prefix).resolve())
        assert server.workspace.vita_command()[1].endswith('ai_runner.py')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    def get(path):
        with urlopen(base + path) as response:
            return json.load(response)
    try:
        for name in ('index.html', 'app.js', 'styles.css', 'theme.js', 'vendor/pdf.mjs', 'vendor/pdf.worker.mjs', 'vendor/PDFJS-LICENSE', 'vendor/editor.mjs', 'vendor/EDITOR-LICENSE'):
            with urlopen(base + '/' + name) as response:
                assert response.read() == (STATIC_ROOT / name).read_bytes(), name
        assert len(list((STATIC_ROOT / 'vendor').rglob('*.*'))) > 150
        assert get('/api/branches')['branches'][0]['name'] == 'master'
        assert get('/api/providers?branch=master')['default']['provider'] == 'openai'
        snapshot = get('/api/workspace?branch=master')
        assert 'Installed CV' in snapshot['document']['html']
        token = get('/api/session')['token']
        request = Request(base + '/api/lint', data=json.dumps({'content':r'\textbf{unfinished'}).encode(), headers={'Content-Type':'application/json','X-Vita-Token':token})
        with urlopen(request) as response:
            assert json.load(response)['diagnostics'][0]['severity'] == 'error'
        body = {'branch':'master', 'path':'main.tex', 'revision':snapshot['revision'], 'content':source + '\n% Saved from installed package'}
        request = Request(base + '/api/save', data=json.dumps(body).encode(), headers={'Content-Type':'application/json','X-Vita-Token':token})
        with urlopen(request) as response:
            assert json.load(response)['content'] == body['content']
        assert (repo / 'main.tex').read_text(encoding='utf-8') == body['content']
    finally:
        server.shutdown(); server.server_close(); thread.join()
    print(f'PASS: installed vita-tree {version}, both CLI entries, bundled UI/PDF assets, parser, HTTP API and real file save.')


if __name__ == '__main__':
    main()
