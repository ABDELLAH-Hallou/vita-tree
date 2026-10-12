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
import uuid

from .latex import parse_document, replace_leaf
from .server import branch_payload, run_git


class ConflictError(ValueError):
    pass


class PushError(RuntimeError):
    def __init__(self, message, *, commit_created=False, commit=None):
        super().__init__(message)
        self.commit_created = commit_created
        self.commit = commit


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
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(content, encoding="utf-8", newline="")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class Workspace:
    def __init__(self, repository: Path, document_path="main.tex", vita_source: Path | None = None):
        self.repository = repository
        self.document_path = document_path
        safe_path(repository, document_path)
        common = Path(run_git(repository, "rev-parse", "--git-common-dir"))
        self.root = (repository / common).resolve() / "vita-tree"
        self.lock = threading.RLock()
        self.jobs: dict[str, dict] = {}
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
        raise ValueError(f"Unknown branch: {name}")

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
            raise ValueError("Create a local branch from this remote branch before editing.")
        target = self.root / "worktrees" / digest(name)[:20]
        target.parent.mkdir(parents=True, exist_ok=True)
        run_git(self.repository, "-c", "core.hooksPath=", "worktree", "add", str(target), name)
        return target

    def metadata_path(self, name):
        return self.root / "branches" / (digest(name) + ".json")

    def metadata(self, name):
        path = self.metadata_path(name)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def read(self, name, filename):
        location = self.location(name)
        return read_text(safe_path(location, filename)) if location else self.committed(self.head(name), filename)

    def snapshot(self, name):
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
        for label in ("analyze", "adapt", "review"):
            for path in (f".vita/results/{label}.md", f"{label}.md"):
                value = read(path)
                if value:
                    artifacts[label] = {"path": path, "content": value}
                    break
        return {"branch": name, "path": self.document_path, "commit": commit,
                "baseCommit": baseline, "baseBranch": meta.get("baseBranch", name + " · committed"),
                "content": source, "revision": digest(source), "document": parse_document(source),
                "original": original, "originalDocument": parse_document(original),
                "job": job, "jobRevision": digest(job), "artifacts": artifacts,
                "diff": "".join(difflib.unified_diff(original.splitlines(True), source.splitlines(True), fromfile="original/"+self.document_path, tofile=name+"/"+self.document_path)),
                "worktree": str(location) if location else None, "editable": bool(branch["local"]),
                "dirty": source != self.committed(commit, self.document_path),
                "running": next((j for j in self.jobs.values() if j["branch"] == name and j["status"] == "running"), None)}

    def busy(self, name):
        if any(j["branch"] == name and j["status"] == "running" for j in self.jobs.values()):
            raise ConflictError("An AI run is in progress on this branch. Wait before saving.")

    def save(self, name, filename, revision, content=None, leaf=None, text=None):
        if filename not in {self.document_path, "job.md"}:
            raise ValueError("Only the CV and job.md can be edited")
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
            return {"revision": digest(content), "content": content, "path": str(target)}

    def publish_paths(self):
        """Files Vita Tree owns and may include in a UI-created commit."""
        return tuple(dict.fromkeys((
            self.document_path,
            "job.md",
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
                raise ValueError(f"Missing revision for {filename}")
            if not isinstance(content, str) or len(content.encode("utf-8")) > 2_000_000:
                raise ValueError(f"Invalid {filename} content (maximum 2 MB)")
            current = read_text(safe_path(location, filename))
            if digest(current) != revision:
                raise ConflictError(f"{filename} changed outside the editor. Reload before committing.")
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
            "destination": f"{remote}/{remote_branch}" if remote else None,
            "upstream": upstream, "ahead": ahead, "files": changes,
            "excludedChanges": excluded, "pendingWrites": len(pending), "review": review,
        }

    def commit_preview(self, name, source_revision=None, source_content=None,
                       job_revision=None, job_content=None):
        with self.lock:
            self.busy(name)
            if not self.branch(name)["local"]:
                raise ValueError("Create a local branch before committing and pushing.")
            location = self.location(name, create=True)
            pending = self._pending_writes(
                location, source_revision, source_content, job_revision, job_content,
            )
            return self._publish_review(location, name, pending)

    def commit_and_push(self, name, message, review, source_revision=None, source_content=None,
                        job_revision=None, job_content=None):
        with self.lock:
            self.busy(name)
            if not self.branch(name)["local"]:
                raise ValueError("Create a local branch before committing and pushing.")
            location = self.location(name, create=True)
            pending = self._pending_writes(
                location, source_revision, source_content, job_revision, job_content,
            )
            preview = self._publish_review(location, name, pending)
            if not isinstance(review, str) or review != preview["review"]:
                raise ConflictError("The branch changed after review. Review the commit again before publishing.")
            if not preview["remote"]:
                raise ValueError("No Git remote is configured. Add a remote, then try again.")
            files = [item["path"] for item in preview["files"]]
            commit_created = False
            commit = self.head(name)
            if files:
                if not isinstance(message, str) or not message.strip():
                    raise ValueError("Enter a commit message.")
                message = message.strip()
                if len(message) > 200 or any(char in message for char in "\r\n\x00"):
                    raise ValueError("Use a single-line commit message of 200 characters or fewer.")
                identity = self._git_process(location, "var", "GIT_AUTHOR_IDENT")
                if identity.returncode:
                    raise ValueError("Git author name and email are missing. Configure user.name and user.email, then try again.")
                for filename, content in pending.items():
                    atomic_write(safe_path(location, filename), content)
                # VITA commonly ignores .vita/, but explicitly reviewed reports
                # are intentional publication inputs for this one commit.
                add = self._git_process(location, "add", "-f", "-A", "--", *files)
                if add.returncode:
                    raise RuntimeError("Git could not stage the reviewed files. Your files were preserved.")
                created = self._git_process(location, "commit", "--only", "-m", message, "--", *files)
                if created.returncode:
                    raise RuntimeError("Git could not create the commit. Your files were preserved; inspect the worktree and retry.")
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
                    reason = "The remote rejected the push. Fetch and reconcile the remote changes, then retry."
                elif "authentication" in output or "permission denied" in output or "could not read username" in output:
                    reason = "Git authentication failed. Sign in or update your remote credentials, then retry."
                else:
                    reason = "The push failed. Check the remote connection and access, then retry."
                raise PushError(reason, commit_created=commit_created, commit=commit)
            return {
                "branch": name, "destination": f"{remote}/{destination}",
                "commit": commit, "commitCreated": commit_created, "pushed": True,
            }

    def create(self, base, name, job, revision):
        with self.lock:
            if not isinstance(name, str) or name.startswith("-") or not name or name == "HEAD":
                raise ValueError("Choose a valid new branch name")
            run_git(self.repository, "check-ref-format", "--branch", name)
            if any(b["name"] == name for b in branch_payload(self.repository)["branches"]):
                raise ValueError("A branch with this name already exists")
            self.busy(base)
            source = self.read(base, self.document_path)
            if digest(source) != revision:
                raise ConflictError("The base document changed. Reload it before creating a branch.")
            if not isinstance(job, str) or not job.strip():
                raise ValueError("Add a job description before creating a branch")
            commit = self.head(base)
            target = self.root / "worktrees" / digest(name)[:20]
            target.parent.mkdir(parents=True, exist_ok=True)
            run_git(self.repository, "-c", "core.hooksPath=", "worktree", "add", "-b", name, str(target), commit)
            # Preserve the exact viewed CV, including uncommitted edits, in the new workspace.
            atomic_write(safe_path(target, self.document_path), source)
            atomic_write(safe_path(target, "job.md"), job)
            atomic_write(self.metadata_path(name), json.dumps({"baseCommit": commit, "baseBranch": base, "original": source}))
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
                "engines": [x for x in ("pdflatex", "xelatex", "lualatex") if shutil.which(x)]}

    def start_ai(self, name, revision, job_revision, provider="", language="en", model=None, reasoning=""):
        with self.lock:
            self.busy(name)
            command = self.vita_command()
            if not command:
                raise ValueError("VITA CLI not found. Start vt with --vita-source PATH or install vita-cv.")
            if self.document_path != "main.tex":
                raise ValueError("VITA adapt currently requires main.tex at the repository root.")
            for value in (provider, language):
                if not isinstance(value, str) or (value and not re.fullmatch(r"[a-zA-Z0-9_.-]{1,64}", value)):
                    raise ValueError("Invalid provider or language")
            from .providers import resolve
            provider, model, reasoning = resolve(self, name, provider, model, reasoning)
            location = self.location(name, create=True)
            source, job = self.read(name, self.document_path), self.read(name, "job.md")
            if digest(source) != revision or digest(job) != job_revision:
                raise ConflictError("CV or job description changed. Reload before starting AI.")
            if not job.strip():
                raise ValueError("Save a job description first")
            ident = uuid.uuid4().hex
            record = {"id": ident, "branch": name, "status": "running", "step": "analyze", "message": "Analyzing the job description…"}
            self.jobs[ident] = record
            record.update(provider=provider, model=model, reasoning=reasoning)
            threading.Thread(target=self._run_ai, args=(record, location, source, job, command, provider, language, model, reasoning), daemon=True).start()
            return dict(record)

    def _run_ai(self, record, location, source, job, command, provider, language, model, reasoning):
        # Run in a separate snapshot: a failed/partial AI result never overwrites the CV.
        from .pdf import export_snapshot
        stage = self.root / "runs" / record["id"]
        try:
            export_snapshot(self.repository, self.head(record["branch"]), stage, location)
            atomic_write(stage / "main.tex", source)
            atomic_write(stage / "job.md", job)
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env['VITA_TREE_REASONING'] = reasoning
            if self.vita_source:
                env["PYTHONPATH"] = str(self.vita_source) + os.pathsep + env.get("PYTHONPATH", "")
            # VITA's configuration is local/ignored. Copy only configuration/context,
            # and supply keys in child-process memory, never through the API or log.
            for origin in (self.repository, location):
                for filename in ("config.json", "extensions.json", "cv.yaml"):
                    path = safe_path(origin, ".vita/" + filename)
                    if path.is_file():
                        atomic_write(stage / ".vita" / filename, read_text(path))
                secret = safe_path(origin, ".vita/.env")
                if secret.is_file():
                    for line in read_text(secret).splitlines():
                        if "=" in line and not line.lstrip().startswith("#"):
                            key, value = line.split("=", 1)
                            if re.fullmatch(r"[A-Z][A-Z0-9_]*(?:KEY|TOKEN)", key.strip()):
                                env[key.strip()] = value.strip().strip("\"'")
            # Override only this run's configuration. Cross-branch choices must
            # work even when absent from the selected branch's provider mapping.
            extensions_path = stage / '.vita/extensions.json'
            extensions = json.loads(read_text(extensions_path) or '{}')
            extensions.setdefault('llm_providers', {})[provider] = {'model': model}
            atomic_write(extensions_path, json.dumps(extensions))
            for step in ("analyze", "adapt"):
                with self.lock:
                    record.update(step=step, message="Analyzing the job description…" if step == "analyze" else "Adapting the CV…")
                artifact = stage / ".vita/results" / f"{step}.md"
                artifact.unlink(missing_ok=True)
                args = command + [step, "--auto"]
                if provider:
                    args += ["--provider", provider]
                if step == "adapt":
                    args += ["--language", language]
                process = subprocess.run(args, cwd=stage, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=600)
                if process.returncode or not artifact.is_file() or not read_text(artifact).strip():
                    raise ValueError(f"VITA {step} did not produce a report. Check provider configuration and authentication. Your CV is unchanged.")
            result = read_text(stage / "main.tex")
            parsed = parse_document(result)
            if result == source or parsed["error"] or "\\begin{document}" not in result:
                raise ValueError("VITA did not produce a changed, parseable main.tex. Your CV is unchanged; inspect the run files.")
            with self.lock:
                if self.read(record["branch"], self.document_path) != source or self.read(record["branch"], "job.md") != job:
                    raise ConflictError("Files changed during AI execution. Result retained in the run folder; your edits were preserved.")
                # Store the exact before-AI version for comparison, including prior manual edits.
                meta = self.metadata(record["branch"])
                meta.update(baseCommit=self.head(record["branch"]), baseBranch=record["branch"] + " · before AI", original=source)
                atomic_write(self.metadata_path(record["branch"]), json.dumps(meta))
                for step in ("analyze", "adapt"):
                    atomic_write(safe_path(location, f".vita/results/{step}.md"), read_text(stage / f".vita/results/{step}.md"))
                atomic_write(safe_path(location, self.document_path), result)
                record.update(status="succeeded", message="Analysis and adapted CV are ready to review.", runPath=str(stage))
        except Exception as error:
            with self.lock:
                record.update(status="failed", message=str(error), runPath=str(stage))
