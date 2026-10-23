"""Optional interoperability check against a Vita CV source checkout; no AI calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch
import uuid

TESTS=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(TESTS.parent/'src'),str(TESTS)]


def emit():
    from vita.helpers import diagnostics as backend
    from vita.helpers.provider_errors import ProviderError
    @backend.diagnosed('step',name='analyze')
    def example():
        backend.routing('gemini','fixture-model',('gemini','fixture-model',{'reasoning_effort':'medium'},
                        {'GEMINI_API_KEY':'private-key-canary'}),{'provider_origin':'explicit','model_origin':'explicit'})
        backend.capture('request',[('system','private-document-canary'),('user','private-key-canary')])
        backend.capture('schema',{'type':'object','properties':{'overall_score':{'type':'integer'}},'required':['overall_score']})
        backend.capture('instructions')
        backend.http_metadata(401,{'x-request-id':'private-request-id-canary'},
                              json.dumps({'error':{'code':'UNAUTHENTICATED','message':'private-document-canary'}}),rejected=True)
        backend.failure('provider_request',ProviderError(code='authentication',status=401),
                        category='authentication',http_status=401,retryable=False)
        return False
    with patch('socket.create_connection',side_effect=AssertionError('Network calls are forbidden')),patch('socket.socket.connect',side_effect=AssertionError('Network calls are forbidden')):
        assert example() is False
    # Vita CV's own collector must respect Tree's reservation between steps.
    root=Path(os.environ['VITA_DIAGNOSTICS_DIR'])
    trace_id=os.environ['VITA_TRACEPARENT'].split('-')[1]
    with backend.storage_lock(root),patch.object(backend,'RETENTION_SECONDS',0):
        backend.enforce_storage(root,None,0)
    assert (root/trace_id/'manifest.json').is_file()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--vita-source',type=Path)
    parser.add_argument('--emit',action='store_true')
    args=parser.parse_args()
    if args.emit:
        emit();return
    if not args.vita_source or not (args.vita_source/'vita/helpers/diagnostics_contract.py').is_file():
        parser.error('Provide a Vita CV source checkout implementing diagnostics v1.')
    from support import init_repo,cleanup_repo,SOURCE,git
    from vita_tree.workspace import Workspace,digest
    temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
    root=init_repo(Path(temp.name))
    workspace=Workspace(root)
    ident=uuid.uuid4().hex
    record={'id':ident,'traceId':ident,'rootRunId':ident,'parentRunId':None,'attempt':1,'branch':'master',
            'createdAt':0,'status':'running','stepConfig':{'analyze':{'provider':'gemini','model':'fixture-model','reasoning':'medium'}}}
    workspace.jobs[ident]=record
    context={'env':{},'keys':{},'checkpointInputs':{key:digest(SOURCE) for key in ('source','job','config','criteria','backend')},
             'baseCommit':git(root,'rev-parse','HEAD')}
    workspace.inspector.begin(record,context,{'analyze':'shared'})
    env={**os.environ,**workspace.inspector.environment(record,'analyze'),'VITA_DIAGNOSTIC_CONTENT':'sanitized',
         'PYTHONPATH':str(args.vita_source.resolve()),'PYTHONUTF8':'1'}
    try:
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--emit'],cwd=root,env=env,capture_output=True,timeout=30)
        if result.returncode:
            raise AssertionError('Backend diagnostics interoperability subprocess failed; no model was called.')
        value=workspace.inspector.public_detail(ident)
        assert value['backend']['state']=='available',value['backend']
        assert value['overview']['category']=='authentication'
        assert any(e['details'].get('request_id_sha256')==hashlib.sha256(b'private-request-id-canary').hexdigest() for e in value['backend']['events'])
        kinds=set()
        for ref in value['backend']['artifacts']:
            kinds.add(ref['kind'])
            item=workspace.inspector.artifact(ident,ref['id'])
            assert item['state']!='unavailable' or ref['capture_status']=='unavailable',item
        assert {'request','schema','instructions','response','provider_error'} <= kinds
        all_records=json.dumps(value)+''.join(p.read_text(encoding='utf-8') for p in workspace.inspector.path(ident).rglob('*') if p.is_file())
        for canary in ('private-key-canary','private-document-canary','private-request-id-canary'):
            assert canary not in all_records
        record['status']='failed';workspace.inspector.finish(record)
        assert not (workspace.inspector.destination/('.reserve-'+ident+'.json')).exists()
        print('PASS: real Vita CV v1 producer, routing/error/request/schema/capture contracts, request-ID hashing, safe Tree artifact reader, canaries excluded, cross-product active retention reservation, no network/model calls.')
    finally:
        workspace.close();cleanup_repo(temp)


if __name__=='__main__':main()
