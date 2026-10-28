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

    def test_generation_check_stops_on_workspace_shutdown(self):
        marker=self.root/'generation-pids.json'
        script=self.root/'check_fixture.py'
        script.write_text('import subprocess,sys,os,json,time\nfrom pathlib import Path\n'
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
