import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch

from vita_tree.server import VitaTreeServer
from vita_tree.workspace import Workspace, ConflictError, digest, safe_path
from support import SOURCE, cleanup_repo, git, init_repo


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.temp.name))
        self.workspace = Workspace(self.root)

    def tearDown(self):
        cleanup_repo(self.temp)

    def create(self):
        return self.workspace.create('master','etp-acme-swe','Acme seeks a Python engineer',digest(SOURCE))

    def test_create_and_edit_preserve_original_checkout(self):
        before = git(self.root,'status','--porcelain')
        branch = self.create()
        self.assertEqual(branch['job'],'Acme seeks a Python engineer')
        self.assertEqual(git(self.root,'branch','--show-current'),'master')
        self.assertEqual(git(self.root,'status','--porcelain'),before)
        self.assertTrue(Path(branch['worktree']).is_dir())
        result = self.workspace.save(branch['branch'],'main.tex',branch['revision'],SOURCE.replace('reliable','excellent'))
        self.assertIn('excellent',Path(result['path']).read_text())
        self.assertEqual((self.root/'main.tex').read_text(),SOURCE)
        snapshot = self.workspace.snapshot(branch['branch'])
        self.assertIn('+',snapshot['diff'])
        self.assertTrue(snapshot['dirty'])

    def test_uncommitted_source_is_used_as_original_for_new_branch(self):
        altered = SOURCE.replace('reliable','custom')
        (self.root/'main.tex').write_text(altered)
        branch = self.workspace.create('master','new','Job',digest(altered))
        self.assertEqual(branch['original'],altered)
        self.assertEqual(branch['content'],altered)

    def test_stale_save_and_branch_creation_rejected(self):
        branch=self.create()
        (Path(branch['worktree'])/'main.tex').write_text('External change')
        with self.assertRaises(ConflictError):
            self.workspace.save(branch['branch'],'main.tex',branch['revision'],'Overwrite')
        with self.assertRaises(ConflictError):
            self.workspace.create(branch['branch'],'next','Job',branch['revision'])
        self.assertEqual((Path(branch['worktree'])/'main.tex').read_text(),'External change')

    def test_path_traversal_invalid_branch_duplicate_and_remote(self):
        for value in ('../secret','.git/config','C:/secret','a\\b','/tmp/secret','.'):
            with self.assertRaises(ValueError):safe_path(self.root,value)
        self.create()
        with self.assertRaises(ValueError):self.create()
        with self.assertRaises(ValueError):self.workspace.create('master','--bad','Job',digest(SOURCE))
        git(self.root,'update-ref','refs/remotes/origin/remote','HEAD')
        with self.assertRaises(ValueError):self.workspace.save('remote','main.tex',digest(SOURCE),'x')

    def test_existing_uncommitted_reports_are_read(self):
        results=self.root/'.vita/results';results.mkdir(parents=True)
        (results/'analyze.md').write_text('# Analysis\nGood match')
        self.assertIn('Good match',self.workspace.snapshot('master')['artifacts']['analyze']['content'])

    def test_ai_failure_with_zero_exit_is_not_success(self):
        branch=self.create()
        with patch.object(self.workspace,'vita_command',return_value=['fake-vita']), patch('vita_tree.pdf.export_snapshot'):
            import subprocess
            actual=subprocess.run
            def fake(args,**kwargs):
                if args[0]=='fake-vita':return subprocess.CompletedProcess(args,0,b'Failed',b'')
                return actual(args,**kwargs)
            with patch('vita_tree.workspace.subprocess.run',side_effect=fake):
                job=self.workspace.start_ai(branch['branch'],branch['revision'],branch['jobRevision'])
                self.wait_job(job['id'])
        self.assertEqual(self.workspace.jobs[job['id']]['status'],'failed')
        self.assertEqual(self.workspace.read(branch['branch'],'main.tex'),SOURCE)

    def wait_job(self,ident):
        for _ in range(200):
            if self.workspace.jobs[ident]['status']!='running':return
            time.sleep(.05)
        self.fail('AI job did not finish')

    def test_ai_success_reports_and_original_snapshot(self):
        branch=self.create()
        import subprocess
        actual=subprocess.run
        def fake(args,**kwargs):
            if args[0]!='fake-vita':return actual(args,**kwargs)
            cwd=Path(kwargs['cwd']);results=cwd/'.vita/results';results.mkdir(parents=True,exist_ok=True)
            (results/(args[1]+'.md')).write_text('# '+args[1]+' report')
            if args[1]=='adapt':(cwd/'main.tex').write_text(SOURCE.replace('reliable','adapted'))
            return subprocess.CompletedProcess(args,0,b'',b'')
        with patch.object(self.workspace,'vita_command',return_value=['fake-vita']),patch('vita_tree.workspace.subprocess.run',side_effect=fake):
            job=self.workspace.start_ai(branch['branch'],branch['revision'],branch['jobRevision'])
            self.wait_job(job['id'])
        self.assertEqual(self.workspace.jobs[job['id']]['status'],'succeeded',self.workspace.jobs[job['id']])
        current=self.workspace.snapshot(branch['branch'])
        self.assertEqual(current['original'],SOURCE)
        self.assertIn('adapted',current['content'])
        self.assertIn('analyze',current['artifacts'])


class HTTPTests(unittest.TestCase):
    def test_lint_unsaved_source_is_authenticated_and_does_not_write(self):
        original = (self.root/'main.tex').read_bytes()
        req = Request(self.url+'/api/lint', data=json.dumps({'content':r'\textbf{broken'}).encode(), headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 403)
        req.add_header('X-Vita-Token', self.server.token)
        with urlopen(req) as response:
            self.assertEqual(len(json.load(response)['diagnostics']), 1)
        self.assertEqual((self.root/'main.tex').read_bytes(), original)
        req = Request(self.url+'/api/lint', data=b'{"content":42}', headers={'Content-Type':'application/json', 'X-Vita-Token':self.server.token})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 400)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=init_repo(Path(self.temp.name));self.server=VitaTreeServer(('127.0.0.1',0),self.root,'main.tex')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();cleanup_repo(self.temp)

    def test_api_token_origin_and_valid_write(self):
        session=json.load(urlopen(self.url+'/api/session'))
        body=json.dumps({'branch':'master','path':'main.tex','revision':digest(SOURCE),'content':SOURCE+'\n'}).encode()
        req=Request(self.url+'/api/save',data=body,headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as error:urlopen(req)
        self.assertEqual(error.exception.code,403)
        req.add_header('X-Vita-Token',session['token']);req.add_header('Origin','https://evil.example')
        with self.assertRaises(HTTPError) as error:urlopen(req)
        self.assertEqual(error.exception.code,403)
        req.remove_header('Origin')
        result=json.load(urlopen(req));self.assertEqual(result['content'],SOURCE+'\n')

    def test_malformed_json_and_module_mime(self):
        req=Request(self.url+'/api/save',data=b'[]',headers={'Content-Type':'application/json','X-Vita-Token':self.server.token})
        with self.assertRaises(HTTPError) as error:urlopen(req)
        self.assertEqual(error.exception.code,400)
        with urlopen(self.url+'/vendor/pdf.mjs') as response:
            self.assertIn(response.headers.get_content_type(),('text/javascript','application/javascript'))

    def test_asset_mime_ignores_host_file_associations(self):
        with patch('mimetypes.guess_type', return_value=('text/plain', None)):
            for path, expected in (
                ('/app.js', 'text/javascript'),
                ('/vendor/pdf.mjs', 'text/javascript'),
                ('/vendor/pdf_viewer.css', 'text/css'),
                ('/vendor/wasm/qcms_bg.wasm', 'application/wasm'),
            ):
                with self.subTest(path=path), urlopen(self.url+path) as response:
                    self.assertEqual(response.headers.get_content_type(), expected)
