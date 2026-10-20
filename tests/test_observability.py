import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from support import init_repo, SOURCE, cleanup_repo
from vita_tree.observability import Diagnostics
from vita_tree.fileio import atomic_write_bytes
from vita_tree.workspace import Workspace, digest, ConflictError
from vita_tree.server import VitaTreeServer
from vita_tree.pdf import PDFCompiler, PDFExistsError
from vita_tree.exports import cv_filename


class AtomicFileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=Path(self.temp.name)
    def tearDown(self):
        cleanup_repo(self.temp)

    def test_transient_permission_lock_retries_without_partial_file(self):
        import os
        path=self.root/'state.json';path.write_bytes(b'old')
        replace=os.replace
        calls=[]
        def locked(source,target):
            calls.append(1)
            self.assertEqual(path.read_bytes(),b'old')
            if len(calls)<3:raise PermissionError(13,'temporary lock')
            return replace(source,target)
        with patch('vita_tree.fileio.os.replace',side_effect=locked),patch('vita_tree.fileio.time.sleep'):
            atomic_write_bytes(path,b'complete')
        self.assertEqual(path.read_bytes(),b'complete')
        self.assertFalse(list(self.root.glob('*.tmp')))

    def test_cleanup_failure_does_not_mask_original_error_or_replace_target(self):
        path=self.root/'state.json';path.write_bytes(b'old')
        original=PermissionError(13,'replace denied',str(path))
        with patch('vita_tree.fileio.os.replace',side_effect=original),patch('pathlib.Path.unlink',side_effect=PermissionError('cleanup denied')),patch('vita_tree.fileio.time.sleep'):
            with self.assertRaises(PermissionError) as raised:atomic_write_bytes(path,b'new')
        self.assertIs(raised.exception,original)
        self.assertEqual(path.read_bytes(),b'old')

    def test_logs_are_bounded_and_exclude_payloads_exception_text_and_paths(self):
        diag=Diagnostics(self.root/'logs','DEBUG')
        try:
            diag.handler.maxBytes=700
            try:raise PermissionError(13,'private-provider-canary','/private/person/credentials')
            except PermissionError as error:diag.error('history_write_failed',error,run_id='a'*32)
            first=diag.snapshot()
            self.assertEqual(first['events'][0]['errno'],13)
            self.assertEqual(first['events'][0]['error_type'],'PermissionError')
            diag.record('request_failed',prompt='private-provider-canary',headers={'Authorization':'private-provider-canary'},route='/api/jobs?token=private-provider-canary')
            diag.request('POST','/api/save',500,.125,'b'*12)
            diag.request('GET','/unknown/private-provider-canary',404,.1,'c'*12)
            content=json.dumps(diag.snapshot()['events'])+diag.prometheus()
            self.assertNotIn('private-provider-canary',content)
            self.assertNotIn('/private/person',content)
            self.assertIn('vita_tree_http_requests_total',content)
            self.assertEqual(diag.snapshot()['requests']['failed'],2)
            for _ in range(70):diag.record('run_started',run_id='d'*32,status='running')
            self.assertLessEqual(len(list((self.root/'logs').glob('vita-tree-*'))),6)
            raw=''.join(path.read_text() for path in (self.root/'logs').glob('vita-tree-*'))
            self.assertNotIn('private-provider-canary',raw)
        finally:diag.close()

    def test_unwritable_log_directory_keeps_memory_diagnostics(self):
        with patch('pathlib.Path.mkdir',side_effect=PermissionError(13,'private-canary')):
            diag=Diagnostics(self.root/'logs')
        diag.record('run_started',run_id='a'*32,status='running')
        result=diag.snapshot()
        self.assertFalse(result['logging']['enabled'])
        self.assertIn('--log-dir',result['logging']['error'])
        self.assertIn('logging_failed',[event['event'] for event in result['events']])
        self.assertNotIn('private-canary',json.dumps(result))


class PersistenceAndPDFTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=init_repo(Path(self.temp.name));self.workspace=Workspace(self.root)
    def tearDown(self):
        self.workspace.close();cleanup_repo(self.temp)

    def test_review_permission_failure_keeps_memory_and_disk_unreviewed_then_retries(self):
        record={'id':'a'*32,'branch':'master','status':'succeeded','step':'completed','reviewed':False,'stages':[]}
        self.workspace.jobs[record['id']]=record;self.workspace._persist_job(record)
        with patch('vita_tree.workspace.atomic_write',side_effect=PermissionError(13,'private-canary')):
            with self.assertRaisesRegex(RuntimeError,'remain unreviewed'):self.workspace.review_job(record['id'])
        self.assertFalse(self.workspace.get_job(record['id'])['reviewed'])
        self.assertFalse(json.loads((self.workspace.root/'job-history'/('a'*32+'.json')).read_text())['reviewed'])
        self.assertEqual(self.workspace.diagnostics.snapshot()['events'][0]['error_type'],'PermissionError')
        self.workspace.review_job(record['id'])
        reopened=Workspace(self.root)
        try:self.assertTrue(reopened.get_job(record['id'])['reviewed'])
        finally:reopened.close()

    def test_bulk_review_partial_failure_active_run_and_retry(self):
        for letter, status in [('a','succeeded'),('b','failed'),('c','running')]:
            record={'id':letter*32,'branch':'master','status':status,'step':'completed','reviewed':False,'stages':[]}
            self.workspace.jobs[record['id']]=record;self.workspace._persist_job(record)
        from vita_tree.workspace import atomic_write
        def denied(path, content):
            if path.name.startswith('b'*32):raise PermissionError(13,'private-canary')
            return atomic_write(path,content)
        with patch('vita_tree.workspace.atomic_write',side_effect=denied):
            result=self.workspace.review_jobs(['a'*32,'b'*32,'c'*32,'d'*32,'a'*32])
        self.assertEqual(result['reviewed'],['a'*32]);self.assertEqual(len(result['failed']),3)
        self.assertTrue(self.workspace.get_job('a'*32)['reviewed'])
        self.assertFalse(self.workspace.get_job('b'*32)['reviewed'])
        self.assertFalse(self.workspace.get_job('c'*32)['reviewed'])
        self.assertNotIn('private-canary',json.dumps(result))
        self.assertEqual(self.workspace.review_jobs(['a'*32,'b'*32])['reviewed'],['a'*32,'b'*32])
        reopened=Workspace(self.root)
        try:self.assertTrue(reopened.get_job('b'*32)['reviewed'])
        finally:reopened.close()
        for invalid in ([],['invalid'],'all',['a'*32]*501):
            with self.assertRaises(ValueError):self.workspace.review_jobs(invalid)

    def test_branch_permission_failure_is_actionable_without_creating_branch(self):
        from vita_tree.server import run_git
        import subprocess
        import vita_tree.workspace as module
        original=module.run_git
        def denied(repository,*args,**kwargs):
            if 'worktree' in args and 'add' in args:
                with patch('vita_tree.server.subprocess.run',return_value=subprocess.CompletedProcess(args,128,'',"fatal: cannot lock ref: Unable to create /private/person/cv.lock: Permission denied")):
                    return run_git(repository,*args,**kwargs)
            return original(repository,*args,**kwargs)
        with patch('vita_tree.workspace.run_git',side_effect=denied):
            with self.assertRaises(PermissionError) as error:self.workspace.create('master','denied-branch','A role',digest(SOURCE))
        self.assertEqual(error.exception.errno,13)
        self.assertNotIn('/private/person',str(error.exception))
        self.assertNotIn('denied-branch',original(self.root,'branch','--list'))
        self.assertEqual(self.workspace.read('master','main.tex'),SOURCE)
        created=self.workspace.create('master','denied-branch','A role',digest(SOURCE))
        self.assertEqual(created['branch'],'denied-branch')

    def test_progress_persistence_failure_stops_work_and_keeps_failure_visible(self):
        record={'id':'c'*32,'branch':'master','status':'running','step':'analyze','reviewed':False,'stages':[]}
        self.workspace.jobs[record['id']]=record;self.workspace._persist_job(record)
        with patch('vita_tree.workspace.atomic_write',side_effect=PermissionError(13,'private-canary')):
            with self.assertRaisesRegex(ValueError,'could not save its status'):
                self.workspace._job_update(record,step='adapt')
            self.assertEqual(record['step'],'analyze')
            self.assertTrue(self.workspace._job_update(record,status='failed',step='failed'))
        self.assertEqual(self.workspace.get_job(record['id'])['status'],'failed')
        self.assertIn('history could not be saved',record['message'])
        self.assertNotIn('private-canary',json.dumps(self.workspace.list_jobs()))

    def preview(self,side='current'):
        branch=self.workspace.create('master','cv-export','A role',digest(SOURCE))
        compiler=PDFCompiler(self.workspace);pdf=self.root/'.git/preview.pdf';pdf.write_bytes(b'%PDF-1.7\nsynthetic preview')
        ident='b'*32;compiler.results[ident]=pdf
        compiler.previews[ident]={'branch':branch['branch'],'side':side,'revision':digest(branch['original'] if side=='original' else branch['content']),
                                 'filename':cv_filename(SOURCE,side),'commit':branch['commit']}
        return compiler,branch,ident,pdf

    def test_export_uses_existing_worktree_and_compare_before_overwrite(self):
        compiler,branch,ident,pdf=self.preview()
        result=compiler.save(ident,branch['branch'])
        target=Path(result['path'])
        self.assertEqual(target,Path(branch['worktree'])/'cv-Jordan_Lee.pdf')
        self.assertEqual(target.read_bytes(),pdf.read_bytes())
        with self.assertRaises(PDFExistsError) as raised:compiler.save(ident,branch['branch'])
        revision=raised.exception.revision
        target.write_bytes(b'%PDF-1.7\nexternal edit')
        with self.assertRaises(PDFExistsError):compiler.save(ident,branch['branch'],revision)
        self.assertIn(b'external edit',target.read_bytes())
        revision=__import__('hashlib').sha256(target.read_bytes()).hexdigest()
        compiler.save(ident,branch['branch'],revision)
        self.assertEqual(target.read_bytes(),pdf.read_bytes())
        self.assertEqual(self.workspace.read(branch['branch'],'main.tex'),SOURCE)

    def test_export_rejects_stale_branch_wrong_branch_and_unsafe_destination(self):
        compiler,branch,ident,pdf=self.preview()
        with self.assertRaises(ConflictError):compiler.save(ident,'master')
        compiler.previews[ident]['filename']='../outside.pdf'
        with self.assertRaises(ValueError):compiler.save(ident,branch['branch'])
        compiler.previews[ident]['filename']='cv-Jordan_Lee.pdf'
        self.workspace.save(branch['branch'],'main.tex',branch['revision'],SOURCE+'\n% changed')
        with self.assertRaisesRegex(ConflictError,'changed after this PDF'):compiler.save(ident,branch['branch'])
        self.assertFalse((Path(branch['worktree'])/'cv-Jordan_Lee.pdf').exists())

    def test_original_export_has_separate_name_and_permission_failure_preserves_pdf(self):
        compiler,branch,ident,pdf=self.preview('original')
        target=Path(branch['worktree'])/'cv-Jordan_Lee-original.pdf'
        with patch('vita_tree.pdf.atomic_write_bytes',side_effect=PermissionError(13,'private-canary')):
            with self.assertRaises(PermissionError):compiler.save(ident,branch['branch'])
        self.assertFalse(target.exists())
        compiler.save(ident,branch['branch'])
        self.assertEqual(target.read_bytes(),pdf.read_bytes())

    def test_pdf_names_follow_parsed_names_and_remain_portable(self):
        self.assertEqual(cv_filename(r'\name{Taylor SAMPLE}\begin{document}CV\end{document}'),'cv-Taylor_SAMPLE.pdf')
        self.assertEqual(cv_filename(SOURCE),'cv-Jordan_Lee.pdf')
        self.assertEqual(cv_filename(r'\name{../Taylor: SAMPLE?}'),'cv-Taylor_SAMPLE.pdf')
        self.assertEqual(cv_filename('No header'),'cv.pdf')


class HTTPDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd());self.root=init_repo(Path(self.temp.name))
        self.server=VitaTreeServer(('127.0.0.1',0),self.root,'main.tex',log_dir=self.root/'.git/logs-test')
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True);self.worker.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.worker.join();cleanup_repo(self.temp)

    def test_request_references_metrics_and_redacted_error_events(self):
        with patch.object(self.server.workspace,'review_job',side_effect=PermissionError(13,'private-canary','/private/token')):
            request=Request(self.base+'/api/job-reviewed',data=json.dumps({'id':'a'*32}).encode(),headers={'Content-Type':'application/json','X-Vita-Token':self.server.token})
            with self.assertRaises(HTTPError) as caught:urlopen(request)
        body=json.loads(caught.exception.read())
        self.assertEqual(caught.exception.code,500)
        self.assertIn('normal terminal',body['error'])
        self.assertEqual(caught.exception.headers['X-Request-ID'],body['requestId'])
        with urlopen(self.base+'/api/diagnostics') as response:diag=json.load(response)
        self.assertTrue(any(event.get('request_id')==body['requestId'] and event.get('error_type')=='PermissionError' for event in diag['events']))
        with urlopen(self.base+'/metrics') as response:metrics=response.read().decode()
        self.assertIn('vita_tree_http_requests_total',metrics)
        self.assertIn('vita_tree_active_runs',metrics)
        self.assertNotIn('private-canary',json.dumps(diag)+metrics)
        self.assertNotIn('/private/token',json.dumps(diag)+metrics)
        with self.assertRaises(HTTPError) as denied:urlopen(Request(self.base+'/api/diagnostics',headers={'Origin':'https://example.invalid'}))
        self.assertEqual(denied.exception.code,403)
