import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from support import cleanup_repo, init_repo
from vita_tree.ai_config import clean_settings, effective_settings, stage_environment
from vita_tree.workspace import Workspace


class AIConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.temp.name))
        self.workspace = Workspace(self.root)

    def tearDown(self):
        self.workspace.close()
        cleanup_repo(self.temp)

    def test_settings_inherit_custom_models_and_reset_cross_provider_fields(self):
        connection = self.workspace.add_connection('Personal', 'openai', 'private-test-key')
        raw = {'default': {'provider': 'openai', 'model': 'custom/model:version', 'connection': connection['id']},
               'steps': {'extract': {'provider': 'gemini', 'model': 'custom-flash'}, 'adapt': {'model': 'writing-model'}}}
        saved = self.workspace.save_ai_settings('master', raw)
        restored = Workspace(self.root).ai_settings('master')
        self.assertEqual(saved, restored)
        routes = effective_settings(saved, {'extract', 'analyze', 'adapt'})
        self.assertEqual(routes['analyze'], saved['default'])
        self.assertEqual(routes['adapt']['connection'], connection['id'])
        self.assertEqual(routes['adapt']['model'], 'writing-model')
        self.assertEqual(routes['extract']['connection'], '')
        self.assertEqual(routes['extract']['reasoning'], '')
        self.assertNotIn('private-test-key', json.dumps(saved))
        self.assertNotIn('private-test-key', ''.join(p.read_text() for p in (self.workspace.root/'ai-settings').glob('*.json')))

    def test_connections_never_return_keys_and_are_session_only(self):
        result = self.workspace.add_connection('Work', 'gemini', 'session-secret-value')
        self.assertEqual(set(result), {'id', 'name', 'provider'})
        self.assertNotIn('session-secret-value', str(self.workspace.list_connections()))
        self.assertEqual(self.workspace.connections.get(result['id'], 'gemini'), 'session-secret-value')
        with self.assertRaises(ValueError):
            self.workspace.connections.get(result['id'], 'openai')
        self.assertEqual(Workspace(self.root).list_connections(), {'connections': []})
        self.workspace.remove_connection(result['id'])
        with self.assertRaises(ValueError):
            self.workspace.connections.get(result['id'], 'gemini')

    def test_invalid_fields_keys_and_routes_are_rejected(self):
        for raw in (None, [], {'apiKey': 'secret'}, {'default': {'apiKey': 'secret'}},
                    {'steps': []}, {'steps': {'unknown': {}}}, {'default': {'provider': []}},
                    {'default': {'provider': 'unknown'}}, {'default': {'model': '--bad'}},
                    {'default': {'model': 'bad\nmodel'}}, {'default': {'connection': '../file'}}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                clean_settings(self.workspace, 'master', raw)
        for name, provider, key in (('', 'openai', 'key'), ('Test', 'codex', 'key'),
                                    ('Test', 'openai', ''), ('Test', 'openai', 'a\nb')):
            with self.assertRaises(ValueError):
                self.workspace.add_connection(name, provider, key)

    def test_stage_environments_do_not_mutate_shared_credentials(self):
        base = {'OPENAI_API_KEY': 'existing-key', 'VITA_TREE_REASONING': 'high'}
        route = {'provider': 'openai', 'model': 'custom', 'reasoning': '', 'connection': ''}
        one = stage_environment(base, route, 'first-key')
        two = stage_environment(base, route, 'second-key')
        inherited = stage_environment(base, route)
        self.assertEqual(one['OPENAI_API_KEY'], 'first-key')
        self.assertEqual(two['OPENAI_API_KEY'], 'second-key')
        self.assertEqual(inherited['OPENAI_API_KEY'], 'existing-key')
        self.assertEqual(base, {'OPENAI_API_KEY': 'existing-key', 'VITA_TREE_REASONING': 'high'})
        self.assertEqual(one['VITA_TREE_REASONING'], '')
        self.assertEqual(one['ENABLE_JD_EXTRACTION'], 'false')
