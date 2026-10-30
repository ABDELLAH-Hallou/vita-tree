"""The bridge delegates prompt ownership to the backend; no provider calls."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from vita_tree.ai_runner import configure


class DocumentContextTests(unittest.TestCase):
    def test_backend_generation_and_contract_options_are_unchanged(self):
        generate=Mock(return_value='synthetic proposal')
        llm=SimpleNamespace(load_env=lambda:{}, generate=generate)
        with patch.dict('os.environ', {'VITA_TREE_REASONING':''}):
            configure(llm)
        self.assertIs(llm.generate, generate)
        result=llm.generate('captured sources', 'task and matching analysis', provider='codex', response_schema={'type':'object'})
        self.assertEqual(result,'synthetic proposal')
        generate.assert_called_once_with('captured sources', 'task and matching analysis',
            provider='codex', response_schema={'type':'object'})

    def test_configuration_accepts_minimal_backend_without_generate(self):
        llm=SimpleNamespace(load_env=lambda:{'fixture':'value'})
        with patch.dict('os.environ', {'VITA_TREE_REASONING':''}):
            configure(llm)
        self.assertEqual(llm.load_env()['fixture'], 'value')
        self.assertFalse(hasattr(llm,'generate'))
