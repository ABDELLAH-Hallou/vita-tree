"""Executable transport adapter for Vita CV's existing VITA_CODEX hook."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
from urllib.parse import urlparse

from .codex_host import validate_files


def parse_arguments(arguments):
    values = list(arguments)
    if not values or values.pop(0) != 'exec': raise ValueError('Only Codex exec is supported')
    parser = argparse.ArgumentParser(exit_on_error=False)
    parser.add_argument('--sandbox', choices=['read-only'], required=True)
    parser.add_argument('--output-last-message', dest='output', required=True)
    parser.add_argument('--output-schema', dest='schema')
    parser.add_argument('--model', default='')
    parser.add_argument('--config', '-c', default='')
    parser.add_argument('stdin', choices=['-'])
    try:
        options, extra = parser.parse_known_args(values)
        if extra: raise ValueError('Unsupported Codex options')
        options.reasoning = ''
        if options.config:
            name, value = options.config.split('=', 1)
            if name != 'model_reasoning_effort': raise ValueError('Unsupported Codex configuration')
            options.reasoning = json.loads(value)
        if options.reasoning not in ('', 'none','minimal','low','medium','high','xhigh','max','ultra'):
            raise ValueError('Unsupported reasoning')
        return options
    except (argparse.ArgumentError, SystemExit, TypeError) as error:
        raise ValueError('Unsupported Codex arguments') from error


def snapshot(root):
    files = {}
    for base, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in {'.git','node_modules','__pycache__','.venv'}
                   and not (Path(base)/name).is_symlink()]
        for name in names:
            path = Path(base)/name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink(): continue
            try:
                validate_files({relative: ''})
            except ValueError:
                continue
            if path.stat().st_size > 2_000_000: raise ValueError('Codex snapshot file exceeds limit')
            files[relative] = path.read_text(encoding='utf-8-sig')
    return validate_files(files)


def local_file(root, name):
    from .workspace import safe_path
    path = Path(name)
    if path.is_absolute(): path = path.relative_to(root)
    return safe_path(root, path.as_posix())


def _run():
    if sys.argv[1:] == ['--version']:
        print('vita-codex-host protocol/1'); return
    base = os.environ.get('VITA_CODEX_HOST_URL', '').rstrip('/')
    parsed = urlparse(base)
    if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username or parsed.query or parsed.fragment or parsed.path:
        raise ValueError('Set VITA_CODEX_HOST_URL to the trusted host helper address')
    token = Path(os.environ['VITA_CODEX_HOST_AUTH_FILE']).read_text(encoding='utf-8').strip()
    if len(token) < 32: raise ValueError('Host authentication file is invalid')
    opener = build_opener(ProxyHandler({}))
    def request(method, path, data=None):
        encoded = json.dumps(data).encode() if data is not None else None
        req = Request(base+path, data=encoded, method=method,
                      headers={'Authorization': 'Bearer '+token, 'Content-Type':'application/json'})
        with opener.open(req, timeout=10) as response:
            content = response.read(16_000_001)
            if len(content) > 16_000_000: raise ValueError('Host response exceeds limit')
            return json.loads(content)
    if sys.argv[1:] == ['--check']:
        result = request('GET', '/v1/capability')
        if result.get('protocol') != 1: raise ValueError('Unsupported host protocol')
        print('Host Codex connection ready'); return
    options = parse_arguments(sys.argv[1:])
    root = Path.cwd().resolve()
    target = local_file(root, options.output)
    schema = json.loads(local_file(root, options.schema).read_text()) if options.schema else None
    prompt = sys.stdin.read(8_000_001)
    if len(prompt.encode()) > 8_000_000: raise ValueError('Prompt exceeds limit')
    job = request('POST', '/v1/jobs', {'files':snapshot(root), 'prompt':prompt,
                  'model':options.model, 'reasoning':options.reasoning, 'schema':schema})
    path = '/v1/jobs/'+job['id']
    def stop(*_): raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    try:
        while job['status'] == 'running':
            time.sleep(.3)
            job = request('GET', path)
        if job['status'] != 'succeeded':
            print(job.get('error', 'Codex host execution failed'), file=sys.stderr)
            raise SystemExit(1)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(job['output'], encoding='utf-8')
    finally:
        try: request('DELETE', path)
        except Exception: pass  # Host lease also cancels disconnected clients.


def main():
    try: _run()
    except HTTPError as error:
        print(f'HTTP {error.code}: Codex host rejected the request. Check authentication or host capacity.',file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, KeyError) as error:
        print('Codex host connection failed. Check the helper, authentication file and snapshot limits.', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__': main()
