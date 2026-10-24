"""Bounded local boundary checks; all secrets and repositories are synthetic."""
import http.client
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile
from urllib.parse import quote,quote_plus

from support import init_repo,cleanup_repo,git,SOURCE
from vita_tree.server import VitaTreeServer,DashboardHandler,git_document
from vita_tree.workspace import Workspace,safe_path,read_text
from vita_tree.ai_config import stage_environment
from vita_tree.pdf import _extract_snapshot,export_snapshot,compile_document
from vita_tree.security import compiler_environment,engine_executable,scrub_generated
from vita_tree import checkpoints


class HTTPBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        cls.root=init_repo(Path(cls.temp.name))
        cls.server=VitaTreeServer(('127.0.0.1',0),cls.root,'main.tex',log_dir=cls.root/'.git/test-logs')
        cls.worker=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.worker.join();cleanup_repo(cls.temp)

    def request(self,path='/api/session',headers=None,method='GET',body=None):
        client=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            client.request(method,path,body=body,headers=headers or {})
            response=client.getresponse();return response.status,dict(response.getheaders()),response.read()
        finally:client.close()

    def auth(self,**more):
        return {'X-Vita-Token':self.server.token,'Content-Type':'application/json',**more}

    def test_origin_host_fetch_metadata_and_head_share_the_boundary(self):
        for method in ('GET','HEAD'):
            for headers in ({'Host':'unrelated.invalid'},{'Origin':'null'},
                            {'Origin':'http://127.0.0.1:1'},{'Sec-Fetch-Site':'cross-site'},{'Sec-Fetch-Site':'same-site'}):
                with self.subTest(method=method,headers=headers):
                    self.assertEqual(self.request('/',headers,method)[0],403)
        for site in ('same-origin','none'):
            self.assertEqual(self.request(headers={'Sec-Fetch-Site':site})[0],200)
        # Non-browser clients are same-OS-user clients, not authenticated tenants.
        status,headers,body=self.request()
        self.assertEqual(status,200);self.assertIn('token',json.loads(body))
        self.assertNotIn('Access-Control-Allow-Origin',headers)
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertIn("object-src 'none'",headers['Content-Security-Policy'])
        # Rejected HEAD requests still obey HTTP's no-response-body rule.
        with socket.create_connection(('127.0.0.1',self.server.server_port),timeout=3) as client:
            client.sendall(b'HEAD / HTTP/1.0\r\nHost: unrelated.invalid\r\n\r\n')
            response=b''
            while chunk:=client.recv(4096):response+=chunk
        head,body=response.split(b'\r\n\r\n',1)
        self.assertIn(b'403',head);self.assertEqual(body,b'')

    def test_post_requires_token_origin_and_json_and_bounds_the_body(self):
        for headers in ({},{'Content-Type':'application/json'},self.auth(Origin='http://unrelated.invalid'),
                        self.auth(**{'Sec-Fetch-Site':'cross-site'})):
            self.assertEqual(self.request('/api/lint',headers,'POST',b'{}')[0],403)
        for headers,body in ((self.auth(**{'Content-Length':'3000001'}),None),
                             (self.auth(**{'Content-Length':'-1'}),None),
                             (self.auth(**{'Content-Length':'SYNTHETIC-HEADER-CANARY'}),None),
                             (self.auth(**{'Content-Type':'text/plain'}),b'{}'),
                             (self.auth(),b'['*1200+b']'*1200)):
            status,_,content=self.request('/api/lint',headers,'POST',body)
            self.assertEqual(status,400);self.assertNotIn(b'SYNTHETIC-HEADER-CANARY',content)
        self.assertEqual(self.request('/api/lint',self.auth(),'POST',json.dumps({'content':SOURCE}).encode())[0],200)

    def test_short_and_idle_bodies_do_not_invoke_the_action(self):
        with patch.object(self.server.workspace,'cleanup_checkpoints') as action:
            with patch.object(DashboardHandler,'idle_timeout',.1):
                client=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
                client.request('POST','/api/checkpoints-cleanup',body=b'{}',headers=self.auth(**{'Content-Length':'10'}))
                self.assertEqual(client.getresponse().status,400);client.close()
            action.assert_not_called()

    def test_errors_redact_known_credentials_and_remote_userinfo_without_logging_values(self):
        secret='SYNTHETIC-SESSION-BOUNDARY-KEY'
        self.server.workspace.add_connection('Synthetic','openai',secret)
        with patch.object(self.server.workspace,'snapshot',side_effect=ValueError('Rejected '+secret+' https://synthetic-user:synthetic-password@example.invalid/repo')):
            status,_,body=self.request('/api/workspace?branch=master')
        self.assertEqual(status,400)
        for marker in (secret,'synthetic-password'):
            self.assertNotIn(marker,body.decode())
            self.assertNotIn(marker,json.dumps(self.server.diagnostics.snapshot()))

    def test_constructor_cannot_expose_the_server_on_all_interfaces(self):
        with self.assertRaises(ValueError):VitaTreeServer(('0.0.0.0',0),self.root,'main.tex')


class FileCompilerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=Path(self.temp.name).resolve();self.repo=init_repo(self.root/'repo')

    def tearDown(self):cleanup_repo(self.temp)

    def test_paths_symlinks_and_snapshot_archive_entries_cannot_escape(self):
        for name in ('../outside','/outside','C:/outside','a\\outside','a/../../outside','a:stream','\0'):
            with self.subTest(name=name),self.assertRaises(ValueError):safe_path(self.repo,name)
        outside=self.root/'outside';outside.mkdir();(outside/'marker').write_text('SYNTHETIC-OUTSIDE')
        link=self.repo/'linked'
        try:link.symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('Symlink creation unavailable; CI Linux covers this boundary')
        with self.assertRaises(ValueError):safe_path(self.repo,'linked/marker')
        with self.assertRaises(ValueError):safe_path(link,'marker')
        with self.assertRaises(ValueError):export_snapshot(self.repo,git(self.repo,'rev-parse','HEAD'),self.root/'snapshot',self.repo)
        for name,mode in (('../outside.txt',0),('C:/outside.txt',0),('linked.txt',0o120777)):
            archive=io.BytesIO()
            with zipfile.ZipFile(archive,'w') as z:
                item=zipfile.ZipInfo(name);item.external_attr=mode<<16;z.writestr(item,'synthetic')
            archive.seek(0)
            with self.subTest(name=name),self.assertRaises(ValueError):_extract_snapshot(archive,self.root/'snapshot')
        self.assertEqual((outside/'marker').read_text(),'SYNTHETIC-OUTSIDE')

    def test_snapshot_omits_known_credentials_and_keeps_legitimate_local_includes(self):
        for name in ('.env','.env.local','.npmrc','.VITA/source-private.json','.ssh/id_rsa'):
            path=self.repo/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('SYNTHETIC-PRIVATE-COPY')
        (self.repo/'included.tex').write_text('Ordinary included material')
        git(self.repo,'add','--force','.');git(self.repo,'commit','-m','Synthetic snapshot assets')
        target=self.root/'snapshot';export_snapshot(self.repo,git(self.repo,'rev-parse','HEAD'),target,self.repo)
        self.assertEqual((target/'included.tex').read_text(),'Ordinary included material')
        self.assertFalse(any(b'SYNTHETIC-PRIVATE-COPY' in p.read_bytes() for p in target.rglob('*') if p.is_file()))

    def test_oversized_local_and_committed_sources_are_rejected_before_blob_read(self):
        (self.repo/'main.tex').write_text('x'*2_000_001)
        with self.assertRaises(ValueError):read_text(self.repo/'main.tex')
        git(self.repo,'add','main.tex');git(self.repo,'commit','-m','Synthetic oversized source')
        with patch('vita_tree.server.run_git',wraps=__import__('vita_tree.server',fromlist=['run_git']).run_git) as calls:
            with self.assertRaises(ValueError):git_document(self.repo,'HEAD','main.tex')
            self.assertFalse(any(call.args[1:3]==('cat-file','blob') for call in calls.call_args_list))

    def test_oversized_archive_entries_are_rejected_before_decompression(self):
        info=zipfile.ZipInfo('large.tex');info.file_size=100_000_001
        with patch('vita_tree.pdf.zipfile.ZipFile') as archive:
            archive.return_value.__enter__.return_value.infolist.return_value=[info]
            with self.assertRaises(ValueError):_extract_snapshot(io.BytesIO(),self.root/'snapshot')
            archive.return_value.__enter__.return_value.read.assert_not_called()

    def test_unbounded_compiler_diagnostics_are_not_buffered_in_memory(self):
        def compiler(args,**kwargs):
            if '--version' in args:return subprocess.CompletedProcess(args,0,b'engine',b'')
            kwargs['stdout'].write(b'x'*2_000_001)
            self.assertEqual(kwargs['stderr'],subprocess.STDOUT)
            return subprocess.CompletedProcess(args,0)
        with patch('vita_tree.pdf.engine_executable',return_value='trusted-fixture'),patch('vita_tree.pdf.subprocess.run',side_effect=compiler):
            with self.assertRaisesRegex(ValueError,'diagnostic limit'):compile_document(self.repo,'main.tex')

    def test_compiler_credentials_search_path_flags_and_installer_policy(self):
        output=self.repo/'out'
        with patch.dict(os.environ,{'OPENAI_API_KEY':'SYNTHETIC-COMPILER-KEY','AWS_SECRET_ACCESS_KEY':'SYNTHETIC-AWS-KEY',
                                    'TEXMFCNF':'unsafe-template-config','MIKTEX_CORE_ALLOWUNSAFEINPUTFILES':'true'}):
            env=compiler_environment(self.repo,output)
        self.assertNotIn('OPENAI_API_KEY',env);self.assertNotIn('AWS_SECRET_ACCESS_KEY',env);self.assertNotIn('TEXMFCNF',env)
        self.assertEqual(env['MIKTEX_PDFLATEX_CORE_ALLOWUNSAFEINPUTFILES'],'false')
        self.assertEqual(env['openout_any'],'p')
        fake=self.repo/('pdflatex.exe' if os.name=='nt' else 'pdflatex');fake.write_text('not executable')
        with self.assertRaises(ValueError):engine_executable('pdflatex',self.repo,{'PATH':str(self.repo)})
        calls=[]
        def compiler(args,**options):
            calls.append((args,options))
            self.assertNotIn('OPENAI_API_KEY',options['env'])
            if '--version' not in args:
                self.assertIn('-no-shell-escape',args);self.assertIn('--disable-installer',args);self.assertIn('--dont-parse-first-line',args)
                (output/'main.pdf').write_bytes(b'%PDF-1.7\nsynthetic')
            return subprocess.CompletedProcess(args,0,b'MiKTeX',b'')
        with patch('vita_tree.pdf.engine_executable',return_value='trusted-fixture'),patch('vita_tree.pdf.subprocess.run',side_effect=compiler):
            compile_document(self.repo,'main.tex',output=output)
        self.assertEqual(len(calls),3)

    def test_provider_environments_only_receive_the_selected_credentials(self):
        base={'OPENAI_API_KEY':'SYNTHETIC-OPENAI','ANTHROPIC_API_KEY':'SYNTHETIC-ANTHROPIC',
              'AWS_SECRET_ACCESS_KEY':'SYNTHETIC-AWS','GITHUB_TOKEN':'SYNTHETIC-GIT','OPENAI_ADMIN_KEY':'SYNTHETIC-ADMIN',
              'ANTHROPIC_BASE_URL':'https://synthetic.invalid','PATH':os.environ['PATH']}
        env=stage_environment(base,dict(provider='openai',model='fixture',reasoning='medium'))
        self.assertEqual(env['OPENAI_API_KEY'],base['OPENAI_API_KEY'])
        for name in ('ANTHROPIC_API_KEY','AWS_SECRET_ACCESS_KEY','GITHUB_TOKEN','OPENAI_ADMIN_KEY','ANTHROPIC_BASE_URL'):self.assertNotIn(name,env)
        alias=stage_environment({'GEMINI_API_KEY':'old','GOOGLE_API_KEY':'other'},dict(provider='google',model='fixture',reasoning=''),key='chosen')
        self.assertNotIn('GEMINI_API_KEY',alias);self.assertEqual(alias['GOOGLE_API_KEY'],'chosen')

    def test_detected_generated_credentials_are_withheld_before_a_checkpoint(self):
        secret='SYNTHETIC+OUTPUT CREDENTIAL/=?'
        results=self.repo/'.vita/results';results.mkdir(parents=True)
        forms={secret,quote(secret,safe=''),quote_plus(secret,safe='')}
        (results/'analysis.md').write_text('Provider accidentally echoed '+' '.join(forms))
        self.assertTrue(scrub_generated(self.repo,{secret}))
        for value in forms:self.assertNotIn(value,(results/'analysis.md').read_text())

    def test_checkpoint_tampering_and_paths_do_not_authorize_restore(self):
        ident='a'*32;root=self.repo/'.git/checkpoints';files=dict.fromkeys(checkpoints.ARTIFACTS)
        files['main.tex']=SOURCE
        outcome=dict(status='success',verified=True,backend=dict(status='success',attempts=[dict(category='valid')]))
        self.assertTrue(checkpoints.write_checkpoint(root,ident,'analyze','b'*64,files,outcome))
        self.assertIsNotNone(checkpoints.load_checkpoint(root,ident,'analyze'))
        manifest=root/ident/'analyze/manifest.json';value=json.loads(manifest.read_text());value['hashes']['../../outside']='c'*64;manifest.write_text(json.dumps(value))
        self.assertIsNone(checkpoints.load_checkpoint(root,ident,'analyze'))
        self.assertIsNone(checkpoints.load_checkpoint(root,'../outside','analyze'))

    def test_pdf_export_names_are_portable_and_cannot_inject_paths_or_headers(self):
        from vita_tree.exports import cv_filename
        filename=cv_filename(r'\name{../../Synthetic:Unsafe " Name}\begin{document}Body\end{document}')
        self.assertTrue(filename.startswith('cv-') and filename.endswith('.pdf'))
        for marker in ('/','\\',':','"','\r','\n'):self.assertNotIn(marker,filename)
