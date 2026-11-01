"""Private Jobenu batch sessions. Vita owns planning, branches and checkpoints."""

import hashlib
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import uuid

from .fileio import atomic_write_bytes
from .security import credential_name, redact


def read_json(path):
    if path.is_symlink() or path.stat().st_size > 16_000_000:
        raise ValueError("Unsafe or oversized import state.")
    return json.loads(path.read_text(encoding="utf-8-sig"))


class JobenuImports:
    def __init__(self, workspace):
        self.ws = workspace
        self.root = workspace.root / "jobenu-batches"
        self.lock = threading.RLock()
        self.history_lock = threading.RLock()
        self.environments = {}
        self.running = set()
        self.reviewing = set()
        self.workers = set()

    def folder(self, ident):
        from .workspace import safe_path

        if not isinstance(ident, str) or not re.fullmatch("[a-f0-9]{32}", ident):
            raise ValueError("Invalid batch ID.")
        return safe_path(self.root, ident)

    def save(self, record):
        atomic_write_bytes(
            self.folder(record["id"]) / "session.json",
            json.dumps(record, ensure_ascii=False).encode(),
        )

    def record(self, ident):
        return read_json(self.folder(ident) / "session.json")

    def command(self, source=""):
        from .workspace import safe_path

        safe_path(self.ws.repository, ".vita/imports/jobenu")
        source = source or self.ws.vita_source
        env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        if source:
            source = Path(source).expanduser().resolve()
            if not (source / "vita/__main__.py").is_file():
                raise ValueError(
                    "Select a Vita CV source folder containing vita/__main__.py."
                )
            env["PYTHONPATH"] = str(source) + os.pathsep + env.get("PYTHONPATH", "")
            return [sys.executable, "-m", "vita"], env
        executable = self.ws.vita_command()
        if not executable:
            raise ValueError(
                "Vita CV is unavailable. Select a compatible source installation."
            )
        return executable, env

    def invoke(self, command, env, args, cwd=None, timeout=30):
        # File-backed output avoids pipe deadlocks and keeps raw diagnostics private.
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            result = self.ws.processes.run(
                [*command, *args],
                cwd=cwd or self.ws.repository,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                timeout=timeout,
            )
            out.seek(0)
            err.seek(0)
            return result.returncode, out.read(16_000_001), err.read(2_000_000)

    def capability(self, source=""):
        try:
            command, env = self.command(source)
            code, out, _ = self.invoke(command, env, ["import", "jobenu", "--help"])
            supported = code == 0 and all(
                flag.encode() in out
                for flag in ("--plan-id", "--approve-plan", "--json")
            )
            config = self.ws.repository / ".vita/config.json"
            data = read_json(config) if config.is_file() else {}
            base = (
                data.get("integrations", {}).get("jobenu", {}).get("base_branch")
                or data.get("default_base_branch")
                or "master"
            )
            return {
                "available": supported,
                "base": base,
                "message": ""
                if supported
                else "This Vita installation does not support Jobenu batches. Select a compatible Vita CV source folder.",
            }
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError):
            return {
                "available": False,
                "base": "master",
                "message": "Jobenu support could not be verified. Select a compatible Vita CV source folder and check again.",
            }

    def upload(self, filename, content):
        if not isinstance(content, str) or len(content.encode()) > 10 * 1024 * 1024:
            raise ValueError("Choose a JSON export smaller than 10 MiB.")

        def pairs(items):
            d = {}
            for k, v in items:
                if k in d:
                    raise ValueError("Duplicate JSON fields are not supported.")
                d[k] = v
            return d

        try:
            data = json.loads(
                content.lstrip("\ufeff"),
                object_pairs_hook=pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    ValueError("Invalid JSON number")
                ),
            )
        except (ValueError, RecursionError):
            raise ValueError("Choose a valid UTF-8 Jobenu JSON export.") from None
        apps = data.get("applications") if isinstance(data, dict) else None
        if not isinstance(apps, list) or len(apps) > 1000:
            raise ValueError("The export must contain at most 1,000 applications.")
        if data.get("exportedAt") is not None and not isinstance(
            data["exportedAt"], str
        ):
            raise ValueError("Invalid export timestamp.")
        seen = set()
        for app in apps:
            if not isinstance(app, dict) or any(
                not isinstance(app.get(k), str) or not app[k].strip() or "\0" in app[k]
                for k in ("id", "company", "position", "description")
            ):
                raise ValueError(
                    "Every application needs an ID, company, position and description."
                )
            if app["id"] in seen:
                raise ValueError("Application IDs must be unique.")
            if not isinstance(app.get("status", "SAVED"), str) or not isinstance(
                app.get("isDemo", False), bool
            ):
                raise ValueError("Invalid application status or demo flag.")
            if any(
                len(app[k]) > limit
                for k, limit in [("id", 512), ("company", 512), ("position", 2048)]
            ):
                raise ValueError("Oversized application identity or position.")
            seen.add(app["id"])
        ident = uuid.uuid4().hex
        atomic_write_bytes(
            self.folder(ident) / "original.json",
            json.dumps(data, ensure_ascii=False).encode(),
        )
        record = {
            "id": ident,
            "filename": Path(str(filename)).name[:200],
            "status": "selecting",
            "createdAt": time.time(),
        }
        self.save(record)
        return {
            **record,
            "applications": [
                {
                    k: app.get(k, "SAVED" if k == "status" else "")
                    for k in ("id", "company", "position", "status", "isDemo")
                }
                for app in apps
            ],
        }

    def options(self, data):
        base = data.get("base")
        if not self.ws.branch(base)["local"]:
            raise ValueError("Choose an existing local base branch.")
        approval = data.get("approval", "human")
        if approval not in {"human", "auto"}:
            raise ValueError("Choose an approval mode.")
        args = ["--base-branch", base, "--approval", approval]
        for flag, key in (
            ("--run", "run"),
            ("--new-revision", "newRevision"),
            ("--rerun", "rerun"),
            ("--include-demo", "includeDemo"),
        ):
            if data.get(key) is True:
                args.append(flag)
        for flag, key in (("--language", "language"), ("--provider", "provider")):
            value = data.get(key, "")
            if value:
                if not isinstance(value, str) or not re.fullmatch(
                    "[a-zA-Z0-9_.-]{1,64}", value
                ):
                    raise ValueError("Invalid language or provider code.")
                args.extend([flag, value])
        statuses = data.get("statuses", ["SAVED"])
        if not isinstance(statuses, list) or any(
            not isinstance(s, str) or not re.fullmatch("[A-Z_]{1,32}", s)
            for s in statuses
        ):
            raise ValueError("Invalid status filters.")
        for status in statuses:
            args.extend(["--status", status])
        return args

    def preview(self, ident, data):
        with self.lock:
            if self.running:
                raise ValueError(
                    "A Jobenu batch is running. Wait before changing import settings."
                )
            self.history()
            record = self.record(ident)
            record.update(status="selecting", plan=None)
            self.environments.pop(ident, None)
            self.save(record)
            original = read_json(self.folder(ident) / "original.json")
            ids = data.get("ids")
            if (
                not isinstance(ids, list)
                or any(not isinstance(i, str) for i in ids)
                or len(set(ids)) != len(ids)
            ):
                raise ValueError("Select application IDs.")
            known = {a["id"] for a in original["applications"]}
            if not set(ids) <= known:
                raise ValueError("An application is not in this export.")
            filtered = {
                **original,
                "applications": [a for a in original["applications"] if a["id"] in ids],
            }
            path = self.folder(ident) / "selected.json"
            atomic_write_bytes(path, json.dumps(filtered, ensure_ascii=False).encode())
            command, env = self.command(data.get("source", ""))
            # Existing Tree stage provider/model preferences use Vita's environment
            # mechanism, never invented batch command flags. Secrets remain in RAM.
            settings = self.ws.ai_settings(data["base"])
            from .ai_config import effective_settings, PREFIXES

            provider_keys = {}
            saved = (
                self.ws.root
                / "ai-settings"
                / (hashlib.sha256(data["base"].encode()).hexdigest() + ".json")
            )
            routes = (
                effective_settings(settings, set(PREFIXES)) if saved.is_file() else {}
            )
            for step, route in routes.items():
                prefix = PREFIXES[step]
                if route.get("provider"):
                    env[prefix + "_PROVIDER"] = route["provider"]
                if route.get("model"):
                    env[prefix + "_MODEL"] = route["model"]
                if route.get("connection"):
                    key = self.ws.connections.get(
                        route["connection"], route["provider"]
                    )
                    if (
                        route["provider"] in provider_keys
                        and provider_keys[route["provider"]] != key
                    ):
                        raise ValueError(
                            "This batch backend uses one credential per provider. Use the same connection for that provider in all selected steps."
                        )
                    provider_keys[route["provider"]] = key
                    env[route["provider"].upper() + "_API_KEY"] = key
            args = ["import", "jobenu", str(path), *self.options(data), "--json"]
            code, out, _ = self.invoke(command, env, [*args, "--dry-run"])
            plan = self.envelope(code, out)
            if not isinstance(plan.get("plan_id"), str):
                raise ValueError(
                    redact(
                        plan.get(
                            "error",
                            "Preview failed. Check the installation and source.",
                        ),
                        self.secrets(env),
                    )
                )
            record.update(
                status="planned" if code == 0 else "conflict",
                plan=plan,
                args=args,
                source=data.get("source", ""),
                fileHash=hashlib.sha256(path.read_bytes()).hexdigest(),
                options=data,
                capturedRoutes={
                    step: {
                        field: env[prefix + "_" + suffix]
                        for field, suffix in (
                            ("provider", "PROVIDER"),
                            ("model", "MODEL"),
                        )
                        if env.get(prefix + "_" + suffix)
                    }
                    for step, prefix in PREFIXES.items()
                },
            )
            self.environments[ident] = (command, env)
            self.save(record)
            return self.public(record)

    @staticmethod
    def envelope(code, out):
        try:
            if len(out) > 16_000_000:
                raise ValueError()
            result = json.loads(out.decode("utf-8-sig"))
            if (
                not isinstance(result, dict)
                or result.get("schema_version") != 1
                or not isinstance(result.get("status"), str)
            ):
                raise ValueError()
        except (ValueError, UnicodeError):
            raise ValueError(
                "Vita returned unreadable output. Check its Jobenu capability and private execution log; no approval was inferred."
            ) from None
        allowed = {
            0: {"planned", "imported", "complete", "empty"},
            1: {"failed", "rejected", "conflict"},
            2: {
                "awaiting_approval",
                "awaiting_plan_approval",
                "awaiting_requirements_approval",
            },
        }
        if result["status"] not in allowed.get(code, set()):
            raise ValueError("Vita failed without a valid approval-required result.")
        return result

    def start(self, ident, plan_id):
        with self.lock:
            if self.ws._closed:
                raise ValueError(
                    "Vita Tree is stopping. Restart before running a batch."
                )
            r = self.record(ident)
            if self.running:
                raise ValueError("A Jobenu batch is already running.")
            if (
                r.get("status") != "planned"
                or r.get("plan", {}).get("plan_id") != plan_id
                or ident not in self.environments
            ):
                raise ValueError(
                    "Preview this batch again before starting or resuming."
                )
            if (
                hashlib.sha256(self.selected_path(ident).read_bytes()).hexdigest()
                != r["fileHash"]
            ):
                raise ValueError("The selected source changed. Preview again.")
            with self.ws.lock:
                if self.ws._closed:
                    raise ValueError(
                        "Vita Tree is stopping. Restart before running a batch."
                    )
                for entry in self.entries(r):
                    if entry.get("branch"):
                        self.ws.busy(entry["branch"])
                self.running.add(ident)
                worker = threading.Thread(target=self._run, args=(r,), daemon=True)
                try:
                    r.update(
                        status="running",
                        startedAt=time.time(),
                        finishedAt=None,
                        attempt=(r.get("attempt") or 0) + 1,
                    )
                    self.save(r)
                    self.workers.add(worker)
                    worker.start()
                except Exception:
                    self.running.discard(ident)
                    self.workers.discard(worker)
                    raise
            return self.public(r)

    def selected_path(self, ident):
        from .workspace import safe_path

        return safe_path(self.folder(ident), "selected.json")

    def _run(self, r):
        ident = r["id"]
        try:
            command, env = self.environments[ident]
            code, out, err = self.invoke(
                command,
                env,
                [*r["args"], "--approve-plan", "--plan-id", r["plan"]["plan_id"]],
                timeout=None,
            )
            atomic_write_bytes(self.folder(ident) / "execution.log", out + b"\n" + err)
            result = self.envelope(code, out)
            r.update(
                status=result["status"],
                result=result,
                exitCode=code,
                error=result.get("error"),
            )
        except Exception:
            r.update(
                status="failed",
                error="Batch execution stopped. Open the private log, check the installation and preview again to resume. Completed application results remain available.",
            )
        finally:
            with self.lock:
                if self.ws._closed:
                    r.update(
                        status="interrupted",
                        error="Vita Tree stopped. Preview again to resume using native checkpoints.",
                    )
                r["finishedAt"] = time.time()
                try:
                    self.save(r)
                finally:
                    self.running.discard(ident)
                    self.workers.discard(threading.current_thread())

    def entries(self, r):
        plan = r.get("plan") or {}
        rows = (
            plan.get("entries", [])
            if r["status"] in {"planned", "conflict", "selecting"}
            else (r.get("result") or {}).get("results") or plan.get("entries", [])
        )
        from .workspace import safe_path

        try:
            index = safe_path(self.ws.repository, ".vita/imports/jobenu/index.json")
            states = read_json(index).get("applications", {})
        except (OSError, ValueError):
            states = {}
        return [
            {
                **row,
                **states.get(row.get("key"), {})
                .get("versions", {})
                .get(row.get("fingerprint"), {}),
            }
            for row in rows
        ]

    def public(self, r):
        result = {
            k: r.get(k)
            for k in (
                "id",
                "filename",
                "status",
                "createdAt",
                "startedAt",
                "finishedAt",
                "error",
                "exitCode",
            )
        }
        result["plan"] = r.get("plan")
        result["options"] = r.get("options")
        result["entries"] = self.entries(r)
        env = self.environments.get(r["id"], ([], {}))[1]
        return json.loads(
            redact(
                json.dumps(result),
                self.secrets(env),
            )
        )

    def selection(self, ident):
        return {
            "applications": read_json(self.folder(ident) / "original.json")[
                "applications"
            ]
        }

    def listing(self):
        records = []
        for p in self.root.glob("*/session.json"):
            try:
                r = self.record(p.parent.name)
                if r["status"] == "running" and r["id"] not in self.running:
                    r["status"] = "interrupted"
                records.append(self.public(r))
            except (OSError, ValueError):
                continue
        return {"batches": sorted(records, key=lambda r: r["createdAt"], reverse=True)}

    def history(self, branch=None):
        from .jobenu_history import history

        return history(self, branch)

    def target(self, ident, key):
        from .workspace import safe_path

        r = self.record(ident)
        row = next((e for e in self.entries(r) if e.get("key") == key), None)
        if not row or not row.get("workspace"):
            raise ValueError("This application has no imported workspace yet.")
        path = Path(row["workspace"])
        expected = safe_path(
            self.ws.repository, ".vita/imports/jobenu/worktrees"
        ).resolve()
        if path.is_symlink() or not path.resolve().is_relative_to(expected):
            raise ValueError("Unsafe imported workspace.")
        if self.ws.location(row["branch"]) != path.resolve():
            raise ValueError("The imported worktree is missing or changed branches.")
        return r, row, path

    def review(self, ident, key):
        r, row, path = self.target(ident, key)
        command, env = self.environments.get(ident) or self.command(r.get("source", ""))
        if row.get("pending"):
            code, out, _ = self.invoke(
                command,
                env,
                ["facts", "show", row["pending"]["step"], "--json"],
                cwd=path,
            )
            if code:
                raise ValueError(
                    "The factual proposal is unavailable. Check the workspace log."
                )
            report = json.loads(out)
            if report.get("revision") != row["pending"]["revision"]:
                raise ValueError(
                    "The pending revision changed; preview the batch again."
                )
            return {"kind": "facts", "report": self.clean_report(report, env)}
        code, out, _ = self.invoke(command, env, ["requirements", "show"], cwd=path)
        if code:
            return {"kind": "requirements", "needsDraft": True}
        return {
            "kind": "requirements",
            "report": self.clean_report(json.loads(out), env),
        }

    @contextmanager
    def review_guard(self, ident, key):
        if self.running:
            raise ValueError("Wait for the batch to pause before reviewing.")
        target = self.target(ident, key)
        branch = target[1].get("branch")
        with self.ws.lock:
            if branch:
                self.ws.busy(branch)
                self.reviewing.add(branch)
        try:
            yield target
        finally:
            self.reviewing.discard(branch)

    def decide(self, ident, key, action, revision):
        with self.lock, self.review_guard(ident, key) as (r, row, path):
            command, env = self.environments.get(ident) or self.command(
                r.get("source", "")
            )
            if action == "draft":
                args = ["requirements", "draft", "--auto"]
            else:
                current = self.review(ident, key)
                expected = (
                    current["report"]["revision"]
                    if current["kind"] == "facts"
                    else current["report"]["revision"]["revision"]
                )
                if expected != revision:
                    raise ValueError("The proposal changed. Reopen the review.")
                if action not in {"approve", "reject"}:
                    raise ValueError("Choose approve or reject.")
                if current["kind"] == "requirements" and action != "approve":
                    raise ValueError(
                        "Close the review to leave requirements unapproved."
                    )
                args = (
                    ["facts", action, row["pending"]["step"], revision]
                    if current["kind"] == "facts"
                    else ["requirements", "approve", revision]
                )
            code, _, _ = self.invoke(command, env, args, cwd=path, timeout=600)
            if code:
                raise ValueError(
                    "The decision could not be saved. Local work is preserved; reopen the review and inspect the workspace log."
                )
            self.history()
            return {"saved": True}

    def log(self, ident, key=None):
        from .workspace import safe_path

        path = self.folder(ident) / "execution.log"
        if key:
            r = self.record(ident)
            row = next(
                (entry for entry in self.entries(r) if entry.get("key") == key), None
            )
            if not row:
                raise ValueError("Unknown imported application.")
            if row.get("execution_log"):
                candidate = Path(row["execution_log"])
                shared = safe_path(self.ws.repository, ".vita/imports/jobenu/git.log")
                if candidate == shared:
                    path = shared
                else:
                    _, _, workspace = self.target(ident, key)
                    if not candidate.is_relative_to(workspace):
                        raise ValueError(
                            "The application log is outside its workspace."
                        )
                    path = safe_path(
                        workspace, candidate.relative_to(workspace).as_posix()
                    )
        if path.is_symlink():
            raise ValueError("Linked logs are not supported.")
        if path.is_file():
            with path.open("rb") as handle:
                handle.seek(max(0, path.stat().st_size - 100_000))
                raw = handle.read(100_000).decode("utf-8", errors="replace")
        else:
            raw = "The CLI is running. Per-application logs are retained in their imported workspaces."
        env = self.environments.get(ident, ([], {}))[1]
        return {"text": redact(raw, self.secrets(env))}

    def secrets(self, env):
        from .workspace import safe_path

        values = set(self.ws._job_secrets()) | {
            v for k, v in {**os.environ, **env}.items() if credential_name(k)
        }
        try:
            path = safe_path(self.ws.repository, ".env")
            if path.is_file() and path.stat().st_size <= 2_000_000:
                for line in path.read_text(encoding="utf-8-sig").splitlines():
                    key, separator, value = line.partition("=")
                    if separator and credential_name(key):
                        values.add(value.strip().strip("\"'"))
        except (OSError, ValueError):
            pass
        return values

    def clean_report(self, value, env):
        secrets = self.secrets(env)

        def clean(item):
            if isinstance(item, str):
                return redact(item, secrets)
            if isinstance(item, list):
                return [clean(child) for child in item]
            if isinstance(item, dict):
                return {key: clean(child) for key, child in item.items()}
            return item

        return clean(value)

    def alias(self, title, alias):
        from .workspace import safe_path

        if self.running:
            raise ValueError("Wait for the batch before changing aliases.")
        if (
            not isinstance(title, str)
            or not title.strip()
            or not isinstance(alias, str)
            or not re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", alias)
        ):
            raise ValueError("Use a role title and a short lowercase role alias.")
        path = safe_path(self.ws.repository, ".vita/extensions.json")
        data = read_json(path) if path.exists() else {}
        data.setdefault("role_aliases", {})[title] = alias
        atomic_write_bytes(
            path, json.dumps(data, ensure_ascii=False, indent=2).encode()
        )
        return {"saved": True}

    def discard(self, ident):
        with self.lock:
            if ident in self.running:
                raise ValueError("A running batch cannot be forgotten.")
            self.history()
            folder = self.folder(ident)
            for name in (
                "session.json",
                "original.json",
                "selected.json",
                "execution.log",
            ):
                (folder / name).unlink(missing_ok=True)
            folder.rmdir()
            self.environments.pop(ident, None)
            return {"removed": True}
