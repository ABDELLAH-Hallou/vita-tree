"""Synthetic Jobenu preview/progress/approval UI; no providers or personal files."""

import json, threading, time
from pathlib import Path
from unittest.mock import patch
from playwright.sync_api import sync_playwright, expect
from support import init_repo, SOURCE, set_theme, git
from vita_tree.server import VitaTreeServer
from vita_tree.workspace import digest
from test_jobenu import EXPORT


def main():
    root = init_repo(Path(".test-artifacts/jobenu-ui-" + str(time.time_ns())).resolve())
    server = VitaTreeServer(
        ("127.0.0.1", 0), root, "main.tex", log_dir=root / ".git/test-logs"
    )
    manager = server.workspace.jobenu
    workspace = root / ".vita/imports/jobenu/worktrees/fixture"
    workspace.parent.mkdir(parents=True)
    git(root, "worktree", "add", "-b", "native-returned-name", str(workspace), "master")
    entry = {
        "key": "key",
        "fingerprint": "hash",
        "company": "Sample Co",
        "position": "Data Engineer",
        "branch": "native-returned-name",
        "action": "existing",
        "workspace": str(workspace),
        "status": "running",
        "current_step": "adapt",
        "completed_steps": ["extract", "analyze"],
    }

    def invoke(command, env, args, **kw):
        if "--help" in args:
            return 0, b"--json --plan-id --approve-plan", b""
        if args[0] == "facts":
            return (
                0,
                json.dumps(
                    {
                        "revision": "fc-fixture",
                        "changes": [
                            {
                                "reason": "unverified_semantic_change",
                                "kind": "semantic_or_factual",
                                "original": "Original Python experience",
                                "proposed": "Proposed Python experience",
                                "verification": "confirmation_required",
                                "source_fact_ids": [],
                            }
                        ],
                    }
                ).encode(),
                b"",
            )
        if args[0] == "requirements":
            return (
                0,
                json.dumps(
                    {
                        "approval_status": "draft",
                        "revision": {
                            "revision": "criteria-fixture",
                            "requirements": [
                                {
                                    "criterion": "Python experience",
                                    "classification": "required",
                                    "category": "hard_skills",
                                    "source_refs": [],
                                }
                            ],
                            "employment_conditions": [
                                {
                                    "criterion": "Remote work",
                                    "classification": "preferred",
                                    "category": "employment_condition",
                                    "source_refs": [],
                                }
                            ],
                        },
                    }
                ).encode(),
                b"",
            )
        if "--dry-run" in args:
            return (
                0,
                json.dumps(
                    {
                        "schema_version": 1,
                        "status": "planned",
                        "plan_id": "native-plan",
                        "entries": [entry],
                    }
                ).encode(),
                b"",
            )
        manager_test_ready.set()
        manager_test_release.wait(20)
        return (
            2,
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "awaiting_approval",
                    "results": [
                        {
                            **entry,
                            "status": "awaiting_approval",
                            "pending": {"step": "adapt", "revision": "fc-fixture"},
                        }
                    ],
                }
            ).encode(),
            b"",
        )

    manager_test_ready = threading.Event()
    manager_test_release = threading.Event()
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with (
            patch.object(manager, "invoke", side_effect=invoke),
            patch.object(manager, "command", return_value=(["fixture"], {})),
            sync_playwright() as pw,
        ):
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 950})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.route(
                "**/__fixture_axe.js",
                lambda route: route.fulfill(
                    path=str(Path("node_modules/axe-core/axe.min.js").resolve()),
                    content_type="application/javascript",
                ),
            )
            page.goto(f"http://127.0.0.1:{server.server_port}")
            page.locator("#open-jobenu").click()
            expect(page.locator("#jobenu-import")).to_be_visible()
            page.locator("#jobenu-file").set_input_files(
                {
                    "name": "synthetic-jobs.json",
                    "mimeType": "application/json",
                    "buffer": json.dumps(EXPORT).encode(),
                }
            )
            expect(page.locator("#jobenu-selection tbody tr")).to_have_count(2)
            page.locator("#jobenu-base").fill("master")
            page.locator("#jobenu-preview").click()
            try:
                expect(page.locator("#jobenu-plan")).to_contain_text(
                    "native-returned-name"
                )
            except AssertionError:
                print(
                    "Preview error:", page.locator("#jobenu-error").inner_text(), errors
                )
                raise
            expect(page.locator("#jobenu-start")).to_be_enabled()
            pending_previews = []
            page.route(
                "**/api/jobenu/preview",
                lambda route: pending_previews.append(route),
                times=1,
            )
            with page.expect_request("**/api/jobenu/preview"):
                page.locator("#jobenu-preview").click()
            page.locator("#jobenu-approval").select_option("auto")
            pending_previews[0].fulfill(
                json={
                    "status": "planned",
                    "plan": {"plan_id": "stale-in-flight", "entries": [entry]},
                }
            )
            expect(page.locator("#jobenu-preview")).to_be_enabled()
            expect(page.locator("#jobenu-start")).to_be_disabled()
            expect(page.locator("#jobenu-plan tbody tr")).to_have_count(0)
            page.locator("#jobenu-approval").select_option("human")
            page.locator("#jobenu-preview").click()
            expect(page.locator("#jobenu-start")).to_be_enabled()
            page.add_script_tag(url="/__fixture_axe.js")
            violations = page.evaluate(
                "async()=> (await axe.run('#jobenu-import',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,help:v.help,nodes:v.nodes.map(n=>n.target)}))"
            )
            assert not violations, violations
            page.screenshot(
                path=".test-artifacts/jobenu-preview-light.png", full_page=True
            )
            page.locator("#jobenu-approval").select_option("auto")
            expect(page.locator("#jobenu-start")).to_be_disabled()
            page.locator("#jobenu-approval").select_option("human")
            page.locator("#jobenu-preview").click()
            expect(page.locator("#jobenu-start")).to_be_enabled()
            page.locator("#jobenu-start").click()
            expect(page.locator("#jobenu-history")).to_contain_text("In progress")
            set_theme(page, "dark")
            page.screenshot(
                path=".test-artifacts/jobenu-progress-dark.png", full_page=True
            )
            manager_test_release.set()
            expect(
                page.get_by_role("button", name="Review changes", exact=True)
            ).to_be_visible(timeout=30000)
            page.get_by_role("button", name="Review changes", exact=True).click()
            expect(page.locator("#jobenu-review")).to_be_visible()
            expect(page.locator("#jobenu-review-content")).to_contain_text(
                "Original Python experience"
            )
            page.screenshot(path=".test-artifacts/jobenu-approval-dark.png")
            page.locator("#jobenu-approve").click()
            expect(page.locator("#jobenu-review")).not_to_be_visible()
            expect(page.locator("#jobenu-feedback")).to_contain_text("Decision saved")
            ident = manager.listing()["batches"][0]["id"]
            record = manager.record(ident)
            record["result"]["results"][0].pop("pending")
            record["result"]["results"][0]["status"] = "awaiting_requirements_approval"
            manager.save(record)
            page.get_by_role("button", name="Review requirements", exact=True).click()
            expect(page.locator("#jobenu-review-content")).to_contain_text(
                "Python experience"
            )
            expect(page.locator("#jobenu-review-content")).to_contain_text(
                "Employment conditions"
            )
            page.screenshot(path=".test-artifacts/jobenu-requirements-dark.png")
            page.locator("#jobenu-approve").click()
            expect(page.locator("#jobenu-review")).not_to_be_visible()
            page.get_by_role("button", name="Preview resume", exact=True).click()
            expect(page.locator("#jobenu-start")).to_be_enabled()
            expect(page.locator("#jobenu-rerun")).not_to_be_checked()
            violations = page.evaluate(
                "async()=> (await axe.run('#jobenu-import',{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>v.id)"
            )
            assert not violations, violations
            page.set_viewport_size({"width": 390, "height": 844})
            page.locator("#jobenu-base").focus()
            page.evaluate("window.scrollTo(0,0)")
            page.screenshot(
                path=".test-artifacts/jobenu-preview-mobile.png", full_page=True
            )
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
            assert not errors, errors
            browser.close()
    finally:
        manager_test_release.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    print(
        "PASS: Jobenu selection, native preview, stale options, background progress, pending review, resume, themes and narrow viewport."
    )


if __name__ == "__main__":
    main()
