"""Actual Vita CV factual gate, synthetic wording, no AI/network requests."""
import os
from pathlib import Path
import runpy
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
step = sys.argv[1]
if step not in {'adapt', 'cover'}:
    runpy.run_path(str(Path(__file__).resolve().parents[1]/'fake_ai_process.py'), run_name='__main__')
else:
    from vita.helpers import factual_changes as facts
    from vita_tree.outcomes import execute
    def forbidden(*args, **kwargs):
        raise AssertionError('No provider/network calls in factual-review tests')
    socket.create_connection = forbidden
    socket.socket.connect = forbidden
    def generate():
        source = Path('main.tex').read_text(encoding='utf-8')
        if step == 'adapt':
            document = source.replace('reliable systems', 'dependable systems').replace(
                'Built Python services', 'Built OOP services').replace('Languages & Python, SQL, JavaScript', 'Languages & Python, SQL, Rust')
        else:
            document = source.replace(r'\begin{rSection}{Summary}', r'\begin{rSection}{Cover letter}')
        return facts.stage(facts.capture(step), document)
    success = execute(step, generate, os.environ['VITA_TREE_EXECUTION_ID'])
    raise SystemExit(0 if success else 1)
