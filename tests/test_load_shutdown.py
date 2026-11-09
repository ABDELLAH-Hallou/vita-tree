"""Workflow integration regression for provider ownership during shutdown."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import test_jobs as job_support
import test_process_lifecycle as process_support


class ShutdownLoadTests(unittest.TestCase):
    setUp=job_support.JobTests.setUp
    tearDown=job_support.JobTests.tearDown
    pipeline_source=job_support.JobTests.pipeline_source
    pipeline_branch=job_support.JobTests.pipeline_branch
    branch=job_support.JobTests.branch
    start=job_support.JobTests.start
    wait=job_support.JobTests.wait
    release=job_support.JobTests.release

    def test_shutdown_stops_provider_tree_without_waiting_for_fixture_release(self):
        self.pipeline_source()
        branch=self.pipeline_branch('shutdown-owned',load={'gate':'shutdown','spawnChild':True})
        command=[sys.executable,str(Path(__file__).with_name('load_provider.py').resolve())]
        with patch.object(self.workspace,'vita_command',return_value=command):
            run=self.start(branch,workflow={'steps':['analyze','adapt']})
            self.wait(lambda:bool(list(self.control.glob('*.started.json'))))
            evidence=json.loads(next(self.control.glob('*.started.json')).read_text())
            self.workspace.close()
            for worker in list(self.workspace._ai_threads):worker.join(timeout=5)
            # Assert before releasing the old fixture: shutdown must own cleanup.
            live=any(t.is_alive() for t in self.workspace._ai_threads)
            try:
                self.assertFalse(live,'Shutdown left its provider process running')
                for pid in (evidence['pid'],evidence['childPid']):
                    process_support.ProcessLifecycleTests.assert_stopped(self,pid)
                self.assertEqual(self.workspace.jobs[run['id']]['status'],'interrupted')
                self.assertEqual(self.workspace.read(branch['branch'],'main.tex'),self.workspace.snapshot('master')['content'])
            finally:
                (self.control/'shutdown.release').touch()
                self.release('shutdown-owned')
                for worker in list(self.workspace._ai_threads):worker.join(timeout=15)
