"""The evidence must retain failures and use reproducible latency summaries."""
import json
import unittest
from unittest.mock import patch,mock_open
from contextlib import redirect_stdout
import io

from load_support import distribution, profile, LoadServer,budget_gate


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

    def test_only_measured_orchestration_can_be_advisory(self):
        values={'orchestrationP95Ms':{'actual':16000,'passed':False}}
        self.assertFalse(budget_gate(values,enforce=True))
        self.assertTrue(budget_gate(values,enforce=True,advisory_orchestration=True))
        for key in ('pollP95Ms','pdfP95Ms','shutdownMs','serverPeakRssMiB','orphans','unexpectedFailures'):
            self.assertFalse(budget_gate({**values,key:{'actual':1,'passed':False}},True,True),key)
        for missing in (None,float('nan'),float('inf'),-1):
            self.assertFalse(budget_gate({'orchestrationP95Ms':{'actual':missing,'passed':False}},True,True))

    def test_shared_host_summary_does_not_claim_a_performance_pass(self):
        from run_load_profile import ci_summary
        report=dict(profile='sustained',replica=1,declared={'pdfMode':'simulated'},passed=True,performancePassed=False,
                    budgetPolicy={'orchestrationAdvisory':True},
                    budgetResults={'orchestrationP95Ms':{'actual':16000,'maximum':15000,'passed':False}})
        with patch.dict('os.environ',{'GITHUB_STEP_SUMMARY':'synthetic-summary'}),patch('builtins.open',mock_open()) as output,redirect_stdout(io.StringIO()) as console:
            ci_summary(report)
        body=output().write.call_args.args[0]
        self.assertIn('All measured performance targets: **MISS**',body)
        self.assertIn('MISS (advisory)',body)
        self.assertIn('warning',console.getvalue())
