"""Internal command trampoline; no provider work before the ownership handshake."""
import os
import signal
import subprocess
import sys
import threading

if os.read(0,1)!=b'1':
    raise SystemExit(1)

if os.name!='nt':
    def parent_gone():
        # The parent keeps this pipe open. EOF also detects an abrupt server
        # exit; provider commands never inherit the read end as their stdin.
        if not os.read(0,1):os.killpg(os.getpgrp(),signal.SIGKILL)
    threading.Thread(target=parent_gone,daemon=True).start()

raise SystemExit(subprocess.call(sys.argv[1:],stdin=subprocess.DEVNULL))
