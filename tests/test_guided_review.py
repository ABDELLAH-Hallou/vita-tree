"""Review policy is explicit, persistent and never retries provider failures."""
import json
import unittest

import test_jobs as support
from vita_tree.workspace import Workspace


class GuidedReviewTests(unittest.TestCase):
    setUp = support.JobTests.setUp
    tearDown = support.JobTests.tearDown
    branch = support.JobTests.branch
    start = support.JobTests.start
    release = support.JobTests.release
    wait = support.JobTests.wait
    finished = support.JobTests.finished
    pipeline_source = support.JobTests.pipeline_source
    pipeline_branch = support.JobTests.pipeline_branch

    def test_unknown_policy_cannot_start_or_approve_work(self):
        branch = self.branch('invalid-policy')
        for value in ('yes', True, None, ['automatic']):
            with self.assertRaisesRegex(ValueError, 'Choose review'):
                self.start(branch, review_policy=value)
        self.assertFalse(self.workspace.jobs)
        self.assertFalse(list(self.control.glob('*.calls')))

    def test_automatic_provider_failure_stops_and_explicit_retry_keeps_policy(self):
        self.pipeline_source()
        branch = self.pipeline_branch('provider-stop', provider_error='overloaded')
        self.release('provider-stop')
        (self.control/'provider-stop.analyze.fail').touch()
        run = self.start(branch, workflow={'steps': ['extract', 'analyze', 'adapt']}, review_policy='automatic')
        self.assertEqual(self.finished(run['id'])['status'], 'failed')
        self.wait(lambda: not self.workspace._ai_threads)
        self.assertEqual(len(self.workspace.jobs), 1)
        self.assertEqual((self.control/'provider-stop.analyze.calls').read_text().count('\n'), 1)
        snapshot = self.workspace.snapshot('provider-stop')
        preview = self.workspace.resume_ai(run['id'], snapshot['revision'], snapshot['jobRevision'], preview=True)
        retry = self.workspace.resume_ai(run['id'], snapshot['revision'], snapshot['jobRevision'], token=preview['token'])
        self.assertEqual(self.finished(retry['id'])['reviewPolicy'], 'automatic')
        self.wait(lambda: not self.workspace._ai_threads)
        self.assertEqual(len(self.workspace.jobs), 2)
        self.assertEqual(self.workspace.read('provider-stop', 'main.tex'), snapshot['content'])

    def test_default_policy_and_restart_history_do_not_trust_arbitrary_text(self):
        branch = self.branch('default-policy', 'provider-fail')
        self.release('default-policy')
        run = self.start(branch)
        self.assertEqual(self.finished(run['id'])['reviewPolicy'], 'manual')
        self.wait(lambda: not self.workspace._ai_threads)
        path = self.workspace.root/'job-history'/(run['id']+'.json')
        record = json.loads(path.read_text())
        record['reviewPolicy'] = 'private-history-canary'
        path.write_text(json.dumps(record), encoding='utf-8')
        self.workspace.close()
        self.workspace = Workspace(self.root)
        public = self.workspace.get_job(run['id'])
        self.assertEqual(public['reviewPolicy'], 'manual')
        self.assertNotIn('private-history-canary', json.dumps(public))
