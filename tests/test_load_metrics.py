"""The evidence must retain failures and use reproducible latency summaries."""
import json
import unittest
from unittest.mock import patch

from load_support import distribution, profile, LoadServer


class LoadMetricsTests(unittest.TestCase):
    def test_nearest_rank_percentiles_and_empty_samples(self):
        self.assertEqual(distribution(range(1,101)),dict(count=100,p50=50,p95=95,maximum=100))
        self.assertEqual(distribution([]),dict(count=0,p50=None,p95=None,maximum=None))
        self.assertEqual(distribution([2000,1,2])['p95'],2000)

    def test_profiles_declare_budgets_before_running(self):
        for name in ('ci','sustained'):
            config=profile(name)
            self.assertGreaterEqual(config['concurrency'],3)
            self.assertGreaterEqual(config['waves'],2)
            for metric in ('submitP95Ms','pollP95Ms','orchestrationP95Ms','pdfP95Ms',
                           'uiInteractionP95Ms','serverPeakRssMiB','peakDescendants'):
                self.assertGreater(config['budgets'][metric],0)
            for metric in ('orphans','unexpectedFailures','cleanWorktreeLeaks'):
                self.assertEqual(config['budgets'][metric],0)

    def test_timed_out_requests_are_not_dropped(self):
        from pathlib import Path
        server=LoadServer(Path.cwd())
        server.base='http://127.0.0.1:1'
        with patch('load_support.urlopen',side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):server.api('/api/jobs')
        self.assertEqual(len(server.samples),1)
        self.assertEqual(server.samples[0]['status'],0)
        self.assertNotIn('body',server.samples[0])
        self.assertNotIn('token',json.dumps(server.samples))
