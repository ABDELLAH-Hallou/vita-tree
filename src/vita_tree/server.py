"""Dependency-free HTTP server and Git data layer for vita-tree."""

from __future__ import annotations

import json
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
    ) -> None:
        self.repository = repository
        self.document_path = document_path
        super().__init__(address, DashboardHandler)


class DashboardHandler(SimpleHTTPRequestHandler):
    server: VitaTreeServer

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        path = parsed.path
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

    def send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

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
) -> None:
    if not STATIC_ROOT.is_dir():
        raise RuntimeError(f"Dashboard assets not found: {STATIC_ROOT}")

    server = VitaTreeServer((host, port), repository, document_path)
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
