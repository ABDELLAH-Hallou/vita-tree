"""Dependency-free HTTP server and Git data layer for vita-tree."""

from __future__ import annotations

import json
import re
import errno
import socket
import secrets
import subprocess
import os
import sys
import time
import uuid
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote
from .observability import Diagnostics, default_log_directory, request_context
from .security import redact, credential_name


STATIC_ROOT = Path(__file__).resolve().parent / "static"
FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"


def resolve_repository(path: str | Path) -> Path:
    candidate = Path(path).expanduser().resolve()
    process = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.returncode:
        message = process.stderr.strip() or f"Not a Git repository: {candidate}"
        raise RuntimeError(message)
    return Path(process.stdout.strip()).resolve()


def run_git(repository: Path, *args: str, strip: bool = True) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if process.returncode:
        message = process.stderr.strip() or "Git command failed"
        if 'permission denied' in message.lower() or 'access is denied' in message.lower():
            raise PermissionError(13, 'Git was denied access to repository files')
        raise RuntimeError(message)
    return process.stdout.strip() if strip else process.stdout


def branch_payload(repository: Path) -> dict[str, object]:
    """Return local branches plus remote-only branches, newest commit first."""
    git_format = FIELD_SEPARATOR.join(
        (
            "%(refname)",
            "%(refname:short)",
            "%(committerdate:iso8601-strict)",
            "%(committerdate:unix)",
            "%(objectname:short)",
            "%(authorname)",
            "%(subject)",
        )
    ) + RECORD_SEPARATOR

    raw = run_git(
        repository,
        "for-each-ref",
        "--sort=-committerdate",
        f"--format={git_format}",
        "refs/heads",
        "refs/remotes",
    )
    current = run_git(repository, "branch", "--show-current")
    branches: dict[str, dict[str, object]] = {}

    for record in raw.split(RECORD_SEPARATOR):
        record = record.strip("\r\n")
        if not record:
            continue
        fields = record.split(FIELD_SEPARATOR)
        if len(fields) != 7:
            continue

        ref, short_ref, iso_date, unix_date, commit, author, subject = fields
        is_remote = ref.startswith("refs/remotes/")
        if is_remote:
            if short_ref.endswith("/HEAD"):
                continue
            remote, _, name = short_ref.partition("/")
            if not name:
                continue
        else:
            remote, name = None, short_ref

        entry = {
            "name": name,
            "ref": ref,
            "modifiedAt": iso_date,
            "timestamp": int(unix_date or 0),
            "commit": commit,
            "author": author,
            "subject": subject,
            "current": name == current,
            "local": not is_remote,
            "remote": remote,
        }
        existing = branches.get(name)
        if existing is None or (not is_remote and not existing["local"]):
            branches[name] = entry

    ordered = sorted(
        branches.values(),
        key=lambda branch: (-int(branch["timestamp"]), str(branch["name"]).lower()),
    )
    return {
        "repository": repository.name,
        "repositoryPath": str(repository),
        "currentBranch": current or None,
        "detached": not bool(current),
        "branches": ordered,
    }


def branch_content_payload(
    repository: Path,
    name: str,
    document_path: str = "main.tex",
) -> dict[str, object]:
    """Read a document from a known branch without touching the working tree."""
    payload = branch_payload(repository)
    branch = next(
        (item for item in payload["branches"] if item["name"] == name),
        None,
    )
    if branch is None:
        raise ValueError(f"Application or CV not found: {name}")

    try:
        content = git_document(repository, branch['ref'], document_path)
    except RuntimeError as error:
        if "does not exist" in str(error) or "exists on disk" in str(error):
            raise FileNotFoundError(
                f"{document_path} does not exist on {name}"
            ) from error
        raise

    return {
        "branch": name,
        "path": document_path,
        "content": content,
        "commit": branch["commit"],
        "modifiedAt": branch["modifiedAt"],
    }


def git_document(repository, ref, name):
    """Read an immutable blob only after checking its byte size."""
    ident = run_git(repository, 'rev-parse', '--verify', f'{ref}:{name}')
    if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', ident):
        raise ValueError('Invalid document object')
    if int(run_git(repository, 'cat-file', '-s', ident)) > 2_000_000:
        raise ValueError('Document exceeds the 2 MB limit')
    return run_git(repository, 'cat-file', 'blob', ident, strip=False)


class VitaTreeServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR permits two live servers to share a port. POSIX
    # retains address reuse for restart, but never enables SO_REUSEPORT.
    allow_reuse_address = os.name != 'nt'
    allow_reuse_port = False

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            super().server_bind()
        except OSError as error:
            if error.errno == errno.EADDRINUSE or getattr(error, 'winerror', None) in {10048, 10013}:
                host, port = self.server_address[:2]
                reason = ('the port is already in use or Windows denied exclusive access'
                          if getattr(error, 'winerror', None) == 10013 else 'the port is already in use')
                raise RuntimeError(f'Cannot start Vita Tree at http://{host}:{port}: {reason}. '
                                   'Stop the existing server or choose another --port.') from error
            raise

    def __init__(
        self,
        address: tuple[str, int],
        repository: Path,
        document_path: str,
        vita_source: Path | None = None,
        log_dir: Path | None = None,
        log_level: str = 'INFO',
    ) -> None:
        if address[0] not in {'127.0.0.1','localhost'}:
            raise ValueError('Vita Tree supports loopback addresses only.')
        from .workspace import Workspace
        from .pdf import PDFCompiler
        self.repository = repository
        self.document_path = document_path
        self.diagnostics = Diagnostics(log_dir if log_dir is not None else default_log_directory(repository), log_level)
        self.workspace = None
        self.socket = None
        self._started = False
        self.token = secrets.token_urlsafe(32)
        try:
            super().__init__(address, DashboardHandler, bind_and_activate=False)
            # Reserve the port before loading history: a rejected second server
            # must not mark the first server's active runs as interrupted.
            self.server_bind()
            self.workspace = Workspace(repository, document_path, vita_source, self.diagnostics)
            self.compiler = PDFCompiler(self.workspace)
            self.server_activate()
        except Exception as error:
            self.diagnostics.error('request_failed', error, operation='server_start')
            self.server_close()
            raise
        self._started = True
        self.diagnostics.record('server_started', operation='server')

    def server_close(self):
        if self.workspace is not None:
            self.workspace.close()
        if self.socket is not None:
            super().server_close()
        if self._started:
            self.diagnostics.record('server_stopped', operation='server')
            self._started = False
        self.diagnostics.close()

    def handle_error(self, request, client_address):
        error = sys.exc_info()[1]
        if error:
            self.diagnostics.error('request_failed', error, operation='server_thread')

    def diagnostic_snapshot(self):
        runs = self.workspace.list_jobs()['runs']
        result = self.diagnostics.snapshot()
        result['history'] = {status: sum(run['status']==status for run in runs)
                             for status in ('running', 'succeeded', 'failed', 'interrupted')}
        return result


class DashboardHandler(SimpleHTTPRequestHandler):
    server: VitaTreeServer
    idle_timeout = 15
    # Windows registry associations can label JS modules as text/plain, which
    # browsers reject with nosniff. Keep bundled web assets platform-independent.
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".wasm": "application/wasm",
    }

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def setup(self):
        super().setup()
        self.connection.settimeout(self.idle_timeout)

    def _observe(self, action):
        self.request_id = uuid.uuid4().hex[:12]
        context_token = request_context.set(self.request_id)
        self.response_status = 500
        self.headers_sent = False
        started = time.monotonic()
        route = urlparse(self.path).path
        try:
            action()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            self.response_status = 499
            self.server.diagnostics.record('client_disconnected', 'DEBUG', request_id=self.request_id, route=route)
        except Exception as error:
            if not self.headers_sent:
                try:
                    self.error_response(error, 500, unexpected=True)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    self.response_status = 499
            else:
                self.server.diagnostics.error('request_failed', error, request_id=self.request_id, route=route)
        finally:
            try:
                self.server.diagnostics.request(self.command, route, self.response_status, time.monotonic()-started, self.request_id)
            finally:
                request_context.reset(context_token)

    def do_GET(self):
        self._observe(self._get)

    def do_HEAD(self):
        self._observe(lambda: super(DashboardHandler,self).do_HEAD() if self.check_origin() else None)

    @staticmethod
    def execution_offset(query):
        raw = query.get('offset', ['0'])[0]
        if not isinstance(raw, str) or not re.fullmatch(r'\d{1,6}', raw):
            raise ValueError('Invalid execution pagination offset')
        return int(raw)

    def _get(self) -> None:  # noqa: N802 - stdlib handler API
        if not self.check_origin():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == '/api/diagnostics':
            self.api_call(self.server.diagnostic_snapshot)
            return
        if path == '/api/executions':
            self.api_call(lambda: self.server.workspace.inspector.listing(self.execution_offset(query), query.get('q',[''])[0], query.get('status',[''])[0]))
            return
        if path == '/api/execution':
            self.api_call(lambda: self.server.workspace.inspector.public_detail(query.get('id',[''])[0], query.get('step',[None])[0], self.execution_offset(query)))
            return
        if path == '/api/execution-artifact':
            self.api_call(lambda: self.server.workspace.inspector.artifact(query.get('id',[''])[0], query.get('artifact',[''])[0]))
            return
        if path == '/api/execution-export':
            inspector = self.server.workspace.inspector
            if query.get('preview',[''])[0] == '1':
                self.api_call(lambda: inspector.export(query.get('id',[''])[0], preview=True))
            else:
                try:
                    body = inspector.export(query.get('id',[''])[0])
                    self.send_bytes(body, 'application/zip', filename='vita-tree-technical-support.zip', download=True)
                except (ValueError, OSError) as error:
                    self.error_response(error, 400)
            return
        if path == '/metrics':
            active = self.server.diagnostic_snapshot()['history']['running']
            self.send_bytes(self.server.diagnostics.prometheus(active).encode(), 'text/plain; version=0.0.4; charset=utf-8')
            return
        if path == "/api/session":
            self.send_json({"token": self.server.token, **self.server.workspace.capabilities()})
            return
        if path == '/api/jobenu':
            self.api_call(self.server.workspace.jobenu.listing)
            return
        if path == "/api/workspace":
            self.api_call(lambda: self.server.workspace.snapshot(query.get("branch", [""])[0]))
            return
        if path == "/api/providers":
            self.api_call(lambda: self.server.workspace.providers(query.get("branch", [""])[0]))
            return
        if path == '/api/connections':
            self.api_call(self.server.workspace.list_connections)
            return
        if path == '/api/ai-settings':
            self.api_call(lambda: self.server.workspace.ai_settings(query.get('branch', [''])[0]))
            return
        if path == "/api/job":
            ident = query.get("id", [""])[0]
            self.api_call(lambda: self.server.workspace.get_job(ident))
            return
        if path == "/api/jobs":
            self.api_call(self.server.workspace.list_jobs)
            return
        if path == "/api/job-result":
            self.api_call(lambda: self.server.workspace.job_result(query.get("id", [""])[0]))
            return
        if path == '/api/factual-review':
            self.api_call(lambda: self.server.workspace.factual_review(query.get('id', [''])[0]))
            return
        if path == '/api/requirements':
            from . import requirements_review
            self.api_call(lambda: requirements_review.view(self.server.workspace, query.get('branch',[''])[0], query.get('runId',[None])[0]))
            return
        if path == "/api/pdf-file":
            pdf = self.server.compiler.results.get(query.get("id", [""])[0])
            if not pdf or not pdf.is_file():
                self.send_json({"error": "This preview has expired. Create it again."}, status=404)
            else:
                info = self.server.compiler.previews.get(query.get('id', [''])[0], {})
                self.send_bytes(pdf.read_bytes(), "application/pdf", filename=info.get('filename'),
                                download=query.get('download', [''])[0]=='1')
            return
        if path == "/api/branches":
            self.api_call(self.server.workspace.applications)
            return
        if path == "/api/branch-content":
            name = query.get('branch', [''])[0]
            if not name:
                self.send_json({'error': 'Missing branch name'}, status=400)
                return
            self.api_call(lambda: branch_content_payload(self.server.repository, name, self.server.document_path))
            return
        if path == "/health":
            self.send_json(
                {"ok": True, "repository": str(self.server.repository)}
            )
            return
        super().do_GET()

    def check_origin(self):
        # Loopback service with same-origin checks: unrelated web pages cannot
        # read the token, run AI, or mutate local repositories through a browser.
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        site = self.headers.get('Sec-Fetch-Site')
        if host not in allowed or (origin and origin != "http://" + host) or site not in {None,'none','same-origin'}:
            self.send_json({"error": "This connection is not allowed. Open Vita Tree using its local address."}, status=403)
            return False
        return True

    def do_POST(self):
        self._observe(self._post)

    def _post(self):
        if not self.check_origin():
            return
        if not secrets.compare_digest(self.headers.get("X-Vita-Token", ""), self.server.token):
            self.send_json({"error": "Your connection needs to be refreshed. Reload the page and try again."}, status=403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > (24_000_000 if urlparse(self.path).path=='/api/jobenu/upload' else 3_000_000):
                raise ValueError("Invalid request size")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected application/json")
            body = self.rfile.read(size)
            if len(body) != size:
                raise ValueError('Incomplete request')
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
        except (ValueError, UnicodeError, RecursionError, TimeoutError):
            self.send_json({"error": 'Invalid JSON request, content type, or request size (maximum 3 MB).'}, status=400)
            return
        workspace = self.server.workspace
        path = urlparse(self.path).path
        actions = {
            '/api/jobenu/capability': lambda: workspace.jobenu.capability(data.get('source','')),
            '/api/jobenu/upload': lambda: workspace.jobenu.upload(data.get('filename','export.json'),data.get('content')),
            '/api/jobenu/selection': lambda: workspace.jobenu.selection(data['id']),
            '/api/jobenu/preview': lambda: workspace.jobenu.preview(data['id'],data),
            '/api/jobenu/start': lambda: workspace.jobenu.start(data['id'],data['planId']),
            '/api/jobenu/review': lambda: workspace.jobenu.review(data['id'],data['key']),
            '/api/jobenu/decide': lambda: workspace.jobenu.decide(data['id'],data['key'],data['action'],data.get('revision')),
            '/api/jobenu/log': lambda: workspace.jobenu.log(data['id'],data.get('key')),
            '/api/jobenu/alias': lambda: workspace.jobenu.alias(data['title'],data['alias']),
            '/api/jobenu/discard': lambda: workspace.jobenu.discard(data['id']),
            '/api/connections': lambda: workspace.add_connection(data.get('name'), data.get('provider'), data.get('apiKey')),
            '/api/connections/remove': lambda: workspace.remove_connection(data.get('id')),
            '/api/generation-check': lambda: workspace.check_generation(data['branch'], data['step'], data.get('aiConfig'), data.get('confirmed')),
            '/api/preflight': lambda: workspace.check_setup(data['branch'], data.get('revision'), data.get('jobRevision'), data.get('engine','auto'), data.get('workflow')),
            '/api/factual-review/apply': lambda: workspace.apply_factual_review(data['id'], data['revision'], data['token'], data.get('decisions'), data.get('confirmed')),
            '/api/review-continue': lambda: workspace.continue_review(data['id'], data['revision'], data['jobRevision']),
            '/api/requirements/draft': lambda: workspace.save_requirements(data['branch'], data['token'], data['revision'], data.get('items')),
            '/api/requirements/approve': lambda: workspace.approve_requirements(data['branch'], data['token'], data['revision'], data.get('confirmed')),
            '/api/ai-settings': lambda: workspace.save_ai_settings(data['branch'], data.get('settings')),
            '/api/resume-preview': lambda: workspace.resume_ai(data['id'], data['revision'], data['jobRevision'], data.get('aiConfig'), data.get('language'), preview=True),
            '/api/resume': lambda: workspace.resume_ai(data['id'], data['revision'], data['jobRevision'], data.get('aiConfig'), data.get('language'), data.get('token')),
            '/api/checkpoints-cleanup': workspace.cleanup_checkpoints,
            "/api/release-worktree": lambda: workspace.release_worktree(data["branch"]),
            "/api/job-reviewed": lambda: workspace.review_job(data["id"]),
            "/api/jobs-reviewed": lambda: {**workspace.review_jobs(data["ids"]), 'requestId': self.request_id},
            "/api/save": lambda: workspace.save(data["branch"], data["path"], data["revision"], data.get("content"), data.get("leaf"), data.get("text"), data.get('projectRevision')),
            "/api/commit-preview": lambda: workspace.commit_preview(data["branch"], data.get("sourceRevision"), data.get("sourceContent"), data.get("jobRevision"), data.get("jobContent")),
            "/api/commit-push": lambda: workspace.commit_and_push(data["branch"], data.get("message"), data.get("review"), data.get("sourceRevision"), data.get("sourceContent"), data.get("jobRevision"), data.get("jobContent")),
            "/api/create": lambda: (workspace.create_application(data["base"], data["applicationName"], data["job"], data["revision"], data.get('projectRevision')) if "applicationName" in data else workspace.create(data["base"], data["name"], data["job"], data["revision"], project_revision=data.get('projectRevision'))),
            "/api/adapt": lambda: workspace.start_ai(data["branch"], data["revision"], data["jobRevision"], data.get("provider", ""), data.get("language", "en"), data.get("model"), data.get("reasoning", ""), data.get("workflow"), data.get('aiConfig'), engine=data.get('engine','auto'), review_policy=data.get('reviewPolicy','manual')),
            "/api/parse": lambda: self.parse_source(data),
            "/api/lint": lambda: self.parse_source(data, lint_only=True),
            "/api/pdf-save": lambda: self.server.compiler.save(data['id'], data['branch'], data.get('existingRevision')),
            "/api/pdf": lambda: self.server.compiler.compile(data["branch"], data.get("side", "current"), data.get("engine", "auto"), data.get("document", "cv"), data.get("runId")),
        }
        if path not in actions:
            self.send_json({"error": "Unknown endpoint"}, status=404)
            return
        self.api_call(actions[path])

    def parse_source(self, data, lint_only=False):
        from .latex import parse_document, lint_source
        content = data["content"]
        if not isinstance(content, str) or len(content) > 2_000_000:
            raise ValueError("Invalid source")
        return {"diagnostics": lint_source(content)} if lint_only else parse_document(content)

    def error_response(self, error, status, extra=None, unexpected=False):
        reference = getattr(self, 'request_id', uuid.uuid4().hex[:12])
        self.server.diagnostics.error('request_failed', error, level='ERROR' if status>=500 else 'WARNING',
                                      request_id=reference, route=urlparse(self.path).path)
        if isinstance(error, PermissionError):
            message = 'Vita Tree does not have permission to save these files. Your existing work is safe. Restart Vita Tree from a normal terminal with access to your CV collection.'
        elif isinstance(error, OSError):
            message = 'A local file operation failed. Check disk space and folder permissions.'
        elif unexpected:
            message = 'The operation could not finish. Open Activity & logs for details.'
        else:
            message = str(error)
        values = list(getattr(self.server.workspace.inspector, 'secrets', ()))
        values.append(self.server.token)
        values.extend(item['key'] for item in self.server.workspace.connections.items.values())
        values.extend(v for k,v in os.environ.items() if credential_name(k))
        message = redact(message, values)
        self.send_json({'error': message + ' Reference: ' + reference, 'requestId': reference, **(extra or {})}, status=status)

    def api_call(self, action):
        from .workspace import ConflictError, PushError
        from .pdf import PDFExistsError
        try:
            result = action()
        except PDFExistsError as error:
            self.error_response(error, 409, {'filename': error.filename, 'existingRevision': error.revision})
        except PushError as error:
            self.error_response(error, 502, {'commitCreated': error.commit_created, 'commit': error.commit, 'canRetry': True})
        except ConflictError as error:
            self.error_response(error, 409)
        except FileNotFoundError as error:
            self.error_response(error, 404)
        except (ValueError, KeyError, TypeError) as error:
            self.error_response(error, 400)
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            self.error_response(error, 500)
        else:
            self.send_json(result)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data: blob:; worker-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'; form-action 'self'")
        self.send_header('X-Request-ID', getattr(self, 'request_id', ''))
        super().end_headers()
        self.headers_sent = True

    def send_response(self, code, message=None):
        self.response_status = code
        super().send_response(code, message)

    def send_bytes(self, body: bytes, content_type: str, status=200, filename=None, download=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if filename:
            self.send_header('Content-Disposition', ('attachment' if download else 'inline') + "; filename=\"cv.pdf\"; filename*=UTF-8''" + quote(filename))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(body, "application/json; charset=utf-8", status)

    def log_message(self, message_format: str, *args: object) -> None:
        pass  # Structured request observations exclude URLs, payloads and headers.


def serve(
    repository: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    document_path: str = "main.tex",
    open_browser: bool = True,
    vita_source: Path | None = None,
    log_dir: Path | None = None,
    log_level: str = 'INFO',
) -> None:
    if not STATIC_ROOT.is_dir():
        raise RuntimeError(f"Dashboard assets not found: {STATIC_ROOT}")

    if host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Vita Tree supports localhost only because it can edit files and run AI.")
    server = VitaTreeServer((host, port), repository, document_path, vita_source, log_dir, log_level)
    url = f"http://{host}:{server.server_port}"
    print(f"vita-tree · {repository}")
    print(f"Dashboard running at {url}")
    print(f"Metrics: {url}/metrics")
    if server.diagnostics.handler:
        print(f"Logs: {server.diagnostics.path}")
    else:
        print(server.diagnostics.file_error or 'File logging is disabled.', file=sys.stderr)
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping vita-tree.")
    finally:
        server.server_close()
