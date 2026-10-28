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
from .execution import ExecutionInspector
from .latex import parse_document, replace_leaf
from .workflow import REPORTS, MESSAGES, capabilities as workflow_capabilities, plan, transition, clean_stages, reusable_reports
from .server import branch_payload, run_git, git_document
from . import checkpoints
from . import factual_review
from . import requirements_review
from .outcomes import read_outcome
from .provider_status import failure
from .resume_inputs import capture as capture_resume_inputs
from .publication import publish, recover as recover_publications
from .ai_config import Connections, clean_settings, effective_settings, stage_environment
from .security import credential_name, scrub_generated
from . import preflight
from . import includes


class ConflictError(ValueError):
    pass


class PushError(RuntimeError):
    def __init__(self, message, *, commit_created=False, commit=None):
        super().__init__(message)
        self.commit_created = commit_created
        self.commit = commit


class AIRunError(ValueError):
    """A fixed, user-facing message safe to expose in the global runs list."""

class PreparationConflict(AIRunError):
    pass


def digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def safe_path(root: Path, name: str) -> Path:
    path = PurePosixPath(name)
    if not name or not path.parts or "\x00" in name or path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name or path.parts[0].lower() == ".git":
        raise ValueError("Invalid repository-relative path")
    target = root.joinpath(*path.parts)
    for parent in [target, *target.parents]:
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda:False)():
            raise ValueError("Symlink paths are not supported")
        if parent == root:
            break
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
        self._history_lock = threading.Lock()
        self._history_read = None
        self.connections = Connections()
        self.jobs: dict[str, dict] = {}
        self._ai_threads = set()
        from .processes import ProcessRegistry
        self.processes = ProcessRegistry()
        self._closed = False
        self._publishing = set()
        self._previewing = {}
        self._setup_checks = set()
        self._release_requested = set()
        self._publish_locks = {}
        self._pending_publications = set()
        recover_publications(self)
        self._load_jobs()
        try:
            self.cleanup_checkpoints()
        except OSError as error:
            self.diagnostics.error('checkpoint_cleanup_failed', error, operation='checkpoints')
        self.vita_source = vita_source
        if self.vita_source is None:
            try:
                # The optional [ai] extra installs VITA in this interpreter, so
                # pipx/uv users get the same bridge as --vita-source users.
                self.vita_source = Path(distribution('vita-cv').locate_file('')).resolve()
            except PackageNotFoundError:
                pass
        self.inspector = ExecutionInspector(self)
        for record in self.jobs.values():
            if record['status'] == 'interrupted':
                self.inspector.mark(record, 'recovery', 'interrupted')
                self.inspector.finish(record)

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

    def create_application(self, base, label, job, revision, project_revision=None):
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
            return self.create(base, name, job, revision, display_name=label, project_revision=project_revision)

    def save_state(self, name, location):
        draft = bool(location and run_git(location, 'status', '--porcelain', '--untracked-files=all', '--ignored', '--', *self.publish_paths(location)))
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
            return git_document(self.repository, commit, filename)
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
        project = includes.project(self, name)
        if project['files'].get(self.document_path, source) != source:
            raise ConflictError('The CV changed while loading its files. Reload the application.')
        before = includes.project(self, name, commit=baseline,
                                  originals={self.document_path: original, **meta.get('originalFiles', {})})
        files = []
        for path in dict.fromkeys([self.document_path, *project['files'], *before['files']]):
            current, previous = project['files'].get(path), before['files'].get(path)
            files.append(dict(path=path, content=current or '', original=previous or '',
                              revision=digest(current or ''), exists=current is not None,
                              originalExists=previous is not None,
                              document=parse_document(current or '', path),
                              originalDocument=parse_document(previous or '', path),
                              diff=''.join(difflib.unified_diff((previous or '').splitlines(True), (current or '').splitlines(True), fromfile='original/'+path, tofile=name+'/'+path))))
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
                "content": source, "revision": digest(source), "document": parse_document(source, self.document_path),
                "original": original, "originalDocument": parse_document(original, self.document_path),
                "files": files, "projectRevision": project['revision'], "originalProjectRevision": before['revision'], "includeDiagnostics": project['diagnostics'],
                "job": job, "jobRevision": digest(job), "artifacts": artifacts, "cover": read("cover-letter.tex"),
                "diff": "".join(difflib.unified_diff(original.splitlines(True), source.splitlines(True), fromfile="original/"+self.document_path, tofile=name+"/"+self.document_path)),
                "worktree": str(location) if location else None, "editable": bool(branch["local"]),
                "dirty": source != self.committed(commit, self.document_path),
                "running": self.active_job(name)}

    JOB_FIELDS = ("id", "branch", "opportunity", "status", "step", "message", "provider", "model",
                  "reasoning", "language", "createdAt", "startedAt", "finishedAt", "reviewed", "stages", "stepConfig", "parentRunId", "rootRunId", "attempt", "checkpointSteps", "outcomes", "traceId", "requirementsRevision", "requirementsDraft", "preflight", "compileEngine", "reviewPolicy")
    ACTIVE_STATUSES = {"queued", "running"}

    def _job_secrets(self):
        return [item['key'] for item in self.connections.items.values()] + list(getattr(getattr(self, 'inspector', None), 'secrets', ()))

    def _public_job(self, record, *, parents=None, secrets=None, factuals=None, requirements=None):
        result = {key: record.get(key) for key in self.JOB_FIELDS}
        result['reviewPolicy'] = 'automatic' if record.get('reviewPolicy') == 'automatic' else 'manual'
        start = record.get("startedAt")
        result["elapsedSeconds"] = max(0, (record.get("finishedAt") or time.time()) - start) if start else 0
        result['resumeAvailable'] = record.get('status') in {'failed', 'interrupted'} and bool(record.get('attempt'))
        result['checkpointSteps'] = [step for step in record.get('checkpointSteps') or []
                                     if (self.root/'checkpoints'/record['id']/step/'manifest.json').is_file()]
        parent = (self.jobs if parents is None else parents).get(record.get('parentRunId'))
        route_fields = ('provider','model','reasoning','connection')
        route_values = lambda item: {step: {k: route.get(k) for k in route_fields} for step, route in (item.get('stepConfig') or {}).items()}
        result['configurationChanged'] = bool(parent and (route_values(record) != route_values(parent) or record.get('language') != parent.get('language')))
        if secrets is None:
            secrets = self._job_secrets()
        result['preflight'] = preflight.public_result(record.get('preflight'), secrets)
        result['outcomes'] = self._safe_outcomes(record.get('outcomes'), secrets)
        result['failures'] = {step: info for step, outcome in result['outcomes'].items()
                              if (info := failure(outcome))}
        result['factualReview'] = factual_review.summary(self, record['id']) if factuals is None else factuals.get(record['id'])
        if record.get('requirementsRevision'):
            result['requirementsStatus'] = requirements_review.run_status(self, record) if requirements is None else requirements.get(record['id'],'unavailable')
        if record.get('requirementsDraft'):
            try:
                with self.lock:
                    review = requirements_review.state(self, requirements_review.context_for(self, record['branch']))
                result['requirementsApprovalNeeded'] = review['state'] != 'approved'
            except (OSError, ValueError):
                result['requirementsApprovalNeeded'] = True
            result['resumeAvailable'] = result['resumeAvailable'] and not result['requirementsApprovalNeeded']
        if result['factualReview']:
            pending = result['factualReview']['state'] != 'resolved'
            result['resumeAvailable'] = result['resumeAvailable'] and not pending
            if not pending and (self.root/'checkpoints'/record['id']/result['factualReview']['step']/'manifest.json').is_file():
                result['checkpointSteps'] = list(dict.fromkeys([*result['checkpointSteps'], result['factualReview']['step']]))
            result['message'] = ('Review the proposed factual changes before continuing. Your application is unchanged.' if pending else
                                 'Factual decisions saved in the preparation draft. Retry to continue with matching inputs and publish after final checks.')
            if result['factualReview']['state'] == 'unavailable':
                result['message'] = 'Factual-review evidence is unavailable or damaged. Start a new preparation; your application is unchanged.'
        return result

    def cleanup_checkpoints(self):
        with self.lock:
            return checkpoints.cleanup(self.root/'checkpoints', self.jobs)

    def resume_ai(self, ident, revision, job_revision, ai_config=None, language=None, token=None, preview=False):
        with self.lock:
            parent = self.jobs.get(ident)
            if not parent or parent.get('status') not in {'failed', 'interrupted'} or not parent.get('attempt'):
                raise ConflictError('Select a failed or interrupted preparation to retry.')
            if (factual_review.summary(self, ident) or {}).get('state') in {'pending', 'unavailable'}:
                raise ConflictError('Review and resolve the factual changes before retrying this preparation.')
            steps = [stage['id'] for stage in parent['stages'] if stage['status'] != 'skipped']
            captured_origins = None
            if ai_config is None:
                prior_origins = self.inspector.read_tree(parent).get('configuration',{})
                captured_origins = {step: prior_origins.get(step,{}).get('origin','captured') for step in parent.get('stepConfig') or {}}
                routes = parent.get('stepConfig') or {}
                clean = {step: {key: value for key, value in route.items() if key in {'provider','model','reasoning','connection'}}
                         for step, route in routes.items()}
                ai_config = {'default': next(iter(clean.values()), {}), 'steps': clean}
            return self.start_ai(parent['branch'], revision, job_revision, language=language or parent['language'],
                                 workflow={'steps': steps}, ai_config=ai_config, resume_from=ident,
                                 resume_token=token, preview_only=preview, captured_origins=captured_origins,
                                 engine=parent.get('compileEngine') or 'auto', review_policy=parent.get('reviewPolicy') or 'manual')

    def continue_review(self, ident, revision, job_revision):
        """Continue an approved draft exactly once, using its captured setup."""
        with self.lock:
            parent = self.jobs.get(ident)
            if not parent:
                raise ValueError('This preparation is unavailable.')
            children = [job for job in self.jobs.values() if job.get('parentRunId') == ident]
            if children:
                return self._public_job(max(children, key=lambda job: job['createdAt']))
            review = factual_review.summary(self, ident)
            if not review and not parent.get('requirementsDraft'):
                raise ConflictError('This preparation is not waiting for approval. Use Retry to inspect its recovery plan.')
            preview = self.resume_ai(ident, revision, job_revision, preview=True)
            if review and (review['state'] != 'resolved' or review['step'] not in preview['reuse']):
                raise ConflictError('The approved draft no longer matches the captured inputs. Your decisions are saved; use Retry to inspect what changed.')
            return self.resume_ai(ident, revision, job_revision, token=preview['token'])

    def _automatic_review(self, record):
        """An explicitly selected policy uses the same review and checkpoint gates."""
        with self.lock:
            if self._closed or record.get('reviewPolicy') != 'automatic' or record['status'] != 'failed':
                return
            facts = factual_review.summary(self, record['id'])
            if facts and facts['state'] == 'pending':
                review = factual_review.view(self, record['id'])
                factual_review.apply(self, record['id'], review['revision'], review['token'],
                                     [{'id': item['id'], 'action': 'accept'} for item in review['items']], True,
                                     automatic=True)
            elif record.get('requirementsDraft'):
                review = requirements_review.view(self, record['branch'])
                if review['state'] != 'pending' or review['revision'] != record['requirementsDraft']:
                    return
                requirements_review.change(self, record['branch'], review['token'], review['revision'],
                                           approve=True, confirmed=True, automatic=True)
            else:
                return  # Provider, compilation and conflict failures never auto-retry.
            self.continue_review(record['id'], digest(self.read(record['branch'], 'main.tex')),
                                 digest(self.read(record['branch'], 'job.md')))

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
                record['reviewPolicy'] = 'automatic' if record.get('reviewPolicy') == 'automatic' else 'manual'
                record["stages"] = clean_stages(record.get("stages"))
                # History is public: whitelist route fields even in hand-edited files.
                routes = record.get('stepConfig')
                record['stepConfig'] = {step: {key: value for key, value in route.items()
                                              if key in {'provider', 'model', 'reasoning', 'connection', 'connectionName'} and isinstance(value, str)}
                                        for step, route in routes.items() if step in REPORTS and isinstance(route, dict)} if isinstance(routes, dict) else {}
                for field in ('parentRunId', 'rootRunId', 'traceId'):
                    value = record.get(field)
                    record[field] = value if isinstance(value, str) and re.fullmatch(r'[a-f0-9]{32}', value) else None
                for field in ('requirementsRevision', 'requirementsDraft'):
                    value = record.get(field)
                    record[field] = value if isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}', value) else None
                attempt = record.get('attempt')
                record['attempt'] = attempt if type(attempt) is int and 1 <= attempt <= 100 else None
                record['checkpointSteps'] = [step for step in record.get('checkpointSteps') or [] if step in REPORTS]
                record['outcomes'] = self._safe_outcomes(record.get('outcomes'))
                record['preflight'] = preflight.public_result(record.get('preflight'))
                record['compileEngine'] = record.get('compileEngine') if record.get('compileEngine') in preflight.ENGINES else 'auto'
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

    @staticmethod
    def _safe_outcomes(values, secrets=()):
        from .outcomes import safe_outcome
        result = {}
        if isinstance(values, dict):
            for step, value in values.items():
                if step not in REPORTS or not isinstance(value, dict):
                    continue
                native = value.get('backend')
                if not isinstance(native, dict):
                    native = None
                if isinstance(native, dict):
                    native = safe_outcome({'schema_version': 1, 'status': native.get('status'),
                                           'attempts': native.get('attempts'), 'run_id': native.get('backendRunId'),
                                           'error': {**(native.get('providerError') or {}), **(native.get('errorDetails') if isinstance(native.get('errorDetails'),dict) else {}), 'code': native.get('errorCode')}}, secrets)
                result[step] = {'status': value.get('status') if value.get('status') in {'success','failed'} else 'failed',
                                'verified': value.get('verified') is True, 'backend': native}
        return result

    def list_jobs(self):
        from copy import deepcopy
        # Overlapping readers share one in-flight refresh. The result is not
        # cached after completion: the next new request reads review files
        # again. Never hold the orchestration lock while a reader is waiting.
        with self._history_lock:
            refresh = self._history_read
            leader = refresh is None
            if leader:
                refresh = {'ready': threading.Event(), 'result': None, 'failed': False}
                self._history_read = refresh
        if not leader:
            if not refresh['ready'].wait(timeout=30) or refresh['failed']:
                raise RuntimeError('Preparation history could not be refreshed. Try refreshing again.')
            return deepcopy(refresh['result'])
        try:
            result = self._list_jobs()
            refresh['result'] = result
            return deepcopy(result)
        except BaseException:
            refresh['failed'] = True
            raise
        finally:
            with self._history_lock:
                self._history_read = None
                refresh['ready'].set()

    def _list_jobs(self):
        from copy import deepcopy
        with self.lock:
            # Capture mutable records and redaction context together. Formatting
            # thousands of file-backed review statuses must not starve workers,
            # draft saves or new submissions that need the workspace lock.
            records = deepcopy(list(self.jobs.values()))
            secrets = self._job_secrets()
        parents = {record['id']: record for record in records}
        factuals = factual_review.summaries(self, parents)
        requirements = requirements_review.run_statuses(self, records)
        return {"runs": [self._public_job(record, parents=parents, secrets=secrets, factuals=factuals, requirements=requirements)
                         for record in sorted(records, key=lambda item: item.get('createdAt') or 0, reverse=True)]}

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
        review = factual_review.summary(self, ident)
        if review and review['state'] == 'resolved':
            saved = checkpoints.load_checkpoint(self.root/'checkpoints', ident, review['step'])
            if saved:
                files.update({name: content for name, content in saved[1].items() if content is not None})
        original = safe_path(self.root / "run-inputs" / record["id"], "main.tex")
        if original.is_file():
            files["original/main.tex"] = read_text(original)
        skipped = {task['id'] for task in record.get('stages') or [] if task['status'] == 'skipped'}
        inputs = {'job.md', 'original/main.tex'}
        if 'adapt' in skipped:
            inputs.add('main.tex')
        inputs.update('.vita/results/' + filename for step in skipped if step in REPORTS for filename in REPORTS[step])
        root_id = record.get('rootRunId') or ident
        attempts = [self._public_job(item) for item in self.jobs.values()
                    if (item.get('rootRunId') or item['id']) == root_id]
        return {"run": record, "files": files, "attemptHistory": sorted(attempts, key=lambda item: item.get('createdAt') or 0), "inputs": sorted(inputs & files.keys()),
                "coverPdf": {"runId": ident} if self.cover_pdf_result(ident) else None}

    def active_job(self, name):
        with self.lock:
            return next((self._public_job(j) for j in self.jobs.values()
                         if j["branch"] == name and j["status"] in self.ACTIVE_STATUSES), None)

    def close(self):
        with self.lock:
            self.connections.items.clear()
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

            workers = list(self._ai_threads)

        # Mark records interrupted before cancelling their process trees so a
        # racing worker cannot publish or turn shutdown into a provider failure.
        self.processes.close()
        # Allow cancelled workers to clear captured keys and finish cleanup
        # before the same workspace is reopened. Never join under its lock.
        deadline = time.monotonic() + 5
        for worker in workers:
            if worker is not threading.current_thread():
                worker.join(timeout=max(0, deadline - time.monotonic()))

    def busy(self, name):
        if name in self._pending_publications:
            raise ConflictError('Publication recovery is pending for this application. Check folder access and restart Vita Tree before editing or retrying.')
        if self.active_job(name):
            raise ConflictError("This application is being prepared. Wait before changing its files.")
        if name in self._publishing:
            raise ConflictError("This application is being saved and synced. Wait before changing it.")

    def save(self, name, filename, revision, content=None, leaf=None, text=None, project_revision=None):
        with self.lock:
            self.busy(name)
            graph = includes.project(self, name)
            if ((filename not in {self.document_path, 'job.md'} and not project_revision)
                    or (project_revision is not None and project_revision != graph['revision'])):
                raise ConflictError('The CV files or include dependencies changed outside the editor. Copy your edits, then reload before saving.')
            if filename not in {self.document_path, 'job.md'} and filename not in graph['files']:
                raise ValueError('Only the CV, its supported local includes and job description can be edited here. Reload the CV file list.')
            location = self.location(name, create=True)
            target = safe_path(location, filename)
            current = read_text(target)
            if digest(current) != revision:
                raise ConflictError("This file changed outside the editor. Copy your edits, then reload before saving.")
            if leaf is not None:
                if filename == 'job.md' or not isinstance(text, str):
                    raise ValueError("Invalid structured edit")
                content = replace_leaf(current, str(leaf), text)
            if not isinstance(content, str) or len(content.encode("utf-8")) > 2_000_000:
                raise ValueError("Invalid file content (maximum 2 MB)")
            atomic_write(target, content)
            return {"revision": digest(content), "content": content, "path": str(target), "saveState": self.save_state(name, location)}

    @staticmethod
    def report_paths():
        return (*dict.fromkeys(".vita/results/" + file for files in REPORTS.values() for file in files), *checkpoints.FACTUAL_ARTIFACTS)

    def publish_paths(self, location=None, pending=None):
        """Files Vita Tree owns and may include in a UI-created commit."""
        graph = includes.local(location, self.document_path, pending) if location else {'files':{},'diagnostics':[]}
        sources = [*graph['files'], *(item['path'] for item in graph['diagnostics'] if item['code']=='missing')]
        return tuple(dict.fromkeys((
            self.document_path,
            *sources,
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
        for filename in self.publish_paths(location, pending):
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
        for filename in self.publish_paths(location, pending):
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

    def create(self, base, name, job, revision, display_name=None, project_revision=None):
        with self.lock:
            if not isinstance(name, str) or name.startswith("-") or not name or name == "HEAD":
                raise ValueError("Choose a valid application name")
            run_git(self.repository, "check-ref-format", "--branch", name)
            if any(b["name"] == name for b in branch_payload(self.repository)["branches"]):
                raise ValueError("An application or saved CV with this name already exists")
            self.busy(base)
            source = self.read(base, self.document_path)
            project = includes.project(self, base)
            if project['files'].get(self.document_path, source) != source:
                raise ConflictError('The starting CV changed while capturing its includes. Reload before creating an application.')
            if project_revision is not None and project_revision != project['revision']:
                raise ConflictError('The starting CV includes changed. Reload before creating an application.')
            if digest(source) != revision:
                raise ConflictError("The starting CV changed. Refresh it before creating an application.")
            if not isinstance(job, str) or not job.strip():
                raise ValueError("Add a job description before creating an application")
            commit = self.head(base)
            target = self.root / "worktrees" / digest(name)[:20]
            target.parent.mkdir(parents=True, exist_ok=True)
            run_git(self.repository, "-c", "core.hooksPath=", "worktree", "add", "-b", name, str(target), commit)
            # Preserve the exact viewed CV, including uncommitted edits, in the new workspace.
            for path, content in {self.document_path: source, **project['files']}.items():
                destination = safe_path(target, path)
                if not destination.is_file() or read_text(destination) != content:
                    atomic_write(destination, content)
            missing = {item['path']: None for item in project['diagnostics'] if item['code'] == 'missing'}
            for path in missing:
                safe_path(target, path).unlink(missing_ok=True)
            atomic_write(safe_path(target, "job.md"), job)
            atomic_write(self.metadata_path(name), json.dumps({"baseCommit": commit, "baseBranch": base, "original": source, "originalFiles": {**project['files'], **missing}, **({"displayName": display_name} if display_name else {})}))
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

    def list_connections(self):
        with self.lock:
            return {'connections': self.connections.list()}

    def add_connection(self, name, provider, api_key):
        with self.lock:
            return self.connections.add(name, provider, api_key)

    def remove_connection(self, ident):
        with self.lock:
            self.connections.remove(ident)
            return self.list_connections()

    def ai_settings(self, name):
        self.branch(name)
        path = self.root / 'ai-settings' / (digest(name) + '.json')
        try:
            return clean_settings(self, name, json.loads(read_text(path)))
        except (ValueError, TypeError):
            return clean_settings(self, name, {})

    def save_ai_settings(self, name, settings):
        with self.lock:
            self.branch(name)
            clean = clean_settings(self, name, settings)
            atomic_write(self.root / 'ai-settings' / (digest(name) + '.json'), json.dumps(clean))
            return clean

    def check_generation(self, name, step, settings, confirmed=False):
        from .generation_check import run
        return run(self, name, step, settings, confirmed)

    def factual_review(self, ident):
        return factual_review.view(self, ident)

    def save_requirements(self, branch, token, revision, items):
        return requirements_review.change(self, branch, token, revision, items)

    def approve_requirements(self, branch, token, revision, confirmed=False):
        return requirements_review.change(self, branch, token, revision, approve=True, confirmed=confirmed)

    def apply_factual_review(self, ident, revision, token, decisions, confirmed=False):
        return factual_review.apply(self, ident, revision, token, decisions, confirmed)

    def capabilities(self):
        return {"vita": bool(self.vita_command()), "documentPath": self.document_path,
                "workflow": workflow_capabilities(self.vita_source),
                "engines": [x for x in ("pdflatex", "xelatex", "lualatex") if shutil.which(x)]}

    def check_setup(self, name, revision=None, job_revision=None, engine='auto', workflow=None):
        selected = {task['id'] for task in plan(workflow, workflow_capabilities(self.vita_source)) if task['status'] != 'skipped'}
        return preflight.check_workspace(self, name, revision, job_revision, engine, selected)

    def start_ai(self, name, revision, job_revision, provider="", language="en", model=None, reasoning="", workflow=None, ai_config=None, resume_from=None, resume_token=None, preview_only=False, captured_origins=None, engine='auto', review_policy='manual'):
        with self.lock:
            if self._closed:
                raise ConflictError("Vita Tree is stopping. Restart it before preparing an application.")
            self.busy(name)
            if review_policy not in ('manual', 'automatic'):
                raise ValueError('Choose review before continuing or automatic preparation.')
            if not isinstance(engine,str) or engine not in preflight.ENGINES:
                raise ValueError('Choose a supported TeX engine for setup checks.')
            if resume_from and (factual_review.summary(self, resume_from) or {}).get('state') in {'pending', 'unavailable'}:
                raise ConflictError('Resolve the factual changes before retrying this preparation.')
            self.cleanup_checkpoints()
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
            if uses_ai:
                settings = clean_settings(self, name, ai_config if ai_config is not None else {
                    'default': {'provider': provider, 'model': model, 'reasoning': reasoning}})
                provider, model, reasoning = (settings['default'][key] for key in ('provider', 'model', 'reasoning'))
                routes = effective_settings(settings, selected)
                # Snapshot keys before the worker starts. Removing a connection cannot
                # change a submitted run, and one step's key never replaces another's.
                keys = {step: self.connections.get(route['connection'], route['provider'])
                        for step, route in routes.items() if route['connection']}
                names = {item['id']: item['name'] for item in self.connections.list()}
                for route in routes.values():
                    route['connectionName'] = names.get(route['connection']) or ('Local Codex login' if route['provider'] == 'codex' else 'Existing local credentials')
            else:
                provider, model, reasoning = '', None, ''
                routes, keys = {}, {}
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
                      "reasoning": reasoning, "language": language, "stages": stages, "stepConfig": routes,
                      "parentRunId": resume_from, "rootRunId": self.jobs[resume_from].get('rootRunId') or resume_from if resume_from else ident,
                      "attempt": (self.jobs[resume_from].get('attempt') or 1) + 1 if resume_from else 1,
                      "checkpointSteps": [], "outcomes": {},
                      "traceId": (self.jobs[resume_from].get("traceId") or self.jobs[resume_from].get("rootRunId") or resume_from) if resume_from else ident,
                      "compileEngine": engine, "preflight": None, "reviewPolicy": review_policy}
            if resume_from:
                record['attempt'] = max((item.get('attempt') or 1 for item in self.jobs.values() if item.get('rootRunId') == record['rootRunId']), default=0) + 1
            context = self._ai_context(location, source, job, command, provider, model, reasoning)
            context['stepConfig'], context['keys'] = routes, keys
            context['compileEngine'] = engine
            config = json.loads(context["config"].get("config.json", "{}"))
            if not isinstance(config, dict):
                raise ValueError("Your AI settings could not be read. Check the configuration in AI connection details.")
            if config.get("tex_entry", "main.tex") != "main.tex":
                raise ValueError("This CV collection needs to use main.tex as its CV source. Check its Vita CV settings.")
            if 'cover' in selected and config.get("cover_tex_entry", "cover-letter.tex") != "cover-letter.tex":
                raise ValueError("This CV collection needs to use cover-letter.tex for cover letters. Check its Vita CV settings.")
            context["baseCommit"] = self.head(name)
            captured = {p: read_text(safe_path(location, p)) for p in (*self.report_paths(), "cover-letter.tex")}
            context['coverBefore'] = captured['cover-letter.tex'] if context['factualBackend'] and safe_path(location, 'cover-letter.tex').is_file() else None
            context["reports"] = {p: digest(content) for p, content in captured.items()}
            context["dependencies"] = reusable_reports(captured, digest(job))
            context["selected"] = selected
            if record['attempt'] > 100:
                raise ValueError('This preparation has reached 100 attempts. Start a new preparation.')
            if context['requirementsBackend'] and selected - {'validating'}:
                review = requirements_review.state(self, context)
                if review['state'] == 'approved':
                    data = requirements_review.definition(self, context, review['approvedRevision'])
                    context['requirementsRevision'] = record['requirementsRevision'] = data['revision']
                elif selected - {'extract', 'validating'} and 'extract' not in selected:
                    raise ValueError('Run Extract, then review and approve the job requirements before starting dependent steps.')
                if review['state'] == 'pending':
                    record['requirementsDraft'] = review['revision']
                    raise ValueError('A job definition is awaiting review. Open requirements from Extract and approve it before continuing.')
                # Old assessments are never context for a different definition.
                context['dependencies'] = reusable_reports(captured, digest(job), context.get('requirementsRevision'))
            capture_resume_inputs(self, context, record)
            if context['requirementsBackend'] and selected - {'validating'}:
                pointer = context['criteria'].get('approved/'+digest(job)+'.json')
                captured_revision = json.loads(pointer)['revision'] if pointer else None
                if review['token'] != context['requirementsToken'] or captured_revision != context.get('requirementsRevision'):
                    raise ConflictError('The requirement approval changed while capturing inputs. Review requirements and try again.')
            context['resume'] = checkpoints.resume_plan(self.root/'checkpoints', resume_from, context) if resume_from else {'reuse': [], 'rerun': [], 'checkpoints': {}}
            if resume_from:
                preview = {key: context['resume'][key] for key in ('reuse', 'rerun')}
                preview.update(parentRunId=resume_from, attempt=record['attempt'],
                               token=checkpoints.fingerprint({'inputs': context['checkpointInputs'],
                                    'credentials': context['credentialHashes'], 'routes': routes, 'skills': context['stepSkills'],
                                    'parentRunId': resume_from, 'attempt': record['attempt'],
                                    'initial': context['initialArtifacts'], 'resume': preview,
                                    'baseCommit': context['baseCommit'], 'reports': context['reports']}))
                if preview_only:
                    context['keys'].clear()
                    return preview
                if not resume_token or resume_token != preview['token']:
                    raise ConflictError('The resume plan changed. Review the retry plan again before starting.')

            # Preserve each run's inputs before its independent process starts.
            if context.get('requirementsRevision'):
                requirements_review.retain_run(self, record, context, data)
            inputs = self.root / "run-inputs" / ident
            atomic_write(inputs / "main.tex", source)
            atomic_write(inputs / "job.md", job)
            self._persist_job(record)
            self.jobs[ident] = record
            origins = {step: ('step_override' if step in settings['steps'] else 'shared') for step in routes} if uses_ai else {}
            if captured_origins is not None:
                origins.update(captured_origins)
            self.inspector.begin(record, context, origins)
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
            for filename in ("config.json", "extensions.json", "cv.yaml", "cv-verified.json", "requirements-state.json"):
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
                        if re.fullmatch(r"[A-Z][A-Z0-9_]*(?:KEY|TOKEN|BASE_URL|ENDPOINT)", key.strip()) or key.strip() == "VITA_REQUIREMENTS_DIR":
                            env[key.strip()] = value.strip().strip("\"'")
        malformed = next((item for item in preflight.configuration(config, self.document_path) if item['code']=='configuration_invalid'), None)
        if malformed:
            raise ValueError('Project settings in .vita/' + malformed['target'] + ' are invalid. Open Check setup for guidance; no files were rewritten.')
        try:
            extensions = json.loads(config.get("extensions.json", "{}"))
            if provider:
                extensions.setdefault("llm_providers", {})[provider] = {"model": model}
            config["extensions.json"] = json.dumps(extensions)
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Your AI settings could not be read. Check AI connection details.") from None
        return {"location": location, "source": source, "job": job, "command": command, "env": env, "config": config, "skills": skills,
                'factualBackend': bool(self.vita_source and (self.vita_source/'vita/helpers/factual_changes.py').is_file()),
                'requirementsBackend': requirements_review.supported(self)}

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
        with self.processes.scope():
            self._execute_ai(record, context)

    def _execute_ai(self, record, context):
        from .pdf import export_snapshot, compile_document
        stage = self.root / "runs" / record["id"]
        location, source, job = (context[key] for key in ("location", "source", "job"))
        try:
            with self.inspector.phase(record, "staging"):
                export_snapshot(self.repository, context["baseCommit"], stage, location)
                for name, expected in context['checkpointInputs']['assets'].items():
                    path = safe_path(stage, name)
                    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                        raise PreparationConflict('Your application inputs changed while preparing the workspace. Your edits were preserved.')
                atomic_write(stage / "main.tex", source)
                atomic_write(stage / "job.md", job)
                for filename, content in context["skills"].items():
                    atomic_write(safe_path(stage, filename), content)
                for filename, content in context["config"].items():
                    atomic_write(stage / ".vita" / filename, content)
                # Never mistake reports copied from a previous run for this run's outputs.
                for path in self.report_paths():
                    safe_path(stage, path).unlink(missing_ok=True)
                if context.get('coverBefore') is not None:
                    atomic_write(stage/'cover-letter.tex', context['coverBefore'])
                else:
                    safe_path(stage, "cover-letter.tex").unlink(missing_ok=True)
                for path, content in context['dependencies'].items():
                    atomic_write(safe_path(stage, path), content)
                for name, content in context['criteria'].items():
                    atomic_write(safe_path(stage / '.vita/criteria-snapshot', name), content)
            if not self._job_update(record, step='preflight', message='Checking the captured project and PDF tools before any AI calls.'):
                return
            with self.inspector.phase(record, 'validation'):
                checked = preflight.check_project(stage, context['config'], context['compileEngine'], self.document_path,
                                                  context['selected'], digest(source), digest(job), self.root/'preflight',
                                                  set(context['keys'].values()) | {v for k,v in context['env'].items() if credential_name(k)},
                                                  context['checkpointInputs']['assets'])
                if not self._job_update(record, preflight=checked):return
                if not checked['ready']:
                    problem = next(item for item in checked['checks'] if item['severity']=='error')
                    raise AIRunError(problem['message'] + ' Open Check setup for next steps. No AI was called.')
                def invalidate_checks(message):
                    checked['checks'].append(preflight.item('draft_changed'))
                    self._job_update(record, preflight=preflight.public_result(checked))
                    raise PreparationConflict(message)
                with self.lock:
                    try:
                        current,_=preflight.project_state(self,record['branch'])
                    except (ValueError,OSError,RuntimeError):
                        invalidate_checks('Project inputs became unavailable during setup checks. Your edits were preserved; reload and check again.')
                    if current['commit'] != context['baseCommit'] or current['source'] != digest(source) or current['job'] != digest(job):
                        invalidate_checks('The draft changed during setup checks. Your edits were preserved; check the new draft again.')
                    current_assets={k:v for k,v in current['assets'].items() if k not in {'main.tex','job.md','cover-letter.tex'}}
                    if current_assets!=context['checkpointInputs']['assets']:
                        invalidate_checks('Project dependencies changed during setup checks. Your edits were preserved; check again.')
            verified_source = digest(source) if any(item['code']=='compiled' for item in checked['checks']) else None
            def verify_limited_source(value):
                if digest(value) == verified_source:return
                if parse_document(value)['error'] or r'\begin{document}' not in value:
                    verified = preflight.check_project(stage, context['config'], context['compileEngine'], self.document_path,
                                                        context['selected'], scratch=self.root/'preflight')
                    if not verified['ready']:
                        raise AIRunError('The resulting CV could not compile. Your application is unchanged; check the saved preparation source and PDF dependencies.')
            for task in record["stages"]:
                step = task["id"]
                if task["status"] == "skipped" or step == "validating":
                    continue
                before = checkpoints.artifacts(stage)
                key = checkpoints.signature(context, step, before)
                self.inspector.capture_step(record, step, digest(before['main.tex'] or ''), checkpoints.fingerprint(before), key)
                saved = context['resume']['checkpoints'].get(step)
                if saved:
                    checkpoints.restore(stage, saved[1])
                    reused_pdf = None
                    if step == 'cover' and not saved[0].get('omitted'):
                        output = safe_path(self.root, 'run-pdfs/' + record['id'])
                        prior_pdf = self.root/'checkpoints'/record['parentRunId']/step/'cover-letter.pdf'
                        atomic_write_bytes(output/'cover-letter.pdf', prior_pdf.read_bytes())
                        atomic_write(output/'ready.json', json.dumps({key: saved[0]['pdf'][key] for key in ('engine','warnings')}))
                        reused_pdf = dict(path=output/'cover-letter.pdf', **{key: saved[0]['pdf'][key] for key in ('engine','warnings')})
                    with self.inspector.phase(record, 'checkpoint', step):
                        saved_child = checkpoints.write_checkpoint(self.root/'checkpoints', record['id'], step, key, saved[1], saved[0]['outcome'], reused_pdf, saved[0].get('omitted', False))
                    if not saved_child:
                        self.inspector.mark(record, 'checkpoint', 'not_retained', step)
                    self.inspector.mark(record, 'checkpoint', 'reused', step, reused_from=record['parentRunId'])
                    reused_stages = [dict(item, status='succeeded', startedAt=time.time(), finishedAt=time.time(), reusedFrom=record['parentRunId']) if item['id'] == step else dict(item) for item in record['stages']]
                    saved_outcome = self._safe_outcomes({step: saved[0]['outcome']})[step]
                    if not self._job_update(record, step=step, message='Reused verified ' + step + ' results.',
                                            stages=reused_stages,
                                            checkpointSteps=[*record['checkpointSteps'], *([step] if saved_child else [])],
                                            outcomes={**record['outcomes'], step: saved_outcome}):
                        return
                    continue
                if not self._job_update(record, step=step, message=MESSAGES[step],
                                        stages=transition(record["stages"], step=step)):
                    return
                step_pdf = None
                route = context['stepConfig'][step]
                env = stage_environment(context['env'], route, context['keys'].get(step))
                execution_id = uuid.uuid4().hex
                env.update(self.inspector.environment(record, step))
                env['VITA_TREE_EXECUTION_ID'] = execution_id
                env['VITA_REQUIREMENTS_DIR'] = str(stage / '.vita/criteria-snapshot')
                safe_path(stage, '.vita/results/tree-' + step + '.outcome.json').unlink(missing_ok=True)
                safe_path(stage, '.vita/results/' + step + '.outcome.json').unlink(missing_ok=True)
                # Same provider may use different models in consecutive steps.
                extensions = json.loads(context['config'].get('extensions.json', '{}'))
                extensions.setdefault('llm_providers', {})[route['provider']] = {'model': route['model'], **({'reasoning_effort': route['reasoning']} if route['reasoning'] else {})}
                atomic_write(stage / '.vita/extensions.json', json.dumps(extensions))
                args = context["command"] + [step, "--auto", "--provider", route['provider']]
                if step in ("adapt", "cover"):
                    args += ["--language", record["language"]]
                if step == "cover" and not context['factualBackend']:
                    safe_path(stage, "cover-letter.tex").unlink(missing_ok=True)
                # Retained inputs are context, never evidence that this task ran.
                for filename in REPORTS[step]:
                    safe_path(stage, '.vita/results/' + filename).unlink(missing_ok=True)
                if step in {'adapt', 'cover'}:
                    for downstream in (('adapt', 'cover') if step == 'adapt' else ('cover',)):
                        for suffix in ('.facts.json', '.facts.md', '.decisions.json'):
                            safe_path(stage, '.vita/results/' + downstream + suffix).unlink(missing_ok=True)
                    safe_path(stage, '.vita/results/tree-' + step + '.facts.json').unlink(missing_ok=True)
                if step == 'analyze':
                    for filename in ('delta.md', 'delta.json'):
                        safe_path(stage, '.vita/results/' + filename).unlink(missing_ok=True)
                with self.inspector.phase(record, 'subprocess', step):
                    process = self.processes.run(args, cwd=stage, env=env, stdin=subprocess.DEVNULL,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
                if process.returncode:
                    self.inspector.mark(record, 'subprocess', 'error', step, error=RuntimeError())
                with self.inspector.phase(record, 'validation', step):
                    secrets = set(context['keys'].values()) | {v for k,v in context['env'].items() if credential_name(k)}
                    if scrub_generated(stage,secrets):
                        raise AIRunError('Generated output contained a session credential and was withheld. Your application is unchanged. Review the source and provider setup before retrying.')
                    reports = [read_text(safe_path(stage, ".vita/results/" + name)).strip() for name in REPORTS[step]]
                    if process.returncode:
                        self.diagnostics.record('provider_failed', 'ERROR', run_id=record['id'], step=step, exit_code=process.returncode)
                    outcome = read_outcome(stage, step, execution_id)
                    if outcome:
                        if not self._job_update(record, outcomes={**record['outcomes'], step: outcome}):
                            return
                    if step in {'adapt', 'cover'}:
                        try:
                            if context['factualBackend'] and not process.returncode and not safe_path(stage, '.vita/results/' + step + '.facts.json').is_file():
                                raise ValueError('Missing factual-change contract')
                            pending = factual_review.capture(self, record, context, stage, step, execution_id, before, key)
                        except (OSError, ValueError, KeyError, TypeError):
                            raise AIRunError('Factual-change evidence could not be verified. Check Vita CV contract support and regenerate. Your application is unchanged.') from None
                        if pending:
                            raise AIRunError('Review the proposed factual changes before continuing. Your application is unchanged.')
                    if process.returncode or not any(reports) or (outcome and outcome['status'] != 'success'):
                        info = failure(outcome)
                        raise AIRunError((info['title'] + '. ' + info['action'] if info else 'The expected results were not returned. Inspect execution details before retrying.') + ' Your CV is unchanged.')
                    if step == "extract":
                        try:
                            extracted = json.loads(reports[0])
                            if extracted.get("source_sha256") != digest(job) or not reports[1]:
                                raise ValueError("Job mismatch")
                        except (ValueError, AttributeError):
                            raise AIRunError("The job requirements could not be verified against this job description. Your CV is unchanged.") from None
                        requirements_review.capture(self, record, context, stage, execution_id)
                    if step in {'analyze','review'} and context.get('requirementsRevision'):
                        try:
                            assessment = json.loads(read_text(stage/('.vita/results/'+('analysis.json' if step=='analyze' else 'review.json'))))
                            if assessment['metadata']['requirements_revision'] != context['requirementsRevision']:
                                raise ValueError('Mismatched requirements')
                        except (ValueError, KeyError, TypeError):
                            raise AIRunError('The assessment did not use the captured requirement revision. Your application is unchanged.') from None
                    if read_text(stage / 'job.md') != job:
                        raise AIRunError('The preparation unexpectedly changed its job description. Your application is unchanged.')
                    step_source = read_text(stage / 'main.tex')
                    if step != 'adapt' and step_source != before['main.tex']:
                        raise AIRunError('This feedback step unexpectedly changed the CV. Your application is unchanged; inspect the preparation results.')
                    if step == 'adapt':
                        verify_limited_source(step_source)
                        verified_source = digest(step_source)
                if step == 'cover':
                    cover_source = read_text(safe_path(stage, 'cover-letter.tex'))
                    if not cover_source.strip():
                        raise AIRunError('Your AI service did not produce a valid cover letter. Your application is unchanged; inspect the preparation results.')
                    if not self._job_update(record, message='Compiling the cover-letter PDF…'):
                        return
                    try:
                        output = safe_path(self.root, 'run-pdfs/' + record['id'])
                        with self.inspector.phase(record, 'pdf', step):
                            built = compile_document(stage, 'cover-letter.tex', engine=context['compileEngine'], output=output)
                        self.diagnostics.record('pdf_compiled', operation='compile_cover', run_id=record['id'], step='cover')
                        atomic_write(output / 'ready.json', json.dumps({'engine': built['engine'], 'warnings': built['warnings']}))
                        step_pdf = {'path': built['pdf'], 'engine': built['engine'], 'warnings': built['warnings']}
                    except (ValueError, OSError, subprocess.SubprocessError) as error:
                        raise AIRunError('The cover-letter PDF could not be created. Your application is unchanged. Check the PDF tools and packages, inspect the cover-letter source in the preparation results, then retry.') from error
                if outcome and outcome['verified'] and outcome['status'] == 'success':
                    with self.inspector.phase(record, 'checkpoint', step):
                        saved = checkpoints.write_checkpoint(self.root/'checkpoints', record['id'], step, key,
                                                             checkpoints.artifacts(stage), outcome, step_pdf)
                    if not saved:
                        self.inspector.mark(record, 'checkpoint', 'not_retained', step)
                    if saved and not self._job_update(record, checkpointSteps=[*record['checkpointSteps'], step]):
                        return
                if step == 'extract':
                    requirements_review.require_approval(self, record, context)
            if not self._job_update(record, step="validating", message=MESSAGES["validating"],
                                    stages=transition(record["stages"], step="validating")):
                return
            with self.lock:
                with self.inspector.phase(record, 'validation', 'validating'):
                    cover = None
                    if any(t["id"] == "cover" and t["status"] != "skipped" for t in record["stages"]) and not checkpoints.rejected_cover(checkpoints.artifacts(stage)):
                        cover = read_text(safe_path(stage, "cover-letter.tex"))
                        if not cover.strip():
                            raise AIRunError("Your AI service did not produce a valid cover letter. Your application is unchanged; inspect the preparation results.")
                    result = read_text(stage / "main.tex")
                    adapting = 'adapt' in context['selected']
                    if adapting or context['selected'] == {'validating'}:
                        verify_limited_source(result)
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
                            raise PreparationConflict("Your application changed during preparation. The results were kept separately and your edits were preserved.")
                        # Include files and approved criteria are application evidence, too.
                        # AI setup/skills remain the immutable submitted choice for this
                        # attempt; changing them invalidates checkpoints on the next retry.
                        fresh = self._ai_context(location, source, job, context['command'], record['provider'], record['model'], record['reasoning'])
                        fresh.update(stepConfig=context['stepConfig'], keys=context['keys'], dependencies=context['dependencies'])
                        capture_resume_inputs(self, fresh, record)
                        if any(fresh['checkpointInputs'][key] != context['checkpointInputs'][key]
                               for key in ('assets', 'criteria', 'backend')):
                            raise PreparationConflict('Your application inputs or AI configuration changed during preparation. Results were retained separately and your edits were preserved.')
                        updates = {}
                        if adapting and result != source:
                            meta = self.metadata(record['branch'])
                            meta.update(baseCommit=self.head(record['branch']), baseBranch=record['branch'] + ' · before AI', original=source,
                                        originalFiles=includes.local(location, self.document_path)['files'])
                            updates['@metadata'] = json.dumps(meta)
                        outputs = {'.vita/results/' + filename for step in context['selected'] if step in REPORTS for filename in REPORTS[step]}
                        if 'analyze' in context['selected']:
                            outputs.update(('.vita/results/delta.md', '.vita/results/delta.json'))
                        for path in outputs:
                            target = safe_path(stage, path)
                            updates[path] = read_text(target) if target.is_file() else None
                        if cover is not None:
                            updates['cover-letter.tex'] = cover
                        if adapting and result != source:
                            updates[self.document_path] = result
                        if context['selected'] & {'adapt', 'cover'}:
                            for path, content in checkpoints.artifacts(stage).items():
                                if path in checkpoints.FACTUAL_ARTIFACTS or path.startswith('.vita/factual-changes/'):
                                    updates[path] = content
                with self.lock, self.inspector.phase(record, 'publication', 'validating'):
                    with publish(self, record['id'], record['branch'], updates):
                        if not self._job_update(record, status="succeeded", step="completed", finishedAt=time.time(),
                                                message=("Your changes were checked. Create a PDF preview to check the final layout."
                                                         if context['selected'] == {'validating'} else "Cover-letter PDF ready. Open the run to review and save it." if cover is not None else "Selected steps finished. Open the run to review the results."),
                                                stages=transition(record['stages'], terminal='succeeded')):
                            raise AIRunError('The preparation was interrupted before publication completed.')
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
            self.inspector.finish(record)
            context.get('keys', {}).clear()
            try:
                self._automatic_review(record)
            except Exception as error:
                self.diagnostics.error('automatic_review_failed', error, run_id=record['id'])
                self._job_update(record, message='Automatic approval could not continue safely. Review the saved proposal and application inputs, then continue manually.')
            try:
                if not self._closed:
                    self.cleanup_checkpoints()
            except OSError as error:
                self.diagnostics.error('checkpoint_cleanup_failed', error, operation='checkpoints')
            with self.lock:
                self._ai_threads.discard(threading.current_thread())
                if record["branch"] in self._release_requested:
                    self.release_worktree(record["branch"])
