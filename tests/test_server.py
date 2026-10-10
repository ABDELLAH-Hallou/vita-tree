from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from vita_tree.server import branch_content_payload, branch_payload, resolve_repository
from support import cleanup_repo


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary_directory = tempfile.TemporaryDirectory(
            prefix=".vita-tree-test-",
            dir=Path.cwd(),
        )
        cls.repository = Path(cls.temporary_directory.name)

        def git(*args: str) -> None:
            subprocess.run(
                ["git", *args],
                cwd=cls.repository,
                check=True,
                capture_output=True,
            )

        git("init", "-b", "master")
        git("config", "user.name", "vita-tree tests")
        git("config", "user.email", "tests@example.invalid")
        (cls.repository / "main.tex").write_text(
            "\\documentclass{article}\n\\begin{document}\nHello\\end{document}\n",
            encoding="utf-8",
        )
        git("add", "main.tex")
        git("commit", "-m", "Initial document")
        git("update-ref", "refs/remotes/origin/master", "refs/heads/master")

    @classmethod
    def tearDownClass(cls) -> None:
        cleanup_repo(cls.temporary_directory)

    def test_resolves_repository_root(self) -> None:
        self.assertEqual(resolve_repository(self.repository), self.repository.resolve())

    def test_branches_are_unique_and_newest_first(self) -> None:
        branches = branch_payload(self.repository)["branches"]
        names = [branch["name"] for branch in branches]
        timestamps = [branch["timestamp"] for branch in branches]
        self.assertEqual(names, ["master"])
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_reads_main_tex_without_checkout(self) -> None:
        payload = branch_content_payload(self.repository, "master")
        self.assertEqual(payload["path"], "main.tex")
        self.assertIn("\\begin{document}", payload["content"])

    def test_unknown_branch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            branch_content_payload(self.repository, "../../HEAD")


if __name__ == "__main__":
    unittest.main()
