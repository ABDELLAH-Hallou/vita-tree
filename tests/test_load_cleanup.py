"""Deterministic ordering of automatic and explicit load-fixture release."""
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_jobs as job_support
from support import git
from load_support import clean_worktree_release


class LoadCleanupTests(unittest.TestCase):
    setUp = job_support.JobTests.setUp
    tearDown = job_support.JobTests.tearDown
    branch = job_support.JobTests.branch
    start = job_support.JobTests.start
    wait = job_support.JobTests.wait
    release = job_support.JobTests.release

    def test_deferred_release_can_win_the_explicit_cleanup_race(self):
        branch = self.branch('deferred-release')
        location = Path(branch['worktree'])
        terminal = threading.Event()
        finish = threading.Event()
        original = self.workspace.inspector.finish

        def held_finish(record):
            original(record)
            terminal.set()
            if not finish.wait(20):
                raise AssertionError('Cleanup barrier was not released')

        with patch.object(self.workspace.inspector, 'finish', side_effect=held_finish):
            try:
                run = self.start(branch)
                self.wait(lambda: (self.control/'deferred-release.started').exists())
                self.assertEqual(self.workspace.release_worktree(branch['branch'])['reason'], 'active')
                self.release('deferred-release')
                self.assertTrue(terminal.wait(15))
                self.assertEqual(self.workspace.get_job(run['id'])['status'], 'succeeded')
                git(location, 'add', 'main.tex', 'job.md')
                if (location/'.vita/results').exists():
                    git(location, 'add', '-f', '.vita/results')
                git(location, 'commit', '-m', 'Synthetic load result')
                self.assertEqual(git(location, 'status', '--porcelain', '--ignored'), '')
                finish.set()
                self.wait(lambda: not location.exists())
                server = SimpleNamespace(root=self.root, api=lambda route, data:
                                         self.workspace.release_worktree(data['branch']))
                evidence = clean_worktree_release(server, branch['branch'], location)
                self.assertEqual(evidence, dict(passed=True, reason='absent', folderAbsent=True, branchDetached=True))
                # The branch is also available to ordinary Git, independently
                # of both the API response and the worktree-list assertion.
                git(self.root, 'checkout', branch['branch'])
                git(self.root, 'checkout', 'master')
            finally:
                finish.set()

    def test_explicit_release_checks_folder_and_git_registration(self):
        branch = self.branch('explicit-release')
        location = Path(branch['worktree'])
        git(location, 'add', 'job.md')
        git(location, 'commit', '-m', 'Synthetic clean branch')
        server = SimpleNamespace(root=self.root, api=lambda route, data:
                                 self.workspace.release_worktree(data['branch']))
        self.assertEqual(clean_worktree_release(server, branch['branch'], location),
                         dict(passed=True, reason='clean', folderAbsent=True, branchDetached=True))

    def test_absent_response_cannot_hide_real_leaks_or_other_release_failures(self):
        branch = self.branch('retained-release')
        location = Path(branch['worktree'])
        server = SimpleNamespace(root=self.root, api=lambda route, data: dict(released=False, reason='absent'))
        self.assertEqual(clean_worktree_release(server, branch['branch'], location),
                         dict(passed=False, reason='absent', folderAbsent=False, branchDetached=False))
        # Even a claimed successful removal cannot hide stale Git registration.
        missing = self.root/'missing-fixture-folder'
        server.api = lambda route, data: dict(released=True, reason='clean')
        self.assertFalse(clean_worktree_release(server, branch['branch'], missing)['passed'])
        # Conversely, an unregistered branch does not hide a surviving folder.
        self.assertFalse(clean_worktree_release(server, 'unregistered-fixture', location)['passed'])
        for reason in ('active', 'dirty', 'locked', 'external', 'unknown'):
            server.api = lambda route, data, reason=reason: dict(released=False, reason=reason)
            self.assertFalse(clean_worktree_release(server, 'unregistered-fixture', missing)['passed'], reason)
