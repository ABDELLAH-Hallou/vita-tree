"""The separate synthetic provider check must not leave its process tree alive."""
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch

import test_provider_status as checks
import test_process_lifecycle as processes


class GenerationShutdownTests(unittest.TestCase):
    setUp=checks.CheckTests.setUp
    tearDown=checks.CheckTests.tearDown
    setup=checks.CheckTests.setup

    def test_capability_probe_descendants_do_not_outlive_shutdown(self):
        self.check_probe_descendants()

    def test_timed_out_capability_probe_stops_its_descendants(self):
        self.check_probe_descendants(timeout=True)

    def check_probe_descendants(self, timeout=False):
        from vita_tree.fallback import capabilities
        source=self.root/'synthetic-vita'
        helper=source/'vita/helpers/fallback.py'
        helper.parent.mkdir(parents=True)
        helper.write_text('# Synthetic capability presence marker\n')
        self.workspace.vita_source=source
        stop=self.root/'stop-probe'
        child=self.root/'probe_child.py'
        child.write_text('import time\nfrom pathlib import Path\n'
                         'deadline=time.monotonic()+60\n'
                         'while not Path('+repr(str(stop))+').exists() and time.monotonic()<deadline:time.sleep(.03)\n')
        marker=self.root/'probe-pids.json'
        script=self.root/'probe_fixture.py'
        contract={'schema_version':1,'version':'provider-fallback/1','max_backups':1,
                  'allowed_categories':['timeout'],'default_categories':['timeout']}
        script.write_text('import subprocess,sys,os,json,time\nfrom pathlib import Path\n'
            'child=subprocess.Popen([sys.executable,'+repr(str(child))+'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n'
            'Path('+repr(str(marker))+').write_text(json.dumps([os.getpid(),child.pid]))\n'
            'print('+repr(json.dumps(contract))+',flush=True)\n'+('time.sleep(60)\n' if timeout else ''))
        pids=[]
        try:
            with patch.object(self.workspace,'vita_command',return_value=[sys.executable,str(script)]):
                result=capabilities(self.workspace)
                if timeout:self.assertIsNone(result)
                else:self.assertEqual(result['version'],'provider-fallback/1')
            pids=json.loads(marker.read_text())
            self.workspace.close()
            for pid in pids:processes.ProcessLifecycleTests.assert_stopped(self,pid)
        finally:
            stop.touch()
            self.workspace.close()
            for pid in pids:processes.ProcessLifecycleTests.assert_stopped(self,pid)

    def test_generation_check_stops_on_workspace_shutdown(self):
        marker=self.root/'generation-pids.json'
        script=self.root/'check_fixture.py'
        script.write_text('import subprocess,sys,os,json,time\nfrom pathlib import Path\n'
            # Capability discovery must not publish the generation process marker.
            "if sys.argv[1:3]!=['providers','check']:raise SystemExit(2)\n"
            "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
            'Path('+repr(str(marker))+').write_text(json.dumps([os.getpid(),child.pid]))\n'
            'time.sleep(60)\n')
        errors=[]
        def run():
            try:self.workspace.check_generation('master','extract',self.setup(),True)
            except Exception as error:errors.append(error)
        worker=threading.Thread(target=run)
        try:
            with patch.object(self.workspace,'vita_command',return_value=[sys.executable,str(script)]):
                worker.start()
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    try:
                        pids=json.loads(marker.read_text())
                        break
                    except (FileNotFoundError,ValueError):time.sleep(.03)
                else:self.fail('Generation fixture did not start')
                self.workspace.close()
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive(),'Generation check outlived shutdown')
                for pid in pids:processes.ProcessLifecycleTests.assert_stopped(self,pid)
                self.assertTrue(errors,'A cancelled check must not claim verified generation')
                self.assertEqual(self.workspace._generation_checks,set())
        finally:
            self.workspace.close()
            if worker.ident:worker.join(timeout=5)
