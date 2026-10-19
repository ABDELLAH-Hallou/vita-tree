from __future__ import annotations

import subprocess
import socket
import os
import json
import threading
from unittest.mock import patch
from urllib.request import urlopen, build_opener, ProxyHandler
import tempfile
import unittest
from pathlib import Path

from vita_tree.server import VitaTreeServer, branch_content_payload, branch_payload, resolve_repository
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

    def new_server(self, port=0):
        return VitaTreeServer(('127.0.0.1', port), self.repository, 'main.tex',
                              log_dir=self.repository/'.git/test-server-logs')

    def test_duplicate_server_is_rejected_before_loading_history(self):
        first=self.new_server()
        worker=threading.Thread(target=first.serve_forever,daemon=True);worker.start()
        record={'id':'e'*32,'branch':'master','status':'running','step':'analyze','reviewed':False,'stages':[]}
        first.workspace.jobs[record['id']]=record;first.workspace._persist_job(record)
        history=first.workspace.root/'job-history'/('e'*32+'.json')
        before=history.read_bytes()
        try:
            with patch('vita_tree.workspace.Workspace') as workspace:
                with self.assertRaisesRegex(RuntimeError,'Stop the existing server'):
                    self.new_server(first.server_port)
                workspace.assert_not_called()
            self.assertEqual(history.read_bytes(),before)
            self.assertEqual(first.workspace.get_job(record['id'])['status'],'running')
            opener=build_opener(ProxyHandler({}))
            with opener.open(f'http://127.0.0.1:{first.server_port}/health',timeout=5) as response:
                self.assertTrue(json.load(response)['ok'])
        finally:
            first.shutdown();first.server_close();worker.join()

    def test_existing_legacy_reuse_socket_cannot_be_shared(self):
        with socket.socket() as legacy:
            legacy.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            legacy.bind(('127.0.0.1',0));legacy.listen()
            with patch('vita_tree.workspace.Workspace') as workspace:
                with self.assertRaisesRegex(RuntimeError,'another --port'):
                    self.new_server(legacy.getsockname()[1])
                workspace.assert_not_called()

    @unittest.skipUnless(os.name=='nt','Windows exclusive socket semantics')
    def test_another_process_cannot_reuse_exclusive_server_port(self):
        import sys
        first=self.new_server()
        try:
            self.assertEqual(first.socket.getsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE),1)
            code="""import socket,sys
s=socket.socket()
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
try:
 s.bind(('127.0.0.1',int(sys.argv[1])))
 s.listen()
except OSError as error:
 sys.exit(0 if error.winerror in (10013,10048) else 2)
else:
 sys.exit(1)
finally:
 s.close()
"""
            process=subprocess.run([sys.executable,'-B','-c',code,str(first.server_port)],capture_output=True,timeout=10)
            self.assertEqual(process.returncode,0,process.stderr.decode())
        finally:first.server_close()

    def test_failed_workspace_initialization_releases_reserved_port(self):
        probe=self.new_server();port=probe.server_port;probe.server_close()
        with patch('vita_tree.workspace.Workspace',side_effect=RuntimeError('fixture startup failure')):
            with self.assertRaisesRegex(RuntimeError,'fixture startup failure'):self.new_server(port)
        restarted=self.new_server(port)
        restarted.server_close()

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
