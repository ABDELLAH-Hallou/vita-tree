"""Exercise the real requirements generator with a deterministic fake provider."""
import json
import os
from pathlib import Path
import sys
import socket
from unittest.mock import patch

sys.path[:0]=[str(Path(__file__).resolve().parents[2]/'src'),str(Path(__file__).resolve().parents[1])]
from vita.helpers import env
original=env.load_env
env.load_env=lambda:{**original(),**os.environ}
from vita.commands import requirements as command
from vita_tree.ai_runner import extract_requirements
from vita_tree.outcomes import execute
from requirements_fixtures import proposal

origin=Path.cwd()
def forbidden(*args,**kwargs):
    raise AssertionError('No provider/network calls in canonical requirements tests')
socket.create_connection=forbidden
socket.socket.connect=forbidden
raw=(origin/'job.md').read_text(encoding='utf-8')
(origin/'.vita/results').mkdir(parents=True,exist_ok=True)
def generate(system,prompt,**route):
    assert Path.cwd()!=origin
    assert not Path('main.tex').exists()
    assert not (Path.cwd()/'cv.yaml').exists()
    assert 'PRIVATE-CANDIDATE' not in prompt+system
    assert route['provider']=='codex' and route['model']=='fixture-model'
    assert os.environ['VITA_TREE_REASONING']=='high'
    assert 'no candidate CV' in system
    (origin/'isolated-generation').touch()
    if len(sys.argv)>1:
        from vita.helpers.provider_errors import ProviderError
        raise ProviderError(code='authentication',status=401)
    return json.dumps(proposal(raw))

with patch.object(command,'generate',generate):
    success=execute('extract',lambda:extract_requirements(lambda:True,'codex',os.environ['VITA_TREE_EXECUTION_ID']),os.environ['VITA_TREE_EXECUTION_ID'])
raise SystemExit(0 if success else 1)
