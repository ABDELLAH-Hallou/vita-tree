import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from support import cleanup_repo, git, init_repo
from vita_tree.ai_runner import call_codex, configure
from vita_tree.providers import configured, resolve
from vita_tree.workspace import Workspace


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.temp.name))
        self.workspace = Workspace(self.root)
        self.config = self.root / '.vita/extensions.json'
        self.config.parent.mkdir(exist_ok=True)

    def tearDown(self):
        cleanup_repo(self.temp)

    def write(self, providers):
        self.config.write_text(json.dumps({'llm_providers': providers}), encoding='utf-8')

    def test_all_refs_worktrees_defaults_and_secrets(self):
        self.write({'codex': {'model': 'old-model', 'api_key': 'SECRET'}})
        git(self.root, 'add', '-f', '.vita/extensions.json'); git(self.root, 'commit', '-m', 'Old provider')
        git(self.root, 'update-ref', 'refs/remotes/origin/master', 'HEAD')
        self.write({'gemini': {'model': 'gemini-test'}})
        git(self.root, 'commit', '-am', 'New provider')
        git(self.root, 'branch', 'another')
        self.write({'codex': {'model': 'local-model'}})
        catalog = self.workspace.providers('master')
        self.assertEqual(catalog['refCount'], 3)
        self.assertEqual(catalog['default'], {'provider': 'codex', 'model': 'local-model'})
        self.assertEqual({(o['provider'], o['model']) for o in catalog['options']},
                         {('codex', 'old-model'), ('gemini', 'gemini-test'), ('codex', 'local-model')})
        self.assertNotIn('SECRET', json.dumps(catalog))
        self.assertNotIn('api_key', json.dumps(catalog))
        self.assertEqual(self.workspace.providers('another')['default']['provider'], 'gemini')

    def test_model_reasoning_validation(self):
        self.write({'codex': {'model': 'test-model'}, 'openai': {'model': 'gpt-4-turbo'}})
        with patch.object(self.workspace, 'ai_bridge', return_value=True), patch('vita_tree.providers.codex_efforts', return_value={'test-model': ['low','medium','high']}):
            self.assertEqual(resolve(self.workspace, 'master', 'codex', 'test-model', 'high'), ('codex','test-model','high'))
            for provider, model, effort in [('codex','test-model','ultra'),('openai','gpt-4-turbo','high'),('codex','invented',''),('unknown','','')]:
                with self.assertRaises(ValueError): resolve(self.workspace,'master',provider,model,effort)
            for model, effort in [([], ''), ('test-model', None), ('test-model', [])]:
                with self.assertRaises(ValueError): resolve(self.workspace,'master','codex',model,effort)
        with self.assertRaises(ValueError): resolve(self.workspace,'master','codex','test-model','high')

    def test_malformed_config_is_ignored(self):
        for value in ('[]', 'null', '{', '{"llm_providers":[]}'):
            self.assertEqual(configured(value), [])
        self.assertEqual(configured(json.dumps({'llm_providers': {'_comment': 'secret', 'codex': {'model': '--bad'}, 'openai': {'model': 'valid', 'api_key': 'SECRET'}}})), [('openai','valid')])


class RunnerTests(unittest.TestCase):
    def test_credentials_from_memory_and_default_transport(self):
        original = lambda *args: 'unchanged'
        llm = SimpleNamespace(load_env=lambda: {}, _call_codex_cli=original)
        with patch.dict(os.environ, {'OPENAI_API_KEY':'fixture-key', 'VITA_TREE_REASONING':''}):
            configure(llm)
            self.assertEqual(llm.load_env()['OPENAI_API_KEY'], 'fixture-key')
            self.assertIs(llm._call_codex_cli, original)

    def test_selected_model_effort_and_prompt_reach_codex_without_shell(self):
        llm = SimpleNamespace(_find_codex_cli=lambda:'codex.exe')
        output = Path('.vita/tmp/codex-output.md')
        def fake(command, **kwargs):
            self.assertEqual(command[command.index('--model')+1], 'test-model')
            self.assertEqual(command[command.index('-c')+1], 'model_reasoning_effort="high"')
            self.assertEqual(command[command.index('--sandbox')+1], 'read-only')
            self.assertIn('SYSTEM\n\n==== TASK ====\nUSER', kwargs['input'])
            self.assertNotIn('shell', kwargs)
            return subprocess.CompletedProcess(command, 0)
        with patch('vita_tree.ai_runner.subprocess.run', side_effect=fake), patch.object(Path,'mkdir'), patch.object(Path,'unlink'), patch.object(Path,'read_text', return_value='response'):
            self.assertEqual(call_codex(llm,'SYSTEM','USER','test-model','high'), 'response')
