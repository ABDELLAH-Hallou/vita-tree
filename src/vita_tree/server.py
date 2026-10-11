"""Dependency-free HTTP server and Git data layer for vita-tree."""

from __future__ import annotations

import json
import secrets
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


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
        raise ValueError(f"Unknown branch: {name}")

    try:
        content = run_git(
            repository,
            "show",
            f"{branch['ref']}:{document_path}",
            strip=False,
        )
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


class VitaTreeServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        repository: Path,
        document_path: str,
        vita_source: Path | None = None,
    ) -> None:
        from .workspace import Workspace
        from .pdf import PDFCompiler
        self.repository = repository
        self.document_path = document_path
        self.workspace = Workspace(repository, document_path, vita_source)
        self.compiler = PDFCompiler(self.workspace)
        self.token = secrets.token_urlsafe(32)
        super().__init__(address, DashboardHandler)


class DashboardHandler(SimpleHTTPRequestHandler):
    server: VitaTreeServer
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

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if not self.check_origin():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/session":
            self.send_json({"token": self.server.token, **self.server.workspace.capabilities()})
            return
        if path == "/api/workspace":
            self.api_call(lambda: self.server.workspace.snapshot(query.get("branch", [""])[0]))
            return
        if path == "/api/providers":
            self.api_call(lambda: self.server.workspace.providers(query.get("branch", [""])[0]))
            return
        if path == "/api/job":
            ident = query.get("id", [""])[0]
            record = self.server.workspace.jobs.get(ident)
            self.send_json(record or {"error": "Unknown run"}, status=200 if record else 404)
            return
        if path == "/api/pdf-file":
            pdf = self.server.compiler.results.get(query.get("id", [""])[0])
            if not pdf or not pdf.is_file():
                self.send_json({"error": "Preview expired. Compile again."}, status=404)
            else:
                self.send_bytes(pdf.read_bytes(), "application/pdf")
            return
        if path == "/api/branches":
            try:
                self.send_json(branch_payload(self.server.repository))
            except (RuntimeError, OSError, ValueError) as error:
                self.send_json({"error": str(error)}, status=500)
            return
        if path == "/api/branch-content":
            name = parse_qs(parsed.query).get("branch", [""])[0]
            if not name:
                self.send_json({"error": "Missing branch name"}, status=400)
                return
            try:
                self.send_json(
                    branch_content_payload(
                        self.server.repository,
                        name,
                        self.server.document_path,
                    )
                )
            except (ValueError, FileNotFoundError) as error:
                self.send_json({"error": str(error)}, status=404)
            except (RuntimeError, OSError) as error:
                self.send_json({"error": str(error)}, status=500)
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
        if host not in allowed or (origin and origin != "http://" + host):
            self.send_json({"error": "Only same-origin localhost requests are allowed"}, status=403)
            return False
        return True

    def do_POST(self):
        if not self.check_origin():
            return
        if not secrets.compare_digest(self.headers.get("X-Vita-Token", ""), self.server.token):
            self.send_json({"error": "Invalid session token. Reload the page."}, status=403)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 3_000_000:
                raise ValueError("Invalid request size")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected application/json")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
        except (ValueError, UnicodeError) as error:
            self.send_json({"error": str(error)}, status=400)
            return
        workspace = self.server.workspace
        path = urlparse(self.path).path
        actions = {
            "/api/save": lambda: workspace.save(data["branch"], data["path"], data["revision"], data.get("content"), data.get("leaf"), data.get("text")),
            "/api/create": lambda: workspace.create(data["base"], data["name"], data["job"], data["revision"]),
            "/api/adapt": lambda: workspace.start_ai(data["branch"], data["revision"], data["jobRevision"], data.get("provider", ""), data.get("language", "en"), data.get("model"), data.get("reasoning", "")),
            "/api/parse": lambda: self.parse_source(data),
            "/api/lint": lambda: self.parse_source(data, lint_only=True),
            "/api/pdf": lambda: self.server.compiler.compile(data["branch"], data.get("side", "current"), data.get("engine", "auto")),
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

    def api_call(self, action):
        from .workspace import ConflictError
        try:
            result = action()
        except ConflictError as error:
            self.send_json({"error": str(error)}, status=409)
        except FileNotFoundError as error:
            self.send_json({"error": str(error)}, status=404)
        except (ValueError, KeyError, TypeError) as error:
            self.send_json({"error": str(error)}, status=400)
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            self.send_json({"error": str(error)}, status=500)
        else:
            try:
                self.send_json(result)
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                pass  # The client navigated away while the operation completed.

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data: blob:; worker-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()

    def send_bytes(self, body: bytes, content_type: str, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(body, "application/json; charset=utf-8", status)

    def log_message(self, message_format: str, *args: object) -> None:
        if args and str(args[1]) == "200":
            return
        super().log_message(message_format, *args)


def serve(
    repository: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    document_path: str = "main.tex",
    open_browser: bool = True,
    vita_source: Path | None = None,
) -> None:
    if not STATIC_ROOT.is_dir():
        raise RuntimeError(f"Dashboard assets not found: {STATIC_ROOT}")

    if host not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("Vita Tree supports localhost only because it can edit files and run AI.")
    server = VitaTreeServer((host, port), repository, document_path, vita_source)
    url = f"http://{host}:{server.server_port}"
    print(f"vita-tree · {repository}")
    print(f"Dashboard running at {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping vita-tree.")
    finally:
        server.server_close()
