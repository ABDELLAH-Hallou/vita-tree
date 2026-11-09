"""Real Vita CV provider-check/error producer through Tree; network forbidden."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]


def emit():
    from vita.helpers import llm
    from vita.helpers.provider_errors import ProviderError
    from vita_tree.ai_runner import main
    def synthetic(system, prompt, key, model, **kwargs):
        assert system=='You are running a connection diagnostic.'
        assert prompt=='Reply with OK.'
        assert key=='private-smoke-key'
        if model=='overloaded':raise ProviderError('private-smoke-key private-prompt',status=503)
        if model=='authentication':raise ProviderError('private-smoke-key private-prompt',status=401)
        return 'OK'
    sys.argv=['vita',*sys.argv[2:]]
    with patch.object(llm,'_call_gemini',side_effect=synthetic),patch('socket.create_connection',side_effect=AssertionError('Network forbidden')),patch('socket.socket.connect',side_effect=AssertionError('Network forbidden')):
        main()


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--emit':
        emit();return
    parser=argparse.ArgumentParser();parser.add_argument('--vita-source',type=Path,required=True)
    args=parser.parse_args()
    from support import init_repo,cleanup_repo
    from vita_tree.workspace import Workspace
    from vita_tree.provider_status import provider_error
    temp=tempfile.TemporaryDirectory(dir=Path.cwd(),prefix='.vita-tree-test-')
    root=init_repo(Path(temp.name));workspace=Workspace(root,vita_source=args.vita_source.resolve())
    command=[sys.executable,str(Path(__file__).resolve()),'--emit']
    try:
        with patch.object(workspace,'vita_command',return_value=command),patch.dict(os.environ,{'GEMINI_API_KEY':'private-smoke-key','VITA_PROVIDER_RETRY_BASE_SECONDS':'0','VITA_PROVIDER_RETRY_MAX_SECONDS':'0'}):
            for model in ('fixture-success','overloaded','authentication'):
                result=workspace.check_generation('master','extract',{'default':{'provider':'gemini','model':model},'steps':{}},True)
                if model=='fixture-success':assert result['generationVerified'],result
                else:
                    assert not result['generationVerified'] and result['failure']['category']==model,result
                    assert result['attempts']==(3 if model=='overloaded' else 1),result
                    assert result['failure']['retryable']==(model=='overloaded'),result
                assert result['provider']=='gemini' and result['model']==model,result
                assert 'private-smoke-key' not in json.dumps(result) and 'private-prompt' not in json.dumps(result)
        assert not list(workspace.root.glob('generation-check-*'))
        print('PASS: actual Vita CV provider-check v1 through Tree adapter; explicit model/connection, synthetic prompt only, typed 503/three transient attempts and 401/one permanent attempt, redaction, cleanup, no network/model calls.')
    finally:cleanup_repo(temp)


if __name__=='__main__':main()
