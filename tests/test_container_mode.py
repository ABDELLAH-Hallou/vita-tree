"""Docker opts in to interface binding without disabling browser protection."""
import json
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
from pathlib import Path

from support import init_repo, cleanup_repo
from vita_tree.server import VitaTreeServer


class ContainerModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.tmp.name))

    def tearDown(self):
        cleanup_repo(self.tmp)

    def test_wildcard_requires_explicit_container_mode(self):
        with self.assertRaises(ValueError):
            VitaTreeServer(('0.0.0.0', 0), self.root, 'main.tex')

    def test_container_preserves_host_origin_and_token_checks(self):
        server = VitaTreeServer(('0.0.0.0', 0), self.root, 'main.tex',
                               container_mode=True, public_port=18765)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        opener = build_opener(ProxyHandler({}))
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            def request(path, host='localhost:18765', origin=None, data=None):
                headers = {'Host': host}
                if origin: headers['Origin'] = origin
                return opener.open(Request(url+path, headers=headers, data=data), timeout=5)
            with request('/api/session') as response:
                self.assertTrue(json.load(response)['token'])
            for host, origin in [('evil.invalid:18765', None), ('localhost:18765', 'http://evil.invalid')]:
                with self.assertRaises(HTTPError) as failed:
                    request('/api/session', host, origin)
                self.assertEqual(failed.exception.code, 403)
            with self.assertRaises(HTTPError) as failed:
                request('/api/jobs/review', data=b'{}')
            self.assertEqual(failed.exception.code, 403)
        finally:
            server.shutdown(); server.server_close(); worker.join()
