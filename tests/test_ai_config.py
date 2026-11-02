import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from support import cleanup_repo, init_repo
from vita_tree.ai_config import clean_settings, effective_settings, stage_environment
from vita_tree.workspace import Workspace
from vita_tree.outcomes import safe_outcome
from vita_tree.fallback import capabilities as fallback_capabilities


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

    def test_backup_configuration_and_credentials_are_captured_without_leaking_other_keys(self):
        capabilities = {'version': 'provider-fallback/1', 'default_categories': ['timeout'],
                        'allowed_categories': ['timeout', 'invalid_model']}
        backup = {'provider': 'gemini', 'model': 'fixture-backup', 'categories': ['timeout']}
        with patch('vita_tree.providers.fallback_capabilities', return_value=capabilities):
            saved = self.workspace.save_ai_settings('master', {'default': {
                'provider': 'openai', 'model': 'fixture-primary', 'backup': backup}})
        route = effective_settings(saved, {'adapt'})['adapt']
        env = stage_environment({'GEMINI_API_KEY': 'backup-secret', 'ANTHROPIC_API_KEY': 'unrelated'}, route, 'primary-secret')
        self.assertEqual(env['GEMINI_API_KEY'], 'backup-secret')
        self.assertEqual(env['OPENAI_API_KEY'], 'primary-secret')
        self.assertNotIn('ANTHROPIC_API_KEY', env)
        self.assertEqual(env['VITA_FALLBACK_PROVIDER'], 'gemini')
        self.assertEqual(env['VITA_FALLBACK_MODEL'], 'fixture-backup')
        self.assertEqual(env['VITA_FALLBACK_CATEGORIES'], 'timeout')
        self.assertEqual(env['ADAPT_MODEL'], 'fixture-primary')
        self.assertEqual(env['ADAPT_FALLBACK_ENABLED'], 'true')
        self.assertNotIn('secret', json.dumps(saved))

    def test_backup_rejects_unsupported_backend_invalid_policy_and_same_route(self):
        caps = {'version': 'provider-fallback/1', 'default_categories': ['timeout'], 'allowed_categories': ['timeout']}
        for backup, contract in [({'provider': 'codex', 'model': 'backup'}, None),
                                 ({'provider': 'openai', 'model': 'primary'}, caps),
                                 ({'provider': 'codex', 'model': ''}, caps),
                                 ({'provider': 'codex', 'model': 'backup', 'categories': ['source_conflict']}, caps)]:
            with self.subTest(backup=backup), patch('vita_tree.providers.fallback_capabilities', return_value=contract), self.assertRaises(ValueError):
                clean_settings(self.workspace, 'master', {'default': {'provider': 'openai', 'model': 'primary', 'backup': backup}})

    def test_new_primary_clears_old_stage_fallback_settings(self):
        env = stage_environment({'ADAPT_MODEL': 'old', 'ADAPT_FALLBACK_ENABLED': 'true',
                                 'ADAPT_FALLBACK_MODEL': 'old-backup'},
                                {'provider': 'gemini', 'model': 'new', 'reasoning': '', 'connection': ''})
        self.assertEqual(env['ADAPT_MODEL'], 'new')
        self.assertEqual(env['ADAPT_PROVIDER'], 'gemini')
        self.assertEqual(env['ADAPT_FALLBACK_ENABLED'], 'false')
        self.assertNotIn('ADAPT_FALLBACK_MODEL', env)

    def test_fallback_evidence_survives_parent_sanitization_and_redacts_unknown_fields(self):
        raw = {'schema_version': 1, 'status': 'success', 'attempts': [
            {'number': 1, 'category': 'timeout', 'kind': 'initial'},
            {'number': 2, 'category': 'valid', 'kind': 'fallback'}],
            'routing': {'version': 'provider-fallback/1',
                        'requested': {'provider': 'openai', 'model': 'fixture-primary'},
                        'effective': {'provider': 'gemini', 'model': 'fixture-backup', 'api_key': 'never-public'},
                        'chain': [], 'raw_response': 'never-public'}}
        outcome = {'status': 'success', 'verified': True, 'backend': safe_outcome(raw)}
        sanitized = self.workspace._safe_outcomes({'analyze': outcome})
        self.assertEqual(sanitized['analyze']['backend']['routing']['effective']['model'], 'fixture-backup')
        self.assertEqual(sanitized['analyze']['backend']['attempts'][1]['kind'], 'fallback')
        self.assertNotIn('never-public', json.dumps(sanitized))

    def test_backup_checkpoint_configuration_survives_history_restart(self):
        import time
        route = {'provider': 'openai', 'model': 'primary', 'reasoning': '', 'connection': '',
                 'backup': {'provider': 'gemini', 'model': 'backup@revision', 'reasoning': '', 'connection': '', 'categories': ['timeout']}}
        record = dict(id='a'*32, branch='master', status='failed', createdAt=time.time(),
                      stepConfig={'analyze': route}, stages=[], outcomes={}, attempt=1)
        self.workspace._persist_job(record)
        restored = Workspace(self.root)
        try:
            self.assertEqual(restored.jobs[record['id']]['stepConfig']['analyze']['backup'], route['backup'])
        finally:
            restored.close()

    def test_legacy_installation_does_not_probe_an_unsupported_command(self):
        self.workspace.vita_source = self.root / 'legacy-source'
        with patch.object(self.workspace, 'vita_command', return_value=['synthetic-cli']), patch('vita_tree.fallback.subprocess.run') as invoke:
            self.assertIsNone(fallback_capabilities(self.workspace))
        invoke.assert_not_called()

    def test_step_can_disable_shared_backup_and_keep_it_disabled_after_reload(self):
        contract = {'version': 'provider-fallback/1', 'default_categories': ['timeout'], 'allowed_categories': ['timeout']}
        with patch('vita_tree.providers.fallback_capabilities', return_value=contract):
            saved = self.workspace.save_ai_settings('master', {'default': {
                'provider': 'openai', 'model': 'primary', 'backup': {'provider': 'gemini', 'model': 'backup'}},
                'steps': {'cover': {'backup': None}}})
            restored = self.workspace.ai_settings('master')
        self.assertEqual(saved, restored)
        self.assertIsNone(effective_settings(restored, {'cover'})['cover']['backup'])
        self.assertEqual(effective_settings(restored, {'analyze'})['analyze']['backup']['model'], 'backup')
