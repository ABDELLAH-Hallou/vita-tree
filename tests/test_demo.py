"""Tests for demo repository creation, capability checks, and guided setup (R54, R55, R56, I24, B17)."""
import io
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from support import cleanup_repo
from vita_tree.cli import build_parser
from vita_tree.sample import prepare_demo_repository, SAMPLE_MAIN_TEX, SAMPLE_JOB_MD
from vita_tree.setup import check_prerequisites, run_setup, SetupLock


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".vita-tree-test-", dir=Path.cwd())
        self.root = Path(self.temp.name)

    def tearDown(self):
        cleanup_repo(self.temp)

    def test_prepare_demo_repository_creates_committed_baseline(self):
        demo_dir = self.root / "sample-repo"
        result = prepare_demo_repository(demo_dir)
        self.assertEqual(result, demo_dir.resolve())
        self.assertTrue((demo_dir / ".git").is_dir())
        self.assertTrue((demo_dir / "main.tex").is_file())
        self.assertTrue((demo_dir / "job.md").is_file())
        self.assertEqual((demo_dir / "main.tex").read_text(encoding="utf-8"), SAMPLE_MAIN_TEX)
        self.assertEqual((demo_dir / "job.md").read_text(encoding="utf-8"), SAMPLE_JOB_MD)

        log = subprocess.run(
            ["git", "-C", str(demo_dir), "log", "-1", "--format=%s"],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(log.stdout.strip(), "Initial sample CV and job description")

    def test_repeat_demo_launch_preserves_edits(self):
        demo_dir = self.root / "sample-repo"
        prepare_demo_repository(demo_dir)

        custom_cv = SAMPLE_MAIN_TEX + "\n% User edit in Structure/LaTeX editor\n"
        (demo_dir / "main.tex").write_text(custom_cv, encoding="utf-8")

        # Second launch must preserve user edits
        prepare_demo_repository(demo_dir)
        self.assertEqual((demo_dir / "main.tex").read_text(encoding="utf-8"), custom_cv)

    def test_prepare_demo_repository_handles_spaces_and_unicode(self):
        demo_dir = self.root / "dymo CV espace et accenté"
        result = prepare_demo_repository(demo_dir)
        self.assertTrue(result.is_dir())
        self.assertTrue((result / "main.tex").is_file())

    def test_missing_git_raises_clear_error(self):
        with patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Git is required"):
                prepare_demo_repository(self.root / "no-git-demo")

    def test_cli_parser_has_demo_and_setup(self):
        parser = build_parser()
        args = parser.parse_args(["demo", "--no-browser", "--port", "9999"])
        self.assertEqual(args.command, "demo")
        self.assertTrue(args.no_browser)
        self.assertEqual(args.port, 9999)

        setup_args = parser.parse_args(["setup", "--check"])
        self.assertEqual(setup_args.command, "setup")
        self.assertTrue(setup_args.check)

    def test_check_prerequisites_detects_tools(self):
        prereqs = check_prerequisites()
        self.assertTrue(prereqs["python"]["ok"])
        self.assertTrue(prereqs["git"]["ok"])
        self.assertIn("engines", prereqs["tex"])

    def test_run_setup_check_only_returns_status_code(self):
        code = run_setup(check_only=True)
        self.assertEqual(code, 0)

        with patch("shutil.which", return_value=None):
            failed_code = run_setup(check_only=True)
            self.assertEqual(failed_code, 1)

    def test_setup_lock_single_writer_and_release(self):
        target = self.root / "setup-target"
        with SetupLock(target):
            self.assertTrue((target / ".vita-tree-setup.lock").is_file())
            # Second attempt to acquire same lock must fail
            second_lock = SetupLock(target)
            self.assertFalse(second_lock.acquire(timeout=0.2))

        # After exiting context manager, lock must be released
        self.assertFalse((target / ".vita-tree-setup.lock").is_file())
        second_lock = SetupLock(target)
        self.assertTrue(second_lock.acquire(timeout=0.2))
        second_lock.release()

    def test_setup_race_two_starts_asserts_one_writer_and_recoverable_second(self):
        target = self.root / "race-target"
        lock1 = SetupLock(target)
        self.assertTrue(lock1.acquire(timeout=1.0))
        try:
            # Second process attempting setup returns exit code 2 (conflict)
            code2 = run_setup(auto_demo=True, target=target)
            self.assertEqual(code2, 2)
        finally:
            lock1.release()

        # After first lock is released, target is recoverable and succeeds
        code3 = run_setup(auto_demo=True, target=target)
        self.assertEqual(code3, 0)
        self.assertTrue((target / "main.tex").is_file())

    def test_no_synthetic_secret_canaries_in_output(self):
        canary = "CANARY_SECRET_TOKEN_9876543210"
        with patch.dict(os.environ, {"SECRET_CANARY": canary}):
            buffer = io.StringIO()
            with patch("sys.stdout", buffer):
                run_setup(check_only=True)
            output = buffer.getvalue()
            self.assertNotIn(canary, output)

    def test_readme_description_and_links_compliance(self):
        readme_path = Path(__file__).resolve().parents[1] / "README.md"
        content = readme_path.read_text(encoding="utf-8")

        # Must have quick start and vt demo near the top
        self.assertIn("## Quick start", content)
        self.assertIn("vt demo", content)

        # Must have screenshot with alt text and absolute HTTPS URL
        screenshot_match = re.search(r'!\[([^\]]+)\]\((https://[^\)]+\.png)\)', content)
        self.assertIsNotNone(screenshot_match, "README must include screenshot with alt text and HTTPS URL")
        self.assertTrue(len(screenshot_match.group(1).strip()) > 10, "Alt text must be descriptive")

        # Must NOT contain maintainer token secrets or publish runbook
        self.assertNotIn("TEST_PYPI_API_TOKEN", content)
        self.assertNotIn("PYPI_API_TOKEN", content)
        self.assertNotIn("RELEASE_PLEASE_TOKEN", content)

        # Security link must be absolute HTTPS
        security_links = re.findall(r'\[(?:Security policy|Security)\]\(([^)]+)\)', content, re.IGNORECASE)
        self.assertTrue(len(security_links) > 0, "README must link to Security policy")
        for link in security_links:
            self.assertTrue(link.startswith("https://"), f"Security link must be absolute HTTPS: {link}")

        # Changelog link must be absolute HTTPS
        changelog_links = re.findall(r'\[Changelog\]\(([^)]+)\)', content)
        self.assertTrue(len(changelog_links) > 0, "README must link to Changelog")
        for link in changelog_links:
            self.assertTrue(link.startswith("https://"), f"Changelog link must be absolute HTTPS: {link}")

    def test_security_policy_and_releasing_docs_exist_and_link(self):
        root = Path(__file__).resolve().parents[1]
        security_md = root / "SECURITY.md"
        releasing_md = root / ".github" / "RELEASING.md"

        self.assertTrue(security_md.is_file(), "SECURITY.md must exist")
        self.assertTrue(releasing_md.is_file(), ".github/RELEASING.md must exist")

        sec_content = security_md.read_text(encoding="utf-8")
        self.assertIn("LOCAL_WORKFLOW_AUDIT.md", sec_content)
        self.assertIn("127.0.0.1", sec_content)

        rel_content = releasing_md.read_text(encoding="utf-8")
        self.assertIn("TestPyPI", rel_content)
        self.assertIn("PyPI", rel_content)
