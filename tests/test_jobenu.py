import json
import os
from pathlib import Path
import tempfile, time, unittest
from unittest.mock import patch
from support import init_repo, cleanup_repo, git
from vita_tree.workspace import Workspace, digest, ConflictError
from vita_tree.jobenu import JobenuImports

EXPORT = {
    "exportedAt": "2026-01-01",
    "applications": [
        {
            "id": "one",
            "company": "Sample Co",
            "position": "Data Engineer",
            "description": "Synthetic data job",
            "status": "SAVED",
            "notes": "<img src=x onerror=alert(1)>",
        },
        {
            "id": "two",
            "company": "Other Co",
            "position": "ML Engineer",
            "description": "Synthetic ML job",
            "status": "SAVED",
        },
    ],
}
SOURCE = Path(
    os.environ.get(
        "VITA_JOBENU_SOURCE",
        str(Path(__file__).resolve().parents[1] / ".test-artifacts/vita-jobenu"),
    )
)


class JobenuTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            prefix=".vita-tree-test-", dir=Path.cwd()
        )
        self.root = init_repo(Path(self.temp.name))
        self.ws = Workspace(self.root)
        self.manager = self.ws.jobenu

    def tearDown(self):
        self.ws.close()
        cleanup_repo(self.temp)

    def upload(self):
        return self.manager.upload("jobs.json", json.dumps(EXPORT))["id"]

    def options(self, ident, **extra):
        return dict(
            id=ident,
            ids=["one"],
            base="master",
            approval="human",
            run=False,
            source=str(SOURCE),
            **extra,
        )

    def test_invalid_exports_and_empty_selection(self):
        for value in (
            "bad",
            "[]",
            '{"applications":{}}',
            json.dumps({"applications": [EXPORT["applications"][0]] * 2}),
        ):
            with self.assertRaises(ValueError):
                self.manager.upload("bad.json", value)
        ident = self.upload()
        self.assertEqual(len(self.manager.selection(ident)["applications"]), 2)
        self.manager.discard(ident)
        self.assertFalse(self.manager.folder(ident).exists())

    def test_exit_statuses_require_structured_contract(self):
        for code, out in [
            (2, b"usage: error"),
            (2, b'{"schema_version":1,"status":"failed"}'),
            (0, b'{"schema_version":1,"status":"awaiting_approval"}'),
        ]:
            with self.assertRaises(ValueError):
                self.manager.envelope(code, out)
        self.assertEqual(
            self.manager.envelope(
                2, b'{"schema_version":1,"status":"awaiting_approval"}'
            )["status"],
            "awaiting_approval",
        )

    def test_real_import_partial_selection_worktrees_idempotency_stale_plan(self):
        if not SOURCE.exists():
            self.skipTest("Optional local Jobenu backend reference unavailable")
        self.assertTrue(self.manager.capability(str(SOURCE))["available"])
        ident = self.upload()
        options = self.options(ident)
        before = git(self.root, "rev-parse", "HEAD")
        preview = self.manager.preview(ident, options)
        self.assertEqual(len(preview["plan"]["entries"]), 1)
        selected = json.loads(
            (self.manager.folder(ident) / "selected.json").read_text()
        )
        self.assertEqual(selected["applications"][0], EXPORT["applications"][0])
        self.assertEqual(
            len(
                json.loads((self.manager.folder(ident) / "original.json").read_text())[
                    "applications"
                ]
            ),
            2,
        )
        with self.assertRaises(ValueError):
            self.manager.start(ident, "stale")
        self.manager.start(ident, preview["plan"]["plan_id"])
        deadline = time.monotonic() + 60
        while ident in self.manager.running and time.monotonic() < deadline:
            time.sleep(0.05)
        result = self.manager.public(self.manager.record(ident))
        self.assertEqual(result["status"], "imported", result)
        entry = result["entries"][0]
        self.assertEqual(
            self.ws.location(entry["branch"]), Path(entry["workspace"]).resolve()
        )
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), before)
        preview = self.manager.preview(ident, options)
        self.assertEqual(preview["plan"]["entries"][0]["action"], "existing")
        self.assertNotIn("--rerun", self.manager.record(ident)["args"])

    def test_missing_backend_and_busy_guards(self):
        self.assertFalse(self.manager.capability(str(self.root))["available"])
        ident = self.upload()
        self.manager.running.add(ident)
        try:
            with self.assertRaises(ValueError):
                self.manager.discard(ident)
            with self.assertRaises(ValueError):
                self.manager.preview(ident, self.options(ident))
        finally:
            self.manager.running.clear()

    def test_preserves_native_approval_and_partial_failure_states(self):
        ident = self.upload()
        r = self.manager.record(ident)
        r.update(
            plan={"plan_id": "p", "entries": []},
            args=["import", "jobenu", "selected.json"],
            fileHash="x",
            status="running",
        )
        self.manager.save(r)
        self.manager.running.add(ident)
        self.manager.environments[ident] = (["fixture"], {})
        output = {
            "schema_version": 1,
            "status": "failed",
            "results": [
                {
                    "key": "a",
                    "company": "One",
                    "position": "Role",
                    "branch": "one",
                    "status": "awaiting_requirements_approval",
                },
                {
                    "key": "b",
                    "company": "Two",
                    "position": "Role",
                    "branch": "two",
                    "status": "failed",
                },
            ],
        }
        with patch.object(
            self.manager, "invoke", return_value=(1, json.dumps(output).encode(), b"")
        ):
            self.manager._run(r)
        self.assertEqual(
            [e["status"] for e in self.manager.public(r)["entries"]],
            ["awaiting_requirements_approval", "failed"],
        )

    def test_preview_and_execution_share_options_and_failed_preview_revokes_consent(
        self,
    ):
        ident = self.upload()
        options = self.options(ident)
        options.update(run=True, approval="auto", newRevision=True, rerun=True)
        plan = {
            "schema_version": 1,
            "status": "planned",
            "plan_id": "backend-plan",
            "entries": [],
        }
        calls = []

        def invoke(command, env, args, **kwargs):
            calls.append((list(command), dict(env), list(args)))
            return (
                0,
                json.dumps(
                    plan
                    if "--dry-run" in args
                    else {"schema_version": 1, "status": "complete", "results": []}
                ).encode(),
                b"",
            )

        with (
            patch.object(
                self.manager,
                "command",
                return_value=(["fixture"], {"EXISTING": "captured"}),
            ),
            patch.object(self.manager, "invoke", side_effect=invoke),
        ):
            self.manager.preview(ident, options)
            self.manager.start(ident, "backend-plan")
            deadline = time.monotonic() + 5
            while ident in self.manager.running and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(calls[0][0:2], calls[1][0:2])
            self.assertEqual(calls[0][2][:-1], calls[1][2][:-3])
            self.assertIn("--rerun", calls[0][2])
            self.assertIn("--new-revision", calls[0][2])
            self.assertIn("auto", calls[0][2])
            self.manager.preview(ident, options)
            with patch.object(
                self.manager, "invoke", side_effect=ValueError("invalid backend")
            ):
                with self.assertRaises(ValueError):
                    self.manager.preview(ident, options)
            with self.assertRaises(ValueError):
                self.manager.start(ident, "backend-plan")
            self.manager.listing()

    def test_document_decisions_use_exact_native_revision_and_workspace(self):
        ident = self.upload()
        r = self.manager.record(ident)
        row = {"pending": {"step": "adapt", "revision": "fc-exact"}}

        def invoke(command, env, args, **kw):
            if args[1] == "show":
                return 0, b'{"revision":"fc-exact"}', b""
            self.assertEqual(args, ["facts", "approve", "adapt", "fc-exact"])
            self.assertEqual(kw["cwd"], self.root)
            return 0, b"", b""

        with (
            patch.object(self.manager, "target", return_value=(r, row, self.root)),
            patch.object(self.manager, "command", return_value=(["fixture"], {})),
            patch.object(self.manager, "invoke", side_effect=invoke),
        ):
            with self.assertRaises(ValueError):
                self.manager.decide(ident, "k", "approve", "fc-stale")
            self.assertTrue(
                self.manager.decide(ident, "k", "approve", "fc-exact")["saved"]
            )

    def test_restart_marks_active_batch_interrupted_and_requires_fresh_preview(self):
        ident = self.upload()
        r = self.manager.record(ident)
        r["status"] = "running"
        self.manager.save(r)
        restarted = JobenuImports(self.ws)
        self.assertEqual(restarted.listing()["batches"][0]["status"], "interrupted")
        with self.assertRaises(ValueError):
            restarted.start(ident, "old")

    def test_canonical_approval_is_separate_and_never_uses_factual_flags(self):
        ident = self.upload()
        r = self.manager.record(ident)

        def invoke(command, env, args, **kw):
            if args == ["requirements", "show"]:
                return 0, b'{"revision":{"revision":"canonical-exact"}}', b""
            self.assertEqual(args, ["requirements", "approve", "canonical-exact"])
            return 0, b"Approved", b""

        with (
            patch.object(self.manager, "target", return_value=(r, {}, self.root)),
            patch.object(self.manager, "command", return_value=(["fixture"], {})),
            patch.object(self.manager, "invoke", side_effect=invoke),
        ):
            with self.assertRaises(ValueError):
                self.manager.decide(ident, "k", "approve", "stale")
            with self.assertRaises(ValueError):
                self.manager.decide(ident, "k", "reject", "canonical-exact")
            self.assertTrue(
                self.manager.decide(ident, "k", "approve", "canonical-exact")["saved"]
            )

    def test_progress_reads_native_index_and_public_logs_redact_session_keys(self):
        ident = self.upload()
        r = self.manager.record(ident)
        r.update(
            status="running",
            plan={"entries": [{"key": "k", "fingerprint": "f"}]},
            error="fixture-session-secret",
        )
        index = self.root / ".vita/imports/jobenu/index.json"
        index.parent.mkdir(parents=True)
        index.write_text(
            json.dumps(
                {
                    "applications": {
                        "k": {
                            "versions": {
                                "f": {
                                    "status": "running",
                                    "current_step": "adapt",
                                    "completed_steps": ["extract", "analyze"],
                                }
                            }
                        }
                    }
                }
            )
        )
        self.manager.environments[ident] = (
            ["fixture"],
            {"OPENAI_API_KEY": "fixture-session-secret"},
        )
        self.assertEqual(self.manager.public(r)["entries"][0]["current_step"], "adapt")
        (self.manager.folder(ident) / "execution.log").write_text(
            "fixture-session-secret"
        )
        self.assertNotIn("fixture-session-secret", self.manager.log(ident)["text"])
        self.assertNotIn("fixture-session-secret", json.dumps(self.manager.public(r)))
        (self.root / ".env").write_text('SERVICE_API_KEY="fixture-dotenv-secret"')
        self.assertNotIn(
            "fixture-dotenv-secret",
            self.manager.clean_report({"text": "fixture-dotenv-secret"}, {})["text"],
        )

    def test_saved_stage_preferences_use_native_environment_and_aliases_preserve_config(
        self,
    ):
        ident = self.upload()
        settings = {
            "default": {
                "provider": "codex",
                "model": "fixture-shared",
                "reasoning": "high",
                "connection": "",
            },
            "steps": {
                "adapt": {
                    "provider": "codex",
                    "model": "fixture-adapt",
                    "reasoning": "low",
                    "connection": "",
                }
            },
        }
        saved = self.ws.root / "ai-settings" / (digest("master") + ".json")
        saved.parent.mkdir(parents=True)
        saved.write_text(json.dumps(settings))
        plan = {
            "schema_version": 1,
            "status": "planned",
            "plan_id": "preferences",
            "entries": [],
        }
        with (
            patch.object(self.ws, "ai_settings", return_value=settings),
            patch.object(self.manager, "command", return_value=(["fixture"], {})),
            patch.object(
                self.manager, "invoke", return_value=(0, json.dumps(plan).encode(), b"")
            ),
        ):
            self.manager.preview(ident, self.options(ident))
        env = self.manager.environments[ident][1]
        self.assertEqual(env["ANALYSIS_MODEL"], "fixture-shared")
        self.assertEqual(env["ADAPT_MODEL"], "fixture-adapt")
        self.assertNotIn("VITA_TREE_REASONING", env)
        self.assertNotIn("--model", self.manager.record(ident)["args"])
        config = self.root / ".vita/extensions.json"
        config.parent.mkdir(exist_ok=True)
        config.write_text(json.dumps({"language_map": {"sv": "Swedish"}}))
        self.manager.alias("Data Engineer", "data")
        self.assertEqual(
            json.loads(config.read_text())["language_map"], {"sv": "Swedish"}
        )
        self.assertEqual(
            json.loads(config.read_text())["role_aliases"]["Data Engineer"], "data"
        )

    def test_review_reservation_blocks_only_affected_branch_and_releases_on_failure(
        self,
    ):
        ident = self.upload()
        r = self.manager.record(ident)
        row = {"branch": "master", "pending": {"step": "adapt", "revision": "exact"}}

        def invoke(*args, **kw):
            with self.assertRaises(ConflictError):
                self.ws.busy("master")
            self.ws.busy("another")
            raise ValueError("fixture native failure")

        with (
            patch.object(self.manager, "target", return_value=(r, row, self.root)),
            patch.object(self.manager, "command", return_value=(["fixture"], {})),
            patch.object(self.manager, "invoke", side_effect=invoke),
        ):
            with self.assertRaisesRegex(ValueError, "fixture native failure"):
                self.manager.decide(ident, "k", "approve", "exact")
        self.assertFalse(self.manager.reviewing)
        self.ws.busy("master")

    def test_failed_worktree_creation_keeps_shared_native_git_log_accessible(self):
        ident = self.upload()
        log = self.root / ".vita/imports/jobenu/git.log"
        log.parent.mkdir(parents=True)
        log.write_text("Synthetic Git permission diagnostic")
        r = self.manager.record(ident)
        r.update(
            status="failed",
            result={"results": [{"key": "failed", "execution_log": str(log)}]},
        )
        self.manager.save(r)
        self.assertIn(
            "permission diagnostic", self.manager.log(ident, "failed")["text"]
        )
