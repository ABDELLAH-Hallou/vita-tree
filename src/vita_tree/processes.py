"""Own long-running workflow/TeX process trees without an admission queue."""
from contextlib import contextmanager
from contextvars import ContextVar
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

_current = ContextVar('vita_tree_process_owner', default=None)


class _WindowsJob:
    """Kernel-owned descendant lifetime, including abrupt server termination."""
    def __init__(self):
        import ctypes as c
        from ctypes import wintypes as w
        self.c, self.w = c, w
        class Limits(c.Structure):
            _fields_=[('processTime',c.c_int64),('jobTime',c.c_int64),('flags',w.DWORD),
                      ('minWorkingSet',c.c_size_t),('maxWorkingSet',c.c_size_t),('activeProcesses',w.DWORD),
                      ('affinity',c.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
        class IO(c.Structure):
            _fields_=[(name,c.c_uint64) for name in ('readOps','writeOps','otherOps','readBytes','writeBytes','otherBytes')]
        class Extended(c.Structure):
            _fields_=[('basic',Limits),('io',IO),('processMemory',c.c_size_t),('jobMemory',c.c_size_t),
                      ('peakProcessMemory',c.c_size_t),('peakJobMemory',c.c_size_t)]
        self.kernel=c.WinDLL('kernel32',use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes=[c.c_void_p,w.LPCWSTR]
        self.kernel.CreateJobObjectW.restype=w.HANDLE
        self.kernel.SetInformationJobObject.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD]
        self.kernel.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE]
        self.kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]
        self.kernel.OpenProcess.restype=w.HANDLE
        self.kernel.CloseHandle.argtypes=[w.HANDLE]
        self.handle=self.kernel.CreateJobObjectW(None,None)
        if not self.handle:raise c.WinError(c.get_last_error())
        info=Extended();info.basic.flags=0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle,9,c.byref(info),c.sizeof(info)):
            error=c.WinError(c.get_last_error());self.close();raise error

    def assign(self, process):
        handle=self.kernel.OpenProcess(0x0100|0x0001,False,process.pid)
        if not handle:raise self.c.WinError(self.c.get_last_error())
        try:
            if not self.kernel.AssignProcessToJobObject(self.handle,handle):
                raise self.c.WinError(self.c.get_last_error())
        finally:self.kernel.CloseHandle(handle)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle=None


class ProcessRegistry:
    def __init__(self):
        self.lock=threading.RLock()
        self.children={}
        self.closed=False

    @contextmanager
    def scope(self):
        token=_current.set(self)
        try:yield
        finally:_current.reset(token)

    def active(self):
        with self.lock:return [p.pid for p in self.children if p.poll() is None]

    def _stop(self, process, job):
        if job is not None:
            job.close()
        else:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass

    def run(self, args, *, timeout, cwd=None, env=None, stdin=None, stdout=None, stderr=None):
        # The helper cannot launch the actual command before assignment to its
        # Windows job. This closes the usual Popen/AssignProcess spawn race.
        with self.lock:
            if self.closed:raise RuntimeError('Vita Tree is stopping; no new process was started.')
            job=_WindowsJob() if os.name=='nt' else None
            process=None
            try:
                # Windows venv python.exe is a redirector that can create the
                # real interpreter before job assignment. The stdlib-only
                # handshake helper uses the base interpreter directly instead.
                helper_python=getattr(sys,'_base_executable',sys.executable) if os.name=='nt' else sys.executable
                process=subprocess.Popen([helper_python,'-I',str(Path(__file__).with_name('_process_child.py')),*args],
                    cwd=cwd,env=env,stdin=subprocess.PIPE,
                    stdout=stdout if stdout is not None else subprocess.DEVNULL,
                    stderr=stderr if stderr is not None else subprocess.DEVNULL,
                    **({'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {'start_new_session':True}))
                if job is not None:job.assign(process)
                self.children[process]=job
                process.stdin.write(b'1');process.stdin.flush()
            except BaseException:
                if job is not None:job.close()
                if process is not None:
                    process.kill();process.wait();process.stdin.close()
                    self.children.pop(process,None)
                raise
        try:
            return subprocess.CompletedProcess(args,process.wait(timeout=timeout))
        except subprocess.TimeoutExpired:
            raise subprocess.TimeoutExpired(args,timeout) from None
        finally:
            with self.lock:
                self._stop(process,job)
                process.stdin.close()
                self.children.pop(process,None)
            process.wait(timeout=5)

    def close(self):
        with self.lock:
            self.closed=True
            for process,job in list(self.children.items()):self._stop(process,job)


def run_owned(args, **options):
    owner=_current.get()
    return owner.run(args,**options) if owner is not None else subprocess.run(args,**options)
