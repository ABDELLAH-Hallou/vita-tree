"""Generation stays separate from host factual capture; no provider calls."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from vita_tree.ai_runner import AUTO_DOCUMENT_CONTEXT, configure


class DocumentContextTests(unittest.TestCase):
    def test_document_generation_preserves_inputs_and_contract_options(self):
        for step in ('adapt', 'cover'):
            with self.subTest(step=step), patch.dict('os.environ', {'VITA_TREE_REASONING':''}):
                generate=Mock(return_value='synthetic proposal')
                llm=SimpleNamespace(load_env=lambda:{}, generate=generate)
                configure(llm, step)
                result=llm.generate('captured sources', 'task and matching analysis', provider='codex', response_schema={'type':'object'})
                self.assertEqual(result,'synthetic proposal')
                generate.assert_called_once_with(AUTO_DOCUMENT_CONTEXT+'\ncaptured sources',
                    'task and matching analysis', provider='codex', response_schema={'type':'object'})
                self.assertIn('requires factual approval', generate.call_args.args[0])

    def test_analysis_is_not_given_document_generation_instructions(self):
        generate=Mock()
        llm=SimpleNamespace(load_env=lambda:{}, generate=generate)
        with patch.dict('os.environ', {'VITA_TREE_REASONING':''}):
            configure(llm, 'analyze')
        self.assertIs(llm.generate, generate)
