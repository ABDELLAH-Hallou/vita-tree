"""Synthetic host transport tests; no Codex generation or credentials."""
import unittest
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
from unittest.mock import patch
from vita_tree.codex_client import parse_arguments, local_file
from vita_tree.codex_host import validate_files, HostServer, HostCapacityError


class CodexBridgeTests(unittest.TestCase):
    def test_native_absolute_paths_stay_inside_captured_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            self.assertEqual(local_file(root,str(root/'reply.txt')),root/'reply.txt')
            with self.assertRaises(ValueError):local_file(root,str(root.parent/'outside.txt'))
            with self.assertRaises(ValueError):local_file(root,'../outside.txt')
    def test_native_schema_model_and_reasoning_arguments(self):
        options = parse_arguments(['exec', '--sandbox', 'read-only', '--model', 'synthetic-model',
            '--config', 'model_reasoning_effort="high"', '--output-schema', 'schema.json',
            '--output-last-message', 'reply.txt', '-'])
        self.assertEqual((options.model, options.reasoning), ('synthetic-model', 'high'))
        self.assertEqual(options.schema, 'schema.json')

    def test_client_rejects_arbitrary_command_options(self):
        with self.assertRaises(ValueError):
            parse_arguments(['exec', '--sandbox', 'read-only', '--output-last-message', 'reply.txt', '--dangerously-bypass-approvals-and-sandbox', '-'])

    def test_snapshot_rejects_traversal_credentials_and_excess_size(self):
        for files in ({'../main.tex': 'x'}, {'.env': 'secret'}, {'.vita/.env': 'secret'},
                      {'main.tex': 'x' * 8_000_001}):
            with self.assertRaises(ValueError): validate_files(files)
        self.assertEqual(validate_files({'main.tex': 'synthetic', 'job.md': 'role'}),
                         {'main.tex': 'synthetic', 'job.md': 'role'})


class HostTransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        root = Path(self.tmp.name)
        script = root/'fixture.py'
        script.write_text('''import sys,json,time,subprocess,os
from pathlib import Path
args=sys.argv[1:]; start=time.time(); prompt=sys.stdin.read()
if prompt=='wait':
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
 Path('child.json').write_text(json.dumps([os.getpid(),child.pid]))
 time.sleep(60)
if prompt.startswith('parallel-'):
 barrier=Path(__file__).parent/'barrier';barrier.mkdir(exist_ok=True)
 (barrier/prompt).write_text('ready')
 deadline=time.monotonic()+15
 while len(list(barrier.iterdir()))<2 and time.monotonic()<deadline:time.sleep(.02)
 if len(list(barrier.iterdir()))<2:raise RuntimeError('Sessions did not execute concurrently')
 time.sleep(.2)
else:time.sleep(.8)
schema=json.loads(Path(args[args.index('--output-schema')+1]).read_text()) if '--output-schema' in args else None
output={'prompt':prompt,'source':Path('main.tex').read_text(),'inputFiles':[p.as_posix() for p in Path('.').rglob('*.tex')],'args':args,'schema':schema,'start':start,'end':time.time()}
Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(output))
''',encoding='utf-8')
        executable = root/('codex.cmd' if os.name=='nt' else 'codex')
        executable.write_text((f'@echo off\n"{sys.executable}" "{script}" %*\n' if os.name=='nt'
                               else f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n'),encoding='utf-8')
        executable.chmod(0o755)
        self.token = 'synthetic-host-authentication-value-12345'
        self.auth = root/'auth'; self.auth.write_text(self.token); self.auth.chmod(0o600)
        self.server = HostServer((os.environ.get('VITA_TEST_HOST_BIND','127.0.0.1'),0),self.token,str(executable))
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.opener = build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()

    def request(self, method, path, data=None, *, token=None, origin=None):
        headers={'Authorization':'Bearer '+(self.token if token is None else token)}
        if origin:headers['Origin']=origin
        req=Request(self.url+path,method=method,headers=headers,
                    data=json.dumps(data).encode() if data is not None else None)
        with self.opener.open(req,timeout=5) as response:return json.load(response)

    def test_authentication_origin_and_native_client_contract(self):
        for extra in ({'token':'wrong'},{'origin':'http://evil.invalid'}):
            with self.assertRaises(HTTPError) as error:self.request('GET','/v1/capability',**extra)
            self.assertEqual(error.exception.code,403)
        folder=Path(self.tmp.name)/'client';folder.mkdir()
        (folder/'main.tex').write_text('captured synthetic source')
        (folder/'job.md').write_text('synthetic role')
        (folder/'.env').write_text('DO_NOT_TRANSFER=synthetic-secret')
        (folder/'schema.json').write_text('{"type":"object"}')
        environment={**os.environ,'VITA_CODEX_HOST_URL':self.url,'VITA_CODEX_HOST_AUTH_FILE':str(self.auth),
                     'PYTHONPATH':str(Path(__file__).resolve().parents[1]/'src')}
        result=subprocess.run([sys.executable,'-m','vita_tree.codex_client','exec','--sandbox','read-only',
            '--model','synthetic-model','-c','model_reasoning_effort="high"','--output-schema','schema.json',
            '--output-last-message','reply.txt','-'],input='synthetic prompt',text=True,
            cwd=folder,env=environment,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        output=json.loads((folder/'reply.txt').read_text())
        self.assertEqual(output['source'],'captured synthetic source')
        self.assertEqual(output['schema'],{'type':'object'})
        self.assertIn('synthetic-model',output['args'])
        self.assertIn('model_reasoning_effort="high"',output['args'])
        self.assertNotIn('synthetic-secret',json.dumps(output))
        self.assertFalse(self.server.jobs)

    def test_cancel_stops_host_process_descendants(self):
        request={'files':{'main.tex':'synthetic'},'prompt':'wait','model':'','reasoning':'','schema':None}
        value=self.request('POST','/v1/jobs',request)
        job=self.server.jobs[value['id']]
        path=Path(job['temporary'].name)/'project/child.json'
        deadline=time.monotonic()+15
        while not path.exists() and time.monotonic()<deadline:time.sleep(.05)
        self.assertTrue(path.exists(),'Fixture did not start')
        pids=json.loads(path.read_text())
        with patch.object(job['temporary'],'cleanup',side_effect=PermissionError('Synthetic transient lock')):
            self.assertTrue(self.request('DELETE','/v1/jobs/'+value['id'])['cancelled'])
            self.assertTrue(self.server.retired)
        from test_process_lifecycle import ProcessLifecycleTests
        for pid in pids:ProcessLifecycleTests.assert_stopped(self,pid)
        deadline=time.monotonic()+5
        while self.server.retired and time.monotonic()<deadline:
            self.server.reap()
            if self.server.retired:time.sleep(.05)
        self.assertFalse(self.server.retired,'Cancelled snapshot was not reclaimed')
        self.assertFalse(job['thread'].is_alive())

    def test_host_capacity_rejects_without_queue(self):
        request={'files':{'main.tex':'synthetic'},'prompt':'synthetic','model':'','reasoning':'','schema':None}
        with patch.object(self.server,'launch',side_effect=HostCapacityError):
            with self.assertRaises(HTTPError) as error:self.request('POST','/v1/jobs',request)
        self.assertEqual(error.exception.code,429)
        self.assertFalse(self.server.jobs)

    def test_shutdown_stops_active_host_job_and_rejects_new_work(self):
        request={'files':{'main.tex':'synthetic'},'prompt':'wait','model':'','reasoning':'','schema':None}
        value=self.request('POST','/v1/jobs',request)
        job=self.server.jobs[value['id']]
        path=Path(job['temporary'].name)/'project/child.json'
        deadline=time.monotonic()+15
        pids=None
        while time.monotonic()<deadline:
            try:pids=json.loads(path.read_text());break
            except (OSError,ValueError):time.sleep(.05)
        self.assertTrue(pids,'Fixture did not start')
        self.server.shutdown();self.thread.join();self.server.server_close()
        from test_process_lifecycle import ProcessLifecycleTests
        for pid in pids:ProcessLifecycleTests.assert_stopped(self,pid)
        self.assertFalse(self.server.jobs)
        with self.assertRaises(ValueError):self.server.launch(request)

    def test_parallel_sessions_and_disconnected_client_cleanup(self):
        request={'files':{'main.tex':'first'},'prompt':'parallel-one','model':'','reasoning':'','schema':None}
        first=self.request('POST','/v1/jobs',request)
        second=self.request('POST','/v1/jobs',{**request,'files':{'main.tex':'second'},'prompt':'parallel-two'})
        results={};deadline=time.monotonic()+20
        while len(results)<2 and time.monotonic()<deadline:
            for job in (first,second):
                value=self.request('GET','/v1/jobs/'+job['id'])
                if value['status']!='running':results[job['id']]=value
            time.sleep(.1)
        self.assertEqual(len(results),2)
        outputs=[json.loads(results[job['id']]['output']) for job in (first,second)]
        self.assertEqual([o['source'] for o in outputs],['first','second'])
        self.assertLess(max(o['start'] for o in outputs),min(o['end'] for o in outputs))
        self.server.lease_seconds=.1
        deadline=time.monotonic()+5
        while self.server.jobs and time.monotonic()<deadline:time.sleep(.1)
        self.assertFalse(self.server.jobs)
