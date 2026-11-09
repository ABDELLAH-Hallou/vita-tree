"""First-run behavior for the installed demo and guided setup."""

from contextlib import contextmanager
import io
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from vita_tree import setup
from vita_tree.sample import prepare_demo_repository


class DemoTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_demo_reopens_committed_utf8_sample_with_edits_intact(self):
        demo = self.root / "CV example é"
        self.assertEqual(prepare_demo_repository(demo), demo.resolve())
        document = demo / "main.tex"
        baseline = subprocess.check_output(
            ["git", "-C", str(demo), "show", "HEAD:main.tex"], encoding="utf-8"
        )
        self.assertEqual(baseline, document.read_text(encoding="utf-8"))
        document.write_text(baseline + "% local edit\n", encoding="utf-8")
        self.assertEqual(prepare_demo_repository(demo), demo.resolve())
        self.assertTrue(document.read_text(encoding="utf-8").endswith("% local edit\n"))

    def test_demo_refuses_existing_project_and_preserves_staging(self):
        repo = self.root / "existing"
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        draft = repo / "draft.txt"
        draft.write_text("Synthetic draft", encoding="utf-8")
        command = ["git", "-C", str(repo)]
        subprocess.run([*command, "add", "draft.txt"], check=True)
        status = subprocess.check_output([*command, "status", "--porcelain"])
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            prepare_demo_repository(repo)
        self.assertEqual(subprocess.check_output([*command, "status", "--porcelain"]), status)
        self.assertEqual(draft.read_text(encoding="utf-8"), "Synthetic draft")
        self.assertFalse((repo / "main.tex").exists())

    def test_missing_git_reports_next_action(self):
        with patch("vita_tree.sample.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Install Git"):
                prepare_demo_repository(self.root / "demo")


class GuidedSetupTests(unittest.TestCase):
    def test_prompt_is_available_during_install(self):
        steps = []
        python = Path("python")
        repo = Path("CV é")

        @contextmanager
        def install(release, ai):
            steps.append("install started")
            yield python, lambda: steps.append("install finished")

        def answer(prompt):
            steps.append("prompt answered")
            return "n" if "AI" in prompt or "PDF" in prompt else str(repo)

        with (
            patch.object(setup, "installation", install),
            patch.object(setup.shutil, "which", side_effect=lambda tool: "git" if tool == "git" else None),
            patch("builtins.input", side_effect=answer),
            patch.object(setup, "launch", return_value=0) as launch,
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            self.assertEqual(setup.main(["--release", "1.2.3", "--no-browser"]), 0)
        self.assertEqual(steps, ["prompt answered", "install started", "prompt answered",
                                 "prompt answered", "install finished"])
        launch.assert_called_once_with(python, repo, 0, True)

    def test_setup_failure_does_not_launch(self):
        @contextmanager
        def install(release, ai):
            raise RuntimeError("Install failed. Retry when online.")
            yield

        with (
            patch.object(setup, "installation", install),
            patch.object(setup.shutil, "which", return_value="git"),
            patch.object(setup, "launch") as launch,
            patch("sys.stdout", new_callable=io.StringIO),
            patch("sys.stderr", new_callable=io.StringIO) as errors,
        ):
            self.assertEqual(setup.main(["--release", "1.2.3", "--non-interactive"]), 1)
        launch.assert_not_called()
        self.assertIn("Retry when online", errors.getvalue())

    def test_retry_keeps_the_project_and_ai_selection(self):
        attempts = []

        @contextmanager
        def install(release, ai):
            attempts.append((release, ai))

            def finish():
                if len(attempts) == 1:
                    raise setup.InstallError("Synthetic network failure")

            yield Path("python"), finish

        with (
            patch.object(setup, "installation", install),
            patch.object(setup.shutil, "which", return_value="installed"),
            patch("builtins.input", side_effect=["y", "My CV", "y"]) as prompt,
            patch.object(setup, "launch", return_value=0) as launch,
            patch("sys.stdout", new_callable=io.StringIO),
            patch("sys.stderr", new_callable=io.StringIO),
        ):
            self.assertEqual(setup.main(["--release", "1.2.3"]), 0)
        self.assertEqual(attempts, [("1.2.3", True), ("1.2.3", True)])
        self.assertEqual(prompt.call_count, 3)
        launch.assert_called_once_with(Path("python"), Path("My CV"), 0, False)

    def test_setup_lock_releases_on_failure(self):
        with TemporaryDirectory() as tmp:
            lock = Path(tmp) / "setup.lock"
            with self.assertRaisesRegex(RuntimeError, "already running"):
                with setup.single_writer(lock), setup.single_writer(lock):
                    self.fail("Two writers acquired the same lock")
            with setup.single_writer(lock):
                self.assertTrue(lock.is_file())
