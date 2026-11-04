"""Authenticated, bounded snapshot transport to the host's native Codex CLI.

No shell commands, executable paths or host filesystem paths come from clients.
The native CLI retains provider/model/schema behavior and host authentication.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .processes import ProcessRegistry


class HostCapacityError(ValueError):
    pass


def validate_files(files):
    if not isinstance(files, dict) or len(files) > 256: raise ValueError('Snapshot file limit')
    size = 0
    for name, content in files.items():
        if not isinstance(name, str) or not isinstance(content, str): raise ValueError('Invalid snapshot')
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name
                or name != path.as_posix() or any(p.startswith('.') for p in path.parts if p != '.vita')):
            raise ValueError('Invalid snapshot path')
        allowed = (not name.startswith('.vita/') and (path.suffix in {'.tex','.sty','.cls','.bib'} or name == 'job.md'))
        allowed |= bool(re.fullmatch(r'\.vita/(?:skills/[a-z]+/[^/]+\.md|results/(?:job\.(?:json|toon)|analy(?:sis|ze)\.(?:md|json)|(?:adapt|review|cover|delta)\.(?:md|json)))',name))
        if not allowed: raise ValueError('Unsupported snapshot file')
        size += len(content.encode('utf-8'))
        if len(content.encode('utf-8')) > 2_000_000 or size > 8_000_000: raise ValueError('Snapshot byte limit')
    return files


def validate_request(data):
    if not isinstance(data,dict) or set(data) != {'files','prompt','model','reasoning','schema'}: raise ValueError('Invalid request')
    validate_files(data['files'])
    if not isinstance(data['prompt'],str) or len(data['prompt'].encode()) > 8_000_000: raise ValueError('Prompt limit')
    if not isinstance(data['model'],str) or (data['model'] and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@+-]{0,159}',data['model'])): raise ValueError('Invalid model')
    if data['reasoning'] not in ('','none','minimal','low','medium','high','xhigh','max','ultra'): raise ValueError('Invalid reasoning')
    if data['schema'] is not None and (not isinstance(data['schema'],dict) or len(json.dumps(data['schema'])) > 1_000_000): raise ValueError('Invalid schema')
    return data


def worker(path):
    """Runs inside the owning process tree; communicates only through files."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    folder = Path(path).parent
    command = [data['executable'],'exec','--sandbox','read-only','--output-last-message',str(folder/'output.txt')]
    if data['model']: command += ['--model',data['model']]
    if data['reasoning']: command += ['-c','model_reasoning_effort='+json.dumps(data['reasoning'])]
    if data['schema'] is not None:
        schema = folder/'schema.json'; schema.write_text(json.dumps(data['schema']),encoding='utf-8')
        command += ['--output-schema',str(schema)]
    with (folder/'stderr.txt').open('w+b') as diagnostics:
        result = subprocess.run([*command,'-'],input=data['prompt'].encode('utf-8'),
                                cwd=folder/'project',stdout=subprocess.DEVNULL,stderr=diagnostics,
                                env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')})
        diagnostics.seek(max(0, diagnostics.tell()-64000))
        tail = diagnostics.read(64000)
    # Forward only stable error markers used by Vita CV; never raw diagnostics.
    status = re.search(rb'\b(?:HTTP(?: status)?|status(?: code)?)[: =]+(401|402|403|408|429|500|502|503|504|529)\b',tail,re.I)
    error = 'HTTP '+status[1].decode() if status else 'Codex host execution failed; check host login and model access.'
    if re.search(rb'model_not_found|invalid_model', tail, re.I): error = 'model_not_found'
    if re.search(rb"(?:unexpected|unknown) argument ['\"]--output-schema['\"]", tail):
        error = "unknown argument '--output-schema'"
    output = folder/'output.txt'
    content = output.read_text(encoding='utf-8') if output.is_file() and output.stat().st_size <= 8_000_000 else ''
    (folder/'result.json').write_text(json.dumps({'status':'succeeded' if result.returncode == 0 and content else 'failed',
        'output':content if result.returncode == 0 else '', 'error':error}),encoding='utf-8')


class HostServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, token, executable, *, lease_seconds=15):
        self.token, self.executable = token, executable
        self.jobs, self.lock = {}, threading.RLock()
        self.retired = []
        self.lease_seconds = lease_seconds
        super().__init__(address, HostHandler)
        self.sweeper = threading.Thread(target=self.sweep,daemon=True)
        self.stopped = threading.Event(); self.sweeper.start()

    def sweep(self):
        while not self.stopped.wait(1):
            with self.lock:
                expired = [ident for ident,job in self.jobs.items() if time.monotonic()-job['seen'] > self.lease_seconds]
            for ident in expired: self.remove(ident)
            self.reap()

    def reap(self):
        with self.lock:
            for job in self.retired[:]:
                if job['thread'].is_alive(): continue
                try: job['temporary'].cleanup()
                except OSError: continue  # Windows may still hold descendant handles briefly.
                self.retired.remove(job)

    def remove(self, ident):
        with self.lock: job = self.jobs.pop(ident,None)
        if job:
            job['owner'].close()
            job['thread'].join(timeout=5)
            with self.lock: self.retired.append(job)
            self.reap()

    def launch(self, data):
        with self.lock:
            if self.stopped.is_set(): raise ValueError('Host is stopping')
            if len(self.jobs) >= 32: raise HostCapacityError('Host is at capacity; no request was queued')
            ident = secrets.token_hex(16)
            temporary = tempfile.TemporaryDirectory(prefix='vita-codex-host-')
            folder = Path(temporary.name); project = folder/'project'; project.mkdir()
            try:
                for name,content in data['files'].items():
                    path = project/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding='utf-8')
                subprocess.run(['git','-c','core.hooksPath=','init','--quiet',str(project)],check=True,
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                               env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')})
                request = folder/'request.json'
                request.write_text(json.dumps({**data,'files':None,'executable':self.executable}),encoding='utf-8')
                owner = ProcessRegistry()
                job = {'temporary':temporary,'owner':owner,'seen':time.monotonic(),'result':{'id':ident,'status':'running'}}
                def execute():
                    try:
                        command = [sys.executable,'-m','vita_tree.codex_host','--worker',str(request)]
                        owner.run(command,timeout=600,env=os.environ.copy())
                        job['result'] = {'id':ident,**json.loads((folder/'result.json').read_text(encoding='utf-8'))}
                    except Exception:
                        job['result'] = {'id':ident,'status':'failed','error':'Host Codex stopped or exceeded its time limit.'}
                job['thread'] = threading.Thread(target=execute,daemon=True)
                self.jobs[ident] = job; job['thread'].start()
                return {'id':ident,'status':'running'}
            except BaseException:
                temporary.cleanup(); raise

    def server_close(self):
        with self.lock:
            self.stopped.set()
            identifiers = list(self.jobs)
        self.sweeper.join(timeout=2)
        for ident in identifiers: self.remove(ident)
        deadline = time.monotonic()+5
        while self.retired and time.monotonic()<deadline:
            self.reap()
            if self.retired: time.sleep(.1)
        super().server_close()


class HostHandler(BaseHTTPRequestHandler):
    def log_message(self,*_): pass

    def reply(self, status, data):
        content = json.dumps(data).encode()
        self.send_response(status); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(content))); self.end_headers(); self.wfile.write(content)

    def handle_request(self):
        self.connection.settimeout(10)
        if self.headers.get('Origin') or not secrets.compare_digest(self.headers.get('Authorization',''),'Bearer '+self.server.token):
            self.reply(403,{'error':'Host authorization required'}); return
        try:
            if self.command == 'GET' and self.path == '/v1/capability':
                self.reply(200,{'protocol':1,'provider':'codex','snapshot':True}); return
            if self.command == 'POST' and self.path == '/v1/jobs':
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 16_000_000: raise ValueError('Request size limit')
                data = validate_request(json.loads(self.rfile.read(length)))
                self.reply(202,self.server.launch(data)); return
            if re.fullmatch(r'/v1/jobs/[a-f0-9]{32}',self.path):
                ident = self.path.rsplit('/',1)[1]
                if self.command == 'DELETE': self.server.remove(ident); self.reply(200,{'cancelled':True}); return
                if self.command == 'GET':
                    with self.server.lock:
                        job = self.server.jobs[ident]; job['seen'] = time.monotonic(); result = dict(job['result'])
                    self.reply(200,result); return
            self.reply(404,{'error':'Unknown host operation'})
        except HostCapacityError: self.reply(429,{'error':'Host capacity reached; no request was queued. Retry later.'})
        except (ValueError,KeyError,UnicodeError): self.reply(400,{'error':'Invalid host request or expired session'})

    do_GET = do_POST = do_DELETE = handle_request


def main():
    if sys.argv[1:2] == ['--worker']:
        worker(sys.argv[2]); return
    parser = argparse.ArgumentParser(description='Run the trusted local Codex snapshot connector')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--auth-file',type=Path,required=True)
    args = parser.parse_args()
    if args.auth_file.is_symlink(): parser.error('Authentication file must not be a symlink')
    if not args.auth_file.exists():
        args.auth_file.parent.mkdir(parents=True,exist_ok=True)
        descriptor = os.open(args.auth_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor,'w',encoding='utf-8') as file: file.write(secrets.token_urlsafe(48))
    token = args.auth_file.read_text(encoding='utf-8').strip()
    if len(token) < 32: parser.error('Authentication file must contain a random token of at least 32 characters')
    executable = shutil.which('codex')
    if not executable: parser.error('Install Codex CLI on this host and sign in first')
    if not shutil.which('git'): parser.error('Install Git on this host for isolated Codex snapshots')
    print('Local Codex connector ready. Keep its authentication file private.',flush=True)
    server = HostServer((args.host,args.port),token,executable)
    def stop(*_): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == '__main__': main()
