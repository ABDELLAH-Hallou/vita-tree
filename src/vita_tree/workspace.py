"""Branch workspaces, optimistic file writes, and isolated VITA jobs."""
from __future__ import annotations

import difflib
import hashlib
from importlib.metadata import distribution, PackageNotFoundError
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
import unicodedata
from urllib.parse import urlsplit

from .fileio import atomic_write_bytes
from .observability import Diagnostics
from .latex import parse_document, replace_leaf
from .workflow import REPORTS, MESSAGES, capabilities as workflow_capabilities, plan, transition, clean_stages, reusable_reports
from .server import branch_payload, run_git


class ConflictError(ValueError):
    pass


class PushError(RuntimeError):
    def __init__(self, message, *, commit_created=False, commit=None):
        super().__init__(message)
        self.commit_created = commit_created
        self.commit = commit


class AIRunError(ValueError):
    """A fixed, user-facing message safe to expose in the global runs list."""


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def safe_path(root: Path, name: str) -> Path:
    path = PurePosixPath(name)
    if not name or not path.parts or "\x00" in name or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or path.parts[0].lower() == ".git":
        raise ValueError("Invalid repository-relative path")
    target = root.joinpath(*path.parts)
    for parent in [target, *target.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError("Symlink paths are not supported")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escapes the repository")
    return target


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.stat().st_size > 2_000_000:
        raise ValueError("Document exceeds the 2 MB limit")
    return path.read_text(encoding="utf-8-sig")


def atomic_write(path: Path, content: str):
    atomic_write_bytes(path, content.encode('utf-8'))


class Workspace:
    def __init__(self, repository: Path, document_path="main.tex", vita_source: Path | None = None, diagnostics=None):
        self.repository = repository
        self.diagnostics = diagnostics or Diagnostics()
        self.document_path = document_path
        safe_path(repository, document_path)
        common = Path(run_git(repository, "rev-parse", "--git-common-dir"))
        self.root = (repository / common).resolve() / "vita-tree"
        self.lock = threading.RLock()
        self.jobs: dict[str, dict] = {}
        self._ai_threads = set()
        self._closed = False
        self._publishing = set()
        self._previewing = {}
        self._release_requested = set()
        self._publish_locks = {}
        self._load_jobs()
        self.vita_source = vita_source
        if self.vita_source is None:
            try:
                # The optional [ai] extra installs VITA in this interpreter, so
                # pipx/uv users get the same bridge as --vita-source users.
                self.vita_source = Path(distribution('vita-cv').locate_file('')).resolve()
            except PackageNotFoundError:
                pass

    def branch(self, name):
        for branch in branch_payload(self.repository)["branches"]:
            if branch["name"] == name:
                return branch
        raise ValueError(f"Application or CV not found: {name}")

    def applications(self):
        result = branch_payload(self.repository)
        for branch in result['branches']:
            try:
                meta = self.metadata(branch['name'])
                label = meta.get('displayName') if isinstance(meta, dict) else None
            except (OSError, ValueError, TypeError):
                label = None
            branch['displayName'] = label if isinstance(label,str) and label.strip() else branch['name']
        return result

    def create_application(self, base, label, job, revision):
        if not isinstance(label, str) or not label.strip() or len(label.strip()) > 100 or any(c in label for c in '\r\n\x00'):
            raise ValueError('Enter an application name of up to 100 characters.')
        label = label.strip()
        name = unicodedata.normalize('NFKD', label).encode('ascii', 'ignore').decode().lower()
        name = re.sub(r'[^a-z0-9]+', '-', name).strip('-')[:80].rstrip('-')
        if not name or name == 'head':
            name = 'application-' + digest(label)[:10]
        with self.lock:
            branches = self.applications()['branches']
            if any(branch['displayName'].casefold() == label.casefold() for branch in branches):
                raise ValueError('An application or saved CV with this name already exists. Choose another name.')
            existing = {branch['name'] for branch in branches}
            if name in existing:
                name = name[:70] + '-' + digest(label)[:8]
                while name in existing:
                    name = name[:70] + '-' + uuid.uuid4().hex[:8]
            return self.create(base, name, job, revision, display_name=label)

    def save_state(self, name, location):
        draft = bool(location and run_git(location, 'status', '--porcelain', '--untracked-files=all', '--ignored', '--', *self.publish_paths()))
        upstream = self._git_process(self.repository, 'rev-parse', '--verify', name + '@{upstream}')
        ahead = None
        if upstream.returncode == 0:
            count = self._git_process(self.repository, 'rev-list', '--count', upstream.stdout.strip() + '..' + self.head(name))
            if count.returncode == 0:
                ahead = int(count.stdout.strip())
        return {'draft': draft, 'ahead': ahead}

    def head(self, name):
        return run_git(self.repository, "rev-parse", self.branch(name)["ref"])

    def committed(self, commit, filename):
        safe_path(self.repository, filename)
        try:
            return run_git(self.repository, "show", f"{commit}:{filename}", strip=False)
        except RuntimeError:
            # Distinguish absent files from command/repository failures.
            paths = run_git(self.repository, "ls-tree", "--name-only", commit, "--", filename)
            if not paths:
                return ""
            raise

    def location(self, name, create=False):
        branch = self.branch(name)
        records = run_git(self.repository, "worktree", "list", "--porcelain", "-z", strip=False)
        for record in records.split("\0\0"):
            fields = dict(part.split(" ", 1) for part in record.split("\0") if " " in part)
            if fields.get("branch") == branch["ref"]:
                return Path(fields["worktree"]).resolve()
        if not create:
            return None
        if not branch["local"]:
            raise ValueError("Use this view-only CV to create an application before editing.")
        target = self.root / "worktrees" / digest(name)[:20]
        target.parent.mkdir(parents=True, exist_ok=True)
        run_git(self.repository, "-c", "core.hooksPath=", "worktree", "add", str(target), name)
        return target

    def metadata_path(self, name):
        return self.root / "branches" / (digest(name) + ".json")

    def release_worktree(self, name):
        """Release only an idle, clean worktree owned by this application."""
        with self.lock:
            if self.active_job(name) or name in self._publishing or self._previewing.get(name):
                self._release_requested.add(name)
                return {"released": False, "reason": "active", "message": "This application is still working."}
            self._release_requested.discard(name)
            location = self.location(name)
            expected = self.root / "worktrees" / digest(name)[:20]
            if location is None:
                return {"released": False, "reason": "absent", "message": "The branch is already available in Git."}
            if location == self.repository.resolve() or location != expected.resolve() or expected.is_symlink():
                return {"released": False, "reason": "external", "message": "This folder is managed outside Vita Tree."}
            # Ignored files may contain credentials or local reports: never discard them.
            if run_git(location, "status", "--porcelain", "--untracked-files=all", "--ignored"):
                return {"released": False, "reason": "dirty", "message": "Your application folder was kept because it contains files that have not been saved as a version."}
            try:
                run_git(self.repository, "worktree", "remove", str(location))
            except RuntimeError:
                return {"released": False, "reason": "locked", "message": "Some application files are still in use. Close programs using them and try again."}
            return {"released": True, "reason": "clean", "message": "Application folder closed. You can reopen this application at any time."}

    def metadata(self, name):
        path = self.metadata_path(name)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def read(self, name, filename):
        location = self.location(name)
        return read_text(safe_path(location, filename)) if location else self.committed(self.head(name), filename)

    def snapshot(self, name):
        with self.lock:
            return self._snapshot(name)

    def _snapshot(self, name):
        branch = self.branch(name)
        commit = run_git(self.repository, "rev-parse", branch["ref"])
        meta = self.metadata(name)
        baseline = meta.get("baseCommit", commit)
        location = self.location(name)
        def read(filename):
            return read_text(safe_path(location, filename)) if location else self.committed(commit, filename)
        source = read(self.document_path)
        original = meta.get("original", self.committed(baseline, self.document_path))
        if not source:
            raise FileNotFoundError(f"{self.document_path} is missing or empty on {name}")
        job = read("job.md")
        artifacts = {}
        for label in ("analyze", "adapt", "review", "delta", "cover", "extract"):
            for path in ((".vita/results/analysis.md", ".vita/results/analyze.md", "analyze.md") if label == "analyze" else
                         (".vita/results/job.json",) if label == "extract" else
                         (f".vita/results/{label}.md", f"{label}.md")):
                value = read(path)
                if value:
                    artifacts[label] = {"path": path, "content": value}
                    break
        return {"branch": name, "displayName": meta.get("displayName") or name, "saveState": self.save_state(name, location), "path": self.document_path, "commit": commit,
                "baseCommit": baseline, "baseBranch": meta.get("baseBranch", name + " · committed"),
                "content": source, "revision": digest(source), "document": parse_document(source),
                "original": original, "originalDocument": parse_document(original),
                "job": job, "jobRevision": digest(job), "artifacts": artifacts, "cover": read("cover-letter.tex"),
                "diff": "".join(difflib.unified_diff(original.splitlines(True), source.splitlines(True), fromfile="original/"+self.document_path, tofile=name+"/"+self.document_path)),
                "worktree": str(location) if location else None, "editable": bool(branch["local"]),
                "dirty": source != self.committed(commit, self.document_path),
                "running": self.active_job(name)}

    JOB_FIELDS = ("id", "branch", "opportunity", "status", "step", "message", "provider", "model",
                  "reasoning", "language", "createdAt", "startedAt", "finishedAt", "reviewed", "stages")
    ACTIVE_STATUSES = {"queued", "running"}

    def _public_job(self, record):
        result = {key: record.get(key) for key in self.JOB_FIELDS}
        start = record.get("startedAt")
        result["elapsedSeconds"] = max(0, (record.get("finishedAt") or time.time()) - start) if start else 0
        return result

    def _persist_job(self, record):
        try:
            atomic_write(self.root / "job-history" / (record["id"] + ".json"),
                         json.dumps({key: record.get(key) for key in self.JOB_FIELDS}))
        except OSError as error:
            self.diagnostics.error('history_write_failed', error, run_id=record['id'], operation='job_history')
            raise

    def _load_jobs(self):
        for path in (self.root / "job-history").glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if (not re.fullmatch(r"[a-f0-9]{32}", path.stem) or record.get("id") != path.stem
                        or not isinstance(record.get("branch"), str)
                        or record.get("status") not in self.ACTIVE_STATUSES | {"succeeded", "failed", "interrupted"}):
                    continue
                record = {key: record.get(key) for key in self.JOB_FIELDS}
                record["stages"] = clean_stages(record.get("stages"))
                if any(value is not None and (type(value) not in (int, float) or not 0 <= value < 1e12)
                       for value in (record.get(key) for key in ("createdAt", "startedAt", "finishedAt"))):
                    continue
                if record["status"] in self.ACTIVE_STATUSES:
                    previous = dict(record)
                    record["stages"] = transition(record.get("stages"), terminal="interrupted")
                    record.update(status="interrupted", step="interrupted", finishedAt=time.time(), reviewed=False,
                                  message="Vita Tree stopped before this preparation finished. Review the application and start again.")
                    try:
                        self._persist_job(record)
                    except OSError:
                        pass  # Keep recovered history visible even when its folder is read-only.
                    self.diagnostics.workflow(record, previous)
                self.jobs[record["id"]] = record
            except (OSError, ValueError, TypeError, AttributeError) as error:
                self.diagnostics.error('history_load_failed', error, operation='job_history')
                continue  # A damaged history entry must not prevent opening the CV.

    def list_jobs(self):
        with self.lock:
            return {"runs": [self._public_job(j) for j in sorted(self.jobs.values(),
                    key=lambda j: j.get("createdAt") or 0, reverse=True)]}

    def get_job(self, ident):
        with self.lock:
            if ident not in self.jobs:
                raise FileNotFoundError("Preparation not found")
            return self._public_job(self.jobs[ident])

    def review_job(self, ident):
        with self.lock:
            self.get_job(ident)
            record = self.jobs[ident]
            if record["status"] in self.ACTIVE_STATUSES:
                raise ConflictError("This preparation is still in progress. Review the results when it finishes.")
            if record.get('reviewed'):
                return self._public_job(record)
            updated = {**record, 'reviewed': True}
            try:
                self._persist_job(updated)
            except OSError as error:
                raise RuntimeError('Your review could not be saved; the results remain unreviewed. Check disk space and folder access, then restart Vita Tree from a normal terminal if needed.') from error
            record.update(updated)
            self.diagnostics.record('review_saved', run_id=ident)
            return self._public_job(record)

    def review_jobs(self, identifiers):
        if not isinstance(identifiers, list) or not 1 <= len(identifiers) <= 500 or any(
                not isinstance(ident, str) or not re.fullmatch(r'[a-f0-9]{32}', ident) for ident in identifiers):
            raise ValueError('Select between 1 and 500 results to mark as reviewed.')
        reviewed, failed = [], []
        with self.lock:
            for ident in dict.fromkeys(identifiers):
                if ident not in self.jobs:
                    failed.append({'id': ident, 'error': 'These results are no longer available. Refresh the applications list.'})
                    continue
                if self.jobs[ident]['status'] in self.ACTIVE_STATUSES:
                    failed.append({'id': ident, 'error': 'This preparation is still in progress. Wait for it to finish.'})
                    continue
                try:
                    self.review_job(ident)
                except (RuntimeError, OSError):
                    failed.append({'id': ident, 'error': 'Review state could not be saved. Check write access and retry.'})
                else:
                    reviewed.append(ident)
        return {'reviewed': reviewed, 'failed': failed}

    def cover_pdf_result(self, ident):
        record = self.get_job(ident)
        if record['status'] in self.ACTIVE_STATUSES:
            return None
        folder = safe_path(self.root, 'run-pdfs/' + ident)
        ready, pdf = safe_path(folder, 'ready.json'), safe_path(folder, 'cover-letter.pdf')
        if not ready.is_file() or not pdf.is_file():
            return None
        try:
            info = json.loads(read_text(ready))
            if info['engine'] not in {'pdflatex','xelatex','lualatex'} or not isinstance(info['warnings'], list):
                return None
        except (ValueError, KeyError, TypeError):
            return None
        with pdf.open('rb') as stream:
            if stream.read(5) != b'%PDF-':
                return None
        return {'pdf': pdf, 'engine': info['engine'], 'warnings': info['warnings']}

    def job_result(self, ident):
        record = self.get_job(ident)
        if record["status"] in self.ACTIVE_STATUSES:
            raise ConflictError("This preparation has not finished yet.")
        files = {}
        stage = self.root / "runs" / record["id"]
        for filename in (*self.report_paths(), "main.tex", "job.md", "cover-letter.tex"):
            path = safe_path(stage, filename)
            if path.is_file():
                files[filename] = read_text(path)
        original = safe_path(self.root / "run-inputs" / record["id"], "main.tex")
        if original.is_file():
            files["original/main.tex"] = read_text(original)
        skipped = {task['id'] for task in record.get('stages') or [] if task['status'] == 'skipped'}
        inputs = {'job.md', 'original/main.tex'}
        if 'adapt' in skipped:
            inputs.add('main.tex')
        inputs.update('.vita/results/' + filename for step in skipped if step in REPORTS for filename in REPORTS[step])
        return {"run": record, "files": files, "inputs": sorted(inputs & files.keys()),
                "coverPdf": {"runId": ident} if self.cover_pdf_result(ident) else None}

    def active_job(self, name):
        with self.lock:
            return next((self._public_job(j) for j in self.jobs.values()
                         if j["branch"] == name and j["status"] in self.ACTIVE_STATUSES), None)

    def close(self):
        with self.lock:
            self._closed = True
            for record in self.jobs.values():
                if record["status"] in self.ACTIVE_STATUSES:
                    previous = dict(record)
                    record["stages"] = transition(record.get("stages"), terminal="interrupted")
                    record.update(status="interrupted", step="interrupted", finishedAt=time.time(), reviewed=False,
                                  message="Vita Tree stopped before this preparation finished. Review the application and start again.")
                    try:
                        self._persist_job(record)
                    except OSError:
                        pass
                    self.diagnostics.workflow(record, previous)

    def busy(self, name):
        if self.active_job(name):
            raise ConflictError("This application is being prepared. Wait before changing its files.")
        if name in self._publishing:
            raise ConflictError("This application is being saved and synced. Wait before changing it.")

    def save(self, name, filename, revision, content=None, leaf=None, text=None):
        if filename not in {self.document_path, "job.md"}:
            raise ValueError("Only the CV and job description can be edited here")
        with self.lock:
            self.busy(name)
            location = self.location(name, create=True)
            target = safe_path(location, filename)
            current = read_text(target)
            if digest(current) != revision:
                raise ConflictError("This file changed outside the editor. Copy your edits, then reload before saving.")
            if leaf is not None:
                if filename != self.document_path or not isinstance(text, str):
                    raise ValueError("Invalid structured edit")
                content = replace_leaf(current, str(leaf), text)
            if not isinstance(content, str) or len(content.encode("utf-8")) > 2_000_000:
                raise ValueError("Invalid file content (maximum 2 MB)")
            atomic_write(target, content)
            return {"revision": digest(content), "content": content, "path": str(target), "saveState": self.save_state(name, location)}

    @staticmethod
    def report_paths():
        return tuple(".vita/results/" + file for files in REPORTS.values() for file in files)

    def publish_paths(self):
        """Files Vita Tree owns and may include in a UI-created commit."""
        return tuple(dict.fromkeys((
            self.document_path,
            "job.md",
            "cover-letter.tex",
            *self.report_paths(),
            ".vita/results/analyze.md",
            ".vita/results/adapt.md",
            ".vita/results/review.md",
            "analyze.md",
            "adapt.md",
            "review.md",
        )))

    @staticmethod
    def _git_process(location, *args):
        return subprocess.run(
            ["git", *args], cwd=location, check=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )

    def _publish_target(self, location, name):
        remote = self._git_process(location, "config", "--get", f"branch.{name}.remote")
        merge = self._git_process(location, "config", "--get", f"branch.{name}.merge")
        remote_name = remote.stdout.strip() if remote.returncode == 0 else ""
        destination = merge.stdout.strip() if merge.returncode == 0 else ""
        if remote_name == ".":
            remote_name = ""
        remotes = self._git_process(location, "remote")
        names = [item for item in remotes.stdout.splitlines() if item]
        if not remote_name:
            remote_name = "origin" if "origin" in names else names[0] if len(names) == 1 else ""
        if remote_name not in names:
            remote_name = ""
        if not destination.startswith("refs/heads/"):
            destination = f"refs/heads/{name}"
        remote_branch = destination.removeprefix("refs/heads/")
        upstream = f"{remote_name}/{remote_branch}" if remote_name and remote.returncode == 0 else None
        ahead = None
        if upstream:
            count = self._git_process(location, "rev-list", "--count", f"{upstream}..refs/heads/{name}")
            if count.returncode == 0:
                ahead = int(count.stdout.strip() or 0)
        return remote_name or None, remote_branch, upstream, ahead

    def _pending_writes(self, location, source_revision, source_content, job_revision, job_content):
        pending = {}
        for filename, revision, content in (
            (self.document_path, source_revision, source_content),
            ("job.md", job_revision, job_content),
        ):
            if content is None:
                continue
            if not isinstance(revision, str):
                raise ValueError(f"A saved draft is missing for {filename}")
            if not isinstance(content, str) or len(content.encode("utf-8")) > 2_000_000:
                raise ValueError(f"Invalid {filename} content (maximum 2 MB)")
            current = read_text(safe_path(location, filename))
            if digest(current) != revision:
                raise ConflictError(f"{filename} changed outside the editor. Refresh before saving.")
            if current != content:
                pending[filename] = content
        return pending

    def _publish_changes(self, location, pending):
        changes = []
        visible_selected = 0
        labels = {
            "??": "Untracked", "A ": "Added", " A": "Added", "M ": "Modified",
            " M": "Modified", "MM": "Modified", "D ": "Deleted", " D": "Deleted",
        }
        for filename in self.publish_paths():
            status = self._git_process(
                location, "status", "--porcelain=v1", "--untracked-files=all", "--", filename,
            )
            code = status.stdout[:2] if status.stdout else ""
            if code:
                visible_selected += 1
            path = safe_path(location, filename)
            tracked = self._git_process(location, "ls-files", "--error-unmatch", "--", filename)
            if not code and path.is_file() and tracked.returncode:
                code = "??"
            if code or filename in pending:
                changes.append({"path": filename, "status": labels.get(code, "Changed")})
        full = self._git_process(location, "status", "--porcelain=v1", "--untracked-files=all")
        total = len([line for line in full.stdout.splitlines() if line])
        return changes, max(0, total - visible_selected)

    def connection_label(self, location, remote):
        if not remote:
            return None
        value = self._git_process(location, 'remote', 'get-url', remote)
        if value.returncode:
            return 'Connected destination'
        url = value.stdout.strip()
        ssh = re.fullmatch(r'[^@/\s]+@([^:/\s]+):(.+)', url)
        try:
            parts = urlsplit(url)
            host, path = (ssh.group(1), ssh.group(2)) if ssh else (parts.hostname, parts.path)
        except ValueError:
            return 'Connected destination'
        if not host:
            return 'Connected folder' if parts.scheme == 'file' or Path(url).is_absolute() or url.startswith(('.', chr(92))) else 'Connected destination'
        host = {'github.com':'GitHub','gitlab.com':'GitLab','bitbucket.org':'Bitbucket'}.get(host.lower(),host)
        path = path.strip('/').removesuffix('.git')
        return host + (' · ' + path if path else '')

    def _publish_review(self, location, name, pending):
        changes, excluded = self._publish_changes(location, pending)
        remote, remote_branch, upstream, ahead = self._publish_target(location, name)
        fingerprints = []
        for filename in self.publish_paths():
            path = safe_path(location, filename)
            fingerprints.append((filename, hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None))
        review = digest(json.dumps({
            "head": self.head(name), "changes": changes, "files": fingerprints,
            "pending": {key: digest(value) for key, value in pending.items()},
            "remote": remote, "remoteBranch": remote_branch,
        }, sort_keys=True))
        return {
            "branch": name, "remote": remote, "remoteBranch": remote_branch,
            "destination": f"{remote}/{remote_branch}" if remote else None, "destinationLabel": self.connection_label(location, remote),
            "upstream": upstream, "ahead": ahead, "files": changes,
            "excludedChanges": excluded, "pendingWrites": len(pending), "review": review,
        }

    def commit_preview(self, name, source_revision=None, source_content=None,
                       job_revision=None, job_content=None):
        with self.lock:
            self.busy(name)
            if not self.branch(name)["local"]:
                raise ValueError("Create an editable application from this CV before saving and syncing.")
            location = self.location(name, create=True)
            pending = self._pending_writes(
                location, source_revision, source_content, job_revision, job_content,
            )
            return self._publish_review(location, name, pending)

    def commit_and_push(self, name, message, review, source_revision=None, source_content=None,
                        job_revision=None, job_content=None):
        with self.lock:
            self.busy(name)
            self._publishing.add(name)
            self._publish_locks.setdefault(name, threading.Lock())
        try:
            return self._commit_and_push(name, message, review, source_revision, source_content, job_revision, job_content)
        finally:
            with self.lock:
                self._publishing.discard(name)
                if name in self._release_requested:
                    self.release_worktree(name)

    def _commit_and_push(self, name, message, review, source_revision, source_content, job_revision, job_content):
        # A slow network push must not hold the workspace's global lock.
        with self._publish_locks[name]:
            if not self.branch(name)["local"]:
                raise ValueError("Create an editable application from this CV before saving and syncing.")
            location = self.location(name, create=True)
            pending = self._pending_writes(
                location, source_revision, source_content, job_revision, job_content,
            )
            preview = self._publish_review(location, name, pending)
            if not isinstance(review, str) or review != preview["review"]:
                raise ConflictError("This application changed while you were reviewing it. Review the latest changes before saving.")
            if not preview["remote"]:
                raise ValueError("No sync destination is connected. Check your connection setup, then try again.")
            files = [item["path"] for item in preview["files"]]
            commit_created = False
            commit = self.head(name)
            if files:
                if not isinstance(message, str) or not message.strip():
                    raise ValueError("Enter a short note describing your changes.")
                message = message.strip()
                if len(message) > 200 or any(char in message for char in "\r\n\x00"):
                    raise ValueError("Use a one-line change note of 200 characters or fewer.")
                identity = self._git_process(location, "var", "GIT_AUTHOR_IDENT")
                if identity.returncode:
                    raise ValueError("Your name and email are missing from the save settings. Add them before saving a version.")
                for filename, content in pending.items():
                    atomic_write(safe_path(location, filename), content)
                # VITA commonly ignores .vita/, but explicitly reviewed reports
                # are intentional publication inputs for this one commit.
                add = self._git_process(location, "add", "-f", "-A", "--", *files)
                if add.returncode:
                    raise RuntimeError("The selected changes could not be prepared for saving. Your files are safe.")
                created = self._git_process(location, "commit", "--only", "-m", message, "--", *files)
                if created.returncode:
                    raise RuntimeError("A saved version could not be created. Your files are safe; check the application folder and try again.")
                commit_created = True
                commit = self.head(name)
            remote = preview["remote"]
            destination = preview["remoteBranch"]
            push_args = ["push"]
            if not preview["upstream"]:
                push_args.append("--set-upstream")
            push_args.extend((remote, f"refs/heads/{name}:refs/heads/{destination}"))
            pushed = self._git_process(location, *push_args)
            if pushed.returncode:
                output = (pushed.stderr + "\n" + pushed.stdout).lower()
                if "non-fast-forward" in output or "fetch first" in output or "rejected" in output:
                    reason = "The destination did not accept these changes. Check for conflicting updates or save restrictions, then retry syncing."
                elif "authentication" in output or "permission denied" in output or "could not read username" in output:
                    reason = "Sign-in to the sync destination failed. Check your account access and try again."
                else:
                    reason = "Syncing failed. Check your connection and access to the destination, then retry."
                raise PushError(reason, commit_created=commit_created, commit=commit)
            return {
                "branch": name, "destination": f"{remote}/{destination}",
                "commit": commit, "commitCreated": commit_created, "pushed": True,
            }

    def create(self, base, name, job, revision, display_name=None):
        with self.lock:
            if not isinstance(name, str) or name.startswith("-") or not name or name == "HEAD":
                raise ValueError("Choose a valid application name")
            run_git(self.repository, "check-ref-format", "--branch", name)
            if any(b["name"] == name for b in branch_payload(self.repository)["branches"]):
                raise ValueError("An application or saved CV with this name already exists")
            self.busy(base)
            source = self.read(base, self.document_path)
            if digest(source) != revision:
                raise ConflictError("The starting CV changed. Refresh it before creating an application.")
            if not isinstance(job, str) or not job.strip():
                raise ValueError("Add a job description before creating an application")
            commit = self.head(base)
            target = self.root / "worktrees" / digest(name)[:20]
            target.parent.mkdir(parents=True, exist_ok=True)
            run_git(self.repository, "-c", "core.hooksPath=", "worktree", "add", "-b", name, str(target), commit)
            # Preserve the exact viewed CV, including uncommitted edits, in the new workspace.
            atomic_write(safe_path(target, self.document_path), source)
            atomic_write(safe_path(target, "job.md"), job)
            atomic_write(self.metadata_path(name), json.dumps({"baseCommit": commit, "baseBranch": base, "original": source, **({"displayName": display_name} if display_name else {})}))
            return self.snapshot(name)

    def vita_command(self):
        if self.vita_source and (self.vita_source / "vita" / "__main__.py").is_file():
            if self.ai_bridge():
                return [sys.executable, str(Path(__file__).with_name('ai_runner.py'))]
            return [sys.executable, "-m", "vita"]
        executable = shutil.which("vita")
        return [executable] if executable else None

    def ai_bridge(self):
        return bool(self.vita_source and (self.vita_source / 'vita/helpers/llm.py').is_file())

    def providers(self, name):
        from .providers import discover
        return discover(self, name)

    def capabilities(self):
        return {"vita": bool(self.vita_command()), "documentPath": self.document_path,
                "workflow": workflow_capabilities(self.vita_source),
                "engines": [x for x in ("pdflatex", "xelatex", "lualatex") if shutil.which(x)]}

    def start_ai(self, name, revision, job_revision, provider="", language="en", model=None, reasoning="", workflow=None):
        with self.lock:
            if self._closed:
                raise ConflictError("Vita Tree is stopping. Restart it before preparing an application.")
            self.busy(name)
            stages = plan(workflow, workflow_capabilities(self.vita_source))
            selected = {task['id'] for task in stages if task['status'] != 'skipped'}
            uses_ai = bool(selected - {'validating'})
            command = self.vita_command() if uses_ai else []
            if uses_ai and not command:
                raise ValueError("The Vita CV connection is unavailable. Check AI connection details for setup instructions.")
            if self.document_path != "main.tex":
                raise ValueError("The CV source must use the supported main.tex entry. Check your CV collection setup.")
            for value in (provider, language):
                if not isinstance(value, str) or (value and not re.fullmatch(r"[a-zA-Z0-9_.-]{1,64}", value)):
                    raise ValueError("Choose a supported AI service and output language")
            from .providers import resolve
            if uses_ai:
                provider, model, reasoning = resolve(self, name, provider, model, reasoning)
            else:
                provider, model, reasoning = '', None, ''
            location = self.location(name, create=True)
            source, job = self.read(name, self.document_path), self.read(name, "job.md")
            if digest(source) != revision or digest(job) != job_revision:
                raise ConflictError("The CV or job description changed. Refresh before starting the preparation.")
            if uses_ai and not job.strip():
                raise ValueError("Save a job description first")
            ident = uuid.uuid4().hex
            record = {"id": ident, "branch": name, "opportunity": name, "status": "running", "step": "preparing",
                      "message": "Preparing this branch's AI workspace.", "createdAt": time.time(), "startedAt": time.time(),
                      "finishedAt": None, "reviewed": False, "provider": provider, "model": model,
                      "reasoning": reasoning, "language": language, "stages": stages}
            context = self._ai_context(location, source, job, command, provider, model, reasoning)
            config = json.loads(context["config"].get("config.json", "{}"))
            if not isinstance(config, dict):
                raise ValueError("Your AI settings could not be read. Check the configuration in AI connection details.")
            if config.get("tex_entry", "main.tex") != "main.tex":
                raise ValueError("This CV collection needs to use main.tex as its CV source. Check its Vita CV settings.")
            if 'cover' in selected and config.get("cover_tex_entry", "cover-letter.tex") != "cover-letter.tex":
                raise ValueError("This CV collection needs to use cover-letter.tex for cover letters. Check its Vita CV settings.")
            # The UI's explicit choice wins over auto-extraction and stage routing
            # inherited from an exported .env. No credentials are written here.
            context["env"]["ENABLE_JD_EXTRACTION"] = "false"
            for prefix in ("EXTRACTION", "ANALYSIS", "ADAPT", "REVIEW", "COVER"):
                context["env"][prefix + "_PROVIDER"] = provider
                context["env"][prefix + "_MODEL"] = model or ""
            context["baseCommit"] = self.head(name)
            captured = {p: read_text(safe_path(location, p)) for p in (*self.report_paths(), "cover-letter.tex")}
            context["reports"] = {p: digest(content) for p, content in captured.items()}
            context["dependencies"] = reusable_reports(captured, digest(job))
            context["selected"] = selected
            # Preserve each run's inputs before its independent process starts.
            inputs = self.root / "run-inputs" / ident
            atomic_write(inputs / "main.tex", source)
            atomic_write(inputs / "job.md", job)
            self._persist_job(record)
            self.jobs[ident] = record
            self.diagnostics.workflow(record)
            thread = threading.Thread(target=self._run_ai, args=(record, context), daemon=True)
            self._ai_threads.add(thread)
            try:
                thread.start()
            except RuntimeError:
                self._ai_threads.discard(thread)
                self._job_update(record, status="failed", step="failed", finishedAt=time.time(),
                                 message="Couldn’t start the preparation. Close unused programs and try again.",
                                 stages=transition(record["stages"], terminal="failed"))
            return self._public_job(record)

    def _ai_context(self, location, source, job, command, provider, model, reasoning):
        # Capture each independent run's settings at submission.
        # Credentials stay in memory and never enter the public run record.
        env = os.environ.copy()
        env.update(PYTHONIOENCODING="utf-8", VITA_TREE_REASONING=reasoning)
        if self.vita_source:
            env["PYTHONPATH"] = str(self.vita_source) + os.pathsep + env.get("PYTHONPATH", "")
        config, skills = {}, {}
        for origin in (self.repository, location):
            for filename in ("config.json", "extensions.json", "cv.yaml"):
                path = safe_path(origin, ".vita/" + filename)
                if path.is_file():
                    config[filename] = read_text(path)
            for step in REPORTS:
                folder = safe_path(origin, f".vita/skills/{step}")
                for path in folder.glob("*.md"):
                    relative = path.relative_to(origin).as_posix()
                    skills[relative] = read_text(safe_path(origin, relative))
                    if sum(len(value.encode("utf-8")) for value in skills.values()) > 2_000_000:
                        raise ValueError("Project AI skills exceed the 2 MB limit")
            secret = safe_path(origin, ".vita/.env")
            if secret.is_file():
                for line in read_text(secret).splitlines():
                    if "=" in line and not line.lstrip().startswith("#"):
                        key, value = line.split("=", 1)
                        if re.fullmatch(r"[A-Z][A-Z0-9_]*(?:KEY|TOKEN)", key.strip()):
                            env[key.strip()] = value.strip().strip("\"'")
        try:
            extensions = json.loads(config.get("extensions.json", "{}"))
            extensions.setdefault("llm_providers", {})[provider] = {"model": model}
            config["extensions.json"] = json.dumps(extensions)
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Your AI settings could not be read. Check AI connection details.") from None
        return {"location": location, "source": source, "job": job, "command": command, "env": env, "config": config, "skills": skills}

    def _job_update(self, record, **values):
        with self.lock:
            if self._closed:
                return False
            previous = dict(record)
            updated = {**record, **values}
            try:
                self._persist_job(updated)
            except OSError as error:
                if updated['status'] not in {'failed', 'interrupted'}:
                    raise AIRunError('The preparation could not save its status. Check folder access and review the application files before retrying.') from error
                updated['message'] = 'The preparation stopped, but its history could not be saved. Check folder access and review the application before retrying.'
            record.update(updated)
            self.diagnostics.workflow(record, previous)
            return True

    def _run_ai(self, record, context):
        from .pdf import export_snapshot, compile_document
        stage = self.root / "runs" / record["id"]
        location, source, job = (context[key] for key in ("location", "source", "job"))
        try:
            export_snapshot(self.repository, context["baseCommit"], stage, location)
            atomic_write(stage / "main.tex", source)
            atomic_write(stage / "job.md", job)
            for filename, content in context["skills"].items():
                atomic_write(safe_path(stage, filename), content)
            for filename, content in context["config"].items():
                atomic_write(stage / ".vita" / filename, content)
            # Never mistake reports copied from a previous run for this run's outputs.
            for path in self.report_paths():
                safe_path(stage, path).unlink(missing_ok=True)
            safe_path(stage, "cover-letter.tex").unlink(missing_ok=True)
            for path, content in context['dependencies'].items():
                atomic_write(safe_path(stage, path), content)
            for task in record["stages"]:
                step = task["id"]
                if task["status"] == "skipped" or step == "validating":
                    continue
                if not self._job_update(record, step=step, message=MESSAGES[step],
                                        stages=transition(record["stages"], step=step)):
                    return
                args = context["command"] + [step, "--auto"]
                if record["provider"]:
                    args += ["--provider", record["provider"]]
                if step in ("adapt", "cover"):
                    args += ["--language", record["language"]]
                if step == "cover":
                    safe_path(stage, "cover-letter.tex").unlink(missing_ok=True)
                # Retained inputs are context, never evidence that this task ran.
                for filename in REPORTS[step]:
                    safe_path(stage, '.vita/results/' + filename).unlink(missing_ok=True)
                if step == 'analyze':
                    for filename in ('delta.md', 'delta.json'):
                        safe_path(stage, '.vita/results/' + filename).unlink(missing_ok=True)
                process = subprocess.run(args, cwd=stage, env=context["env"], stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
                reports = [read_text(safe_path(stage, ".vita/results/" + name)).strip() for name in REPORTS[step]]
                if process.returncode:
                    self.diagnostics.record('provider_failed', 'ERROR', run_id=record['id'], step=step, exit_code=process.returncode)
                if process.returncode or not any(reports):
                    raise AIRunError(f"Your AI service did not return the expected results. Check the AI connection and try again. Your CV is unchanged.")
                if step == "extract":
                    try:
                        extracted = json.loads(reports[0])
                        if extracted.get("source_sha256") != digest(job) or not reports[1]:
                            raise ValueError("Job mismatch")
                    except (ValueError, AttributeError):
                        raise AIRunError("The job requirements could not be verified against this job description. Your CV is unchanged.") from None
                if step == 'cover':
                    cover_source = read_text(safe_path(stage, 'cover-letter.tex'))
                    if parse_document(cover_source)['error'] or not all(marker in cover_source for marker in (r'\documentclass', r'\begin{document}', r'\end{document}')):
                        raise AIRunError('Your AI service did not produce a valid cover letter. Your application is unchanged; inspect the preparation results.')
                    if not self._job_update(record, message='Compiling the cover-letter PDF…'):
                        return
                    try:
                        output = safe_path(self.root, 'run-pdfs/' + record['id'])
                        built = compile_document(stage, 'cover-letter.tex', output=output)
                        self.diagnostics.record('pdf_compiled', operation='compile_cover', run_id=record['id'], step='cover')
                        atomic_write(output / 'ready.json', json.dumps({'engine': built['engine'], 'warnings': built['warnings']}))
                    except (ValueError, OSError, subprocess.SubprocessError) as error:
                        raise AIRunError('The cover-letter PDF could not be created. Your application is unchanged. Check the PDF tools and packages, inspect the cover-letter source in the preparation results, then retry.') from error
            if not self._job_update(record, step="validating", message=MESSAGES["validating"],
                                    stages=transition(record["stages"], step="validating")):
                return
            cover = None
            if any(t["id"] == "cover" and t["status"] != "skipped" for t in record["stages"]):
                cover = read_text(safe_path(stage, "cover-letter.tex"))
                if parse_document(cover)["error"] or not all(marker in cover for marker in ("\\documentclass", "\\begin{document}", "\\end{document}")):
                    raise AIRunError("Your AI service did not produce a valid cover letter. Your application is unchanged; inspect the preparation results.")
            result = read_text(stage / "main.tex")
            adapting = 'adapt' in context['selected']
            if adapting or context['selected'] == {'validating'}:
                if parse_document(result)["error"] or "\\begin{document}" not in result:
                    raise AIRunError("main.tex is not parseable. Your branch is unchanged; inspect the source in the LaTeX editor.")
            if not adapting and result != source:
                raise AIRunError("This feedback step unexpectedly changed the CV. Your application is unchanged; inspect the preparation results.")
            with self.lock:
                if self._closed:
                    return
                if (self.head(record["branch"]) != context["baseCommit"]
                        or self.location(record["branch"]) != location
                        or self.read(record["branch"], self.document_path) != source
                        or self.read(record["branch"], "job.md") != job
                        or any(digest(read_text(safe_path(location, p))) != value for p, value in context["reports"].items())):
                    raise AIRunError("Your application changed during preparation. The results were kept separately and your edits were preserved.")
                # Store the exact before-AI version for comparison, including prior manual edits.
                if adapting and result != source:
                    meta = self.metadata(record["branch"])
                    meta.update(baseCommit=self.head(record["branch"]), baseBranch=record["branch"] + " · before AI", original=source)
                    atomic_write(self.metadata_path(record["branch"]), json.dumps(meta))
                outputs = {'.vita/results/' + filename for step in context['selected'] if step in REPORTS for filename in REPORTS[step]}
                if 'analyze' in context['selected']:
                    outputs.update(('.vita/results/delta.md', '.vita/results/delta.json'))
                for path in outputs:
                    if safe_path(stage, path).is_file():
                        atomic_write(safe_path(location, path), read_text(safe_path(stage, path)))
                    else:
                        safe_path(location, path).unlink(missing_ok=True)
                if cover is not None:
                    atomic_write(safe_path(location, "cover-letter.tex"), cover)
                if adapting and result != source:
                    atomic_write(safe_path(location, self.document_path), result)
                self._job_update(record, status="succeeded", step="completed", finishedAt=time.time(),
                                 message=("Your changes were checked. Create a PDF preview to check the final layout."
                                          if context['selected'] == {'validating'} else "Cover-letter PDF ready. Open the run to review and save it." if cover is not None else "Selected steps finished. Open the run to review the results."),
                                 stages=transition(record["stages"], terminal="succeeded"))
        except Exception as error:
            self.diagnostics.error('run_error', error, run_id=record['id'], step=record.get('step'))
            # Never persist exception text or provider stdout: either can contain
            # credentials, prompts, source text, or private local paths.
            message = str(error) if isinstance(error, AIRunError) else (
                "The AI service took too long to respond. Check the connection and start again." if isinstance(error, subprocess.TimeoutExpired)
                else "The preparation could not finish. Check your application files and AI connection, then try again.")
            self._job_update(record, status="failed", step="failed", finishedAt=time.time(), message=message,
                             stages=transition(record.get("stages"), terminal="failed"))
        finally:
            with self.lock:
                self._ai_threads.discard(threading.current_thread())
                if record["branch"] in self._release_requested:
                    self.release_worktree(record["branch"])
