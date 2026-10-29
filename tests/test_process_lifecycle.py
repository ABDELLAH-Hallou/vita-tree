"""Process ownership tests use only short-lived local synthetic programs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from support import cleanup_repo


class ProcessLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = Path(self.temporary.name)

    def tearDown(self):
        cleanup_repo(self.temporary)

    def program(self):
        script = self.root/'fixture.py'
        script.write_text('''import subprocess,sys,time,os,json
from pathlib import Path
p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
Path('pids.json').write_text(json.dumps([os.getpid(),p.pid]))
time.sleep(60)
''', encoding='utf-8')
        return [sys.executable, str(script)]

    def wait_file(self):
        deadline = time.monotonic()+10
        while time.monotonic()<deadline:
            try:
                return json.loads((self.root/'pids.json').read_text())
            except (FileNotFoundError, ValueError):
                time.sleep(.02)
        self.fail('Synthetic process did not start')

    def test_close_kills_owned_provider_and_grandchild(self):
        from vita_tree.processes import ProcessRegistry
        registry = ProcessRegistry()
        errors = []
        def run():
            try:
                registry.run(self.program(), cwd=self.root, timeout=30)
            except Exception as error:
                errors.append(error)
        worker = threading.Thread(target=run)
        worker.start()
        self.wait_file()
        registry.close()
        worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(registry.active(), [])
        # A child would otherwise wake up and write this after its parent exits.
        # Verify process liveness with OS handles/signals, without killing foreign PIDs.
        for pid in json.loads((self.root/'pids.json').read_text()):
            self.assert_stopped(pid)
        self.assertEqual(errors, [])
        with self.assertRaises(RuntimeError): registry.run([sys.executable,'-c','pass'],timeout=1)

    def assert_stopped(self, pid):
        # Group termination is asynchronous; waiting for the trampoline does
        # not mean every descendant has already transitioned to its dead/zombie
        # state. Keep a bounded liveness check instead of a one-instruction race.
        deadline=time.monotonic()+5
        while ProcessLifecycleTests.is_running(self,pid):
            if time.monotonic()>=deadline:self.fail('Owned process is still running')
            time.sleep(.02)

    def is_running(self, pid):
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.OpenProcess.restype=wintypes.HANDLE
            handle=kernel.OpenProcess(0x1000,False,pid)
            if not handle:
                if ctypes.get_last_error() in (87,1168):return False
                self.fail('Could not inspect the owned process lifetime')
            code=wintypes.DWORD()
            try:
                self.assertTrue(kernel.GetExitCodeProcess(wintypes.HANDLE(handle),ctypes.byref(code)))
                return code.value==259
            finally:kernel.CloseHandle(wintypes.HANDLE(handle))
        else:
            # A reparented zombie is no longer executing; the host init reaps it.
            stat=Path('/proc')/str(pid)/'stat'
            try:
                if stat.exists():
                    fields=stat.read_text().split(') ',1)
                    if len(fields)==2 and fields[1].startswith(('Z','X')):return False
            except (FileNotFoundError,ProcessLookupError):return False
            try:os.kill(pid,0)
            except ProcessLookupError:return False
            return True

    def test_timeout_kills_tree_and_preserves_typed_timeout(self):
        from vita_tree.processes import ProcessRegistry
        registry=ProcessRegistry()
        try:
            with self.assertRaises(subprocess.TimeoutExpired):
                registry.run(self.program(),cwd=self.root,timeout=5)
            for pid in self.wait_file():self.assert_stopped(pid)
            self.assertEqual(registry.active(),[])
        finally:registry.close()

    def test_normal_completion_and_nonzero_exit_preserve_return_codes(self):
        from vita_tree.processes import ProcessRegistry
        registry=ProcessRegistry()
        try:
            for code in (0,7):
                result=registry.run([sys.executable,'-c',f'raise SystemExit({code})'],timeout=5)
                self.assertEqual(result.returncode,code)
                self.assertEqual(registry.active(),[])
        finally:registry.close()

    def test_normal_completion_does_not_leave_a_live_grandchild(self):
        from vita_tree.processes import ProcessRegistry
        script=self.root/'normal_child.py'
        script.write_text("import subprocess,sys,os,json\nfrom pathlib import Path\n"
            "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
            "Path('pids.json').write_text(json.dumps([os.getpid(),child.pid]))\n")
        registry=ProcessRegistry()
        try:
            result=registry.run([sys.executable,str(script)],cwd=self.root,timeout=10)
            self.assertEqual(result.returncode,0)
            pids=self.wait_file()
            deadline=time.monotonic()+5
            while True:
                try:
                    for pid in pids:self.assert_stopped(pid)
                    break
                except AssertionError:
                    if time.monotonic()>deadline:raise
                    time.sleep(.03)
        finally:registry.close()

    def test_abrupt_owner_exit_stops_descendants(self):
        # Kill the actual owner, not Windows' venv interpreter redirector.
        owner=self.root/'owner.py'
        owner.write_text('import sys\nsys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[1]/'src'))+')\n'
            'from vita_tree.processes import ProcessRegistry\n'
            'ProcessRegistry().run('+repr(self.program())+',timeout=30)\n')
        process=subprocess.Popen([getattr(sys,'_base_executable',sys.executable),str(owner)],cwd=self.root,
                                 stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            pids=self.wait_file()
            process.kill();process.wait(timeout=5)
            deadline=time.monotonic()+5
            while True:
                try:
                    for pid in pids:self.assert_stopped(pid)
                    break
                except AssertionError:
                    if time.monotonic()>deadline:raise
                    time.sleep(.03)
        finally:
            if process.poll() is None:process.kill();process.wait(timeout=5)

    def test_owned_compiler_output_uses_a_file_without_pipe_deadlock(self):
        from vita_tree.processes import ProcessRegistry,run_owned
        registry=ProcessRegistry()
        try:
            with tempfile.TemporaryFile() as output,registry.scope():
                result=run_owned([sys.executable,'-c',"import sys;sys.stdout.write('x'*2000000)"],
                                 stdout=output,stderr=subprocess.STDOUT,timeout=10)
                self.assertEqual(result.returncode,0)
                output.seek(0,2)
                self.assertEqual(output.tell(),2000000)
        finally:registry.close()

    def test_unsupported_pipes_are_rejected_before_starting_a_process(self):
        from vita_tree.processes import ProcessRegistry
        registry=ProcessRegistry()
        for options in ({'stdin':subprocess.PIPE},{'stdout':subprocess.PIPE},{'stderr':subprocess.PIPE}):
            with self.assertRaises(ValueError):
                registry.run([sys.executable,'-c','pass'],timeout=1,**options)
        self.assertEqual(registry.active(),[])
