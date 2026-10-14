import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from vita_tree.workspace import Workspace, ConflictError, digest
from support import SOURCE, cleanup_repo, init_repo, git


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.temp.name))
        self.control = self.root / '.git/ai-control'
        self.control.mkdir()
        self.workspace = Workspace(self.root)
        self.labels = []
        self.environment = patch.dict(os.environ, {'VITA_TEST_CONTROL': str(self.control), 'VITA_TEST_SECRET': 'private-fixture-value'})
        self.environment.start()
        self.command = patch.object(self.workspace, 'vita_command', return_value=[sys.executable, str(Path(__file__).with_name('fake_ai_process.py'))])
        self.command.start()

    def tearDown(self):
        for label in self.labels:
            self.release(label)
        self.workspace.close()
        for thread in list(self.workspace._ai_threads):
            thread.join(timeout=15)
            self.assertFalse(thread.is_alive())
        self.command.stop()
        self.environment.stop()
        cleanup_repo(self.temp)

    def branch(self, label, mode='success'):
        self.labels.append(label)
        return self.workspace.create('master', label, json.dumps({'label': label, 'mode': mode}), digest(SOURCE))

    def start(self, branch, **kwargs):
        return self.workspace.start_ai(branch['branch'], branch['revision'], branch['jobRevision'], **kwargs)

    def release(self, label):
        (self.control / (label + '.release')).touch()

    def wait(self, predicate):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.04)
        self.fail('Timed out waiting for controlled AI process')

    def finished(self, ident):
        self.wait(lambda: self.workspace.get_job(ident)['status'] not in self.workspace.ACTIVE_STATUSES)
        return self.workspace.get_job(ident)

    def test_all_processes_start_without_queue_and_branches_are_isolated(self):
        branches = [self.branch(label) for label in ('first', 'second', 'third')]
        run_config = Path(branches[2]['worktree']) / '.vita/config.json'
        run_config.parent.mkdir(exist_ok=True)
        run_config.write_text('{"marker":"captured-at-start"}')
        first, second, third = [self.start(branch, language=language) for branch, language in zip(branches, ('en', 'fr', 'de'))]
        run_config.write_text('{"marker":"changed-after-start"}')
        self.wait(lambda: all((self.control / (label + '.started')).exists() for label in ('first', 'second', 'third')))
        self.assertEqual(self.workspace.get_job(third['id'])['status'], 'running')
        self.assertFalse(any((self.control / (label + '.finished')).exists() for label in ('first', 'second', 'third')))
        with self.assertRaises(ConflictError):
            self.start(branches[0])
        for branch in branches:
            self.assertEqual(self.workspace.release_worktree(branch['branch'])['reason'], 'active')
            with self.assertRaises(ConflictError):
                self.workspace.save(branch['branch'], 'main.tex', branch['revision'], 'overwrite')
            with self.assertRaises(ConflictError):
                self.workspace.commit_preview(branch['branch'])
        other = self.branch('independent')
        self.workspace.save(other['branch'], 'main.tex', other['revision'], SOURCE + '\n% independent edit')
        self.release('second')
        self.assertEqual(self.finished(second['id'])['status'], 'succeeded')
        self.wait(lambda: (self.control / 'third.started').exists())
        self.assertEqual(self.workspace.get_job(first['id'])['status'], 'running')
        self.release('third'); self.release('first')
        for record, language in zip((first, second, third), ('en', 'fr', 'de')):
            result = self.finished(record['id'])
            self.assertEqual(result['status'], 'succeeded', result)
            self.assertEqual(result['language'], language)
            snapshot = self.workspace.snapshot(record['branch'])
            self.assertIn(record['branch'] + ' systems', snapshot['content'])
            self.assertEqual(snapshot['original'], SOURCE)
            self.assertEqual(snapshot['artifacts']['analyze']['content'], '# ' + record['branch'] + ' analyze')
            retained = self.workspace.job_result(record['id'])['files']
            self.assertEqual(retained['original/main.tex'], SOURCE)
            self.assertIn(record['branch'], retained['main.tex'])
        self.assertLess(float((self.control/'first.started').read_text()), float((self.control/'second.finished').read_text()))
        self.assertLess(float((self.control/'second.started').read_text()), float((self.control/'first.finished').read_text()))
        retained_config = self.workspace.root / 'runs' / third['id'] / '.vita/config.json'
        self.assertEqual(json.loads(retained_config.read_text())['marker'], 'captured-at-start')
        public = json.dumps(self.workspace.list_jobs())
        for secret in ('private-fixture-value', 'VITA_TEST_SECRET', SOURCE, 'source', 'env', 'runPath'):
            self.assertNotIn(secret, public)

    def test_failure_validation_and_external_conflicts_preserve_files(self):
        for label, mode in (('provider', 'provider-fail'), ('validation', 'invalid'), ('conflict', 'success')):
            with self.subTest(mode=mode):
                branch = self.branch(label, mode); record = self.start(branch)
                self.wait(lambda: (self.control / (label + '.started')).exists())
                if label == 'conflict':
                    (Path(branch['worktree']) / 'main.tex').write_text(SOURCE + '\n% external')
                self.release(label)
                result = self.finished(record['id'])
                self.assertEqual(result['status'], 'failed', result)
                expected = SOURCE + ('\n% external' if label == 'conflict' else '')
                self.assertEqual(self.workspace.read(label, 'main.tex'), expected)
                self.assertNotIn('private-fixture-value', json.dumps(result))
                self.assertIsNotNone(result['finishedAt'])

    def test_restart_keeps_history_and_review_flags_and_interrupts_active_jobs(self):
        done = self.start(self.branch('done')); self.release('done'); self.finished(done['id'])
        self.workspace.review_job(done['id'])
        running = self.start(self.branch('running'))
        another = self.start(self.branch('another'))
        self.assertEqual(another['status'], 'running')
        self.workspace.close()
        self.release('running')
        self.release('another')
        for thread in list(self.workspace._ai_threads):
            thread.join(timeout=15)
        reopened = Workspace(self.root)
        self.assertTrue(reopened.get_job(done['id'])['reviewed'])
        for ident in (running['id'], another['id']):
            self.assertEqual(reopened.get_job(ident)['status'], 'interrupted')
            self.assertFalse(reopened.get_job(ident)['reviewed'])
        reopened.review_job(running['id'])
        self.assertFalse(reopened.get_job(another['id'])['reviewed'])
        self.assertEqual(reopened.read('running', 'main.tex'), SOURCE)
        self.assertEqual(reopened.job_result(another['id'])['files']['original/main.tex'], SOURCE)
        reopened.close()

    def test_unclean_restart_marks_persisted_active_job_interrupted(self):
        record = {'id': 'a'*32, 'branch': 'master', 'status': 'running', 'step': 'adapt', 'createdAt': time.time(), 'reviewed': False}
        self.workspace._persist_job(record)
        recovered = Workspace(self.root)
        self.assertEqual(recovered.get_job(record['id'])['status'], 'interrupted')
        self.assertIsNotNone(recovered.get_job(record['id'])['finishedAt'])
        recovered.close()

    def test_release_clean_owned_worktree_allows_checkout_and_recreation(self):
        branch = self.branch('releasable')
        worktree = Path(branch['worktree'])
        git(worktree, 'add', 'job.md', 'main.tex'); git(worktree, 'commit', '-m', 'Job fixture')
        before = git(worktree, 'rev-parse', 'HEAD')
        release = self.workspace.release_worktree('releasable')
        self.assertTrue(release['released'], release)
        self.assertFalse(worktree.exists())
        git(self.root, 'checkout', 'releasable')
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.workspace.release_worktree('releasable')['reason'], 'external')
        git(self.root, 'checkout', 'master')
        snapshot = self.workspace.snapshot('releasable')
        self.workspace.save('releasable', 'main.tex', snapshot['revision'], SOURCE + '\n% reopened')
        self.assertTrue(worktree.is_dir())
        self.assertIn('reopened', self.workspace.read('releasable', 'main.tex'))

    def test_leave_during_run_releases_worktree_only_after_it_finishes_clean(self):
        branch = self.branch('leave-running', 'provider-fail')
        worktree = Path(branch['worktree'])
        git(worktree, 'add', 'main.tex', 'job.md'); git(worktree, 'commit', '-m', 'Saved input')
        record = self.start(branch)
        self.wait(lambda: (self.control / 'leave-running.started').exists())
        self.assertEqual(self.workspace.release_worktree('leave-running')['reason'], 'active')
        self.assertTrue(worktree.exists())
        self.release('leave-running')
        self.assertEqual(self.finished(record['id'])['status'], 'failed')
        self.wait(lambda: not worktree.exists())
        git(self.root, 'checkout', 'leave-running')

    def test_pdf_export_keeps_worktree_until_preview_finishes(self):
        from vita_tree.pdf import PDFCompiler
        branch = self.branch('preview')
        worktree = Path(branch['worktree'])
        git(worktree, 'add', 'main.tex', 'job.md'); git(worktree, 'commit', '-m', 'Saved input')
        compiler = PDFCompiler(self.workspace)
        with patch.object(compiler, '_compile', side_effect=lambda *args: self.workspace.release_worktree('preview')):
            self.assertEqual(compiler.compile('preview', 'current', 'auto')['reason'], 'active')
        self.assertFalse(worktree.exists())
        self.assertNotIn('preview', self.workspace._previewing)

    def test_release_preserves_dirty_ignored_locked_and_external_worktrees(self):
        branch = self.branch('keep')
        worktree = Path(branch['worktree'])
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'dirty')
        git(worktree, 'add', 'job.md'); git(worktree, 'commit', '-m', 'Job fixture')
        (worktree / 'main.tex').write_text(SOURCE + '\n% local')
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'dirty')
        (worktree / 'main.tex').write_text(SOURCE)
        (worktree / '.gitignore').write_text('local-secret\n')
        git(worktree, 'add', '.gitignore'); git(worktree, 'commit', '-m', 'Ignore fixture')
        (worktree / 'local-secret').write_text('preserve-me')
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'dirty')
        self.assertEqual((worktree / 'local-secret').read_text(), 'preserve-me')
        (worktree / 'local-secret').unlink()
        git(self.root, 'worktree', 'lock', str(worktree))
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'locked')
        git(self.root, 'worktree', 'unlock', str(worktree))
        external = self.root / '.git/external-worktree'
        git(self.root, 'worktree', 'add', '-b', 'external', str(external))
        self.assertEqual(self.workspace.release_worktree('external')['reason'], 'external')
        self.assertTrue(external.exists())
