import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from support import cleanup_repo
from vita_tree import ai_runner
from vita_tree.outcomes import read_outcome


class BackendAdapterTests(unittest.TestCase):
    def test_native_codex_schema_and_reasoning_contract_remain_supported(self):
        calls=[]
        def native(system,user,model='',*,response_schema=None,reasoning_effort=None):
            calls.append((response_schema,reasoning_effort))
            return 'synthetic'
        llm=types.SimpleNamespace(load_env=lambda:{},_call_codex_cli=native)
        with patch.dict(os.environ,{'VITA_TREE_REASONING':'high'}):
            ai_runner.configure(llm)
            self.assertEqual(llm._call_codex_cli('system','user','model',response_schema={'type':'object'}),'synthetic')
        self.assertEqual(calls,[({'type':'object'},'high')])

    def test_runner_uses_boolean_backend_api_and_native_trace_without_stdout_parsing(self):
        temporary=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        root=Path(temporary.name)
        helpers=types.ModuleType('vita.helpers')
        env=types.SimpleNamespace(load_env=lambda:{})
        llm=types.SimpleNamespace(load_env=lambda:{})
        helpers.env=env;helpers.llm=llm
        calls=[]
        def run(step,**kwargs):
            calls.append((step,kwargs))
            folder=Path('.vita/results');folder.mkdir(parents=True,exist_ok=True)
            if step=='extract':
                (folder/'extract.outcome.json').write_text(json.dumps({'schema_version':1,'step':step,
                    'run_id':'a'*32,'status':'success','attempts':[{'number':1,'category':'valid','mode':'validated_prompt'}]}))
            return step!='cover'
        commands=types.ModuleType('vita.commands.ai_step');commands.run=run
        modules={'vita':types.ModuleType('vita'),'vita.helpers':helpers,'vita.commands':types.ModuleType('vita.commands'),
                 'vita.commands.ai_step':commands}
        previous=Path.cwd()
        try:
            os.chdir(root)
            with patch.dict(sys.modules,modules),patch.dict(os.environ,{'VITA_TREE_EXECUTION_ID':'nonce','VITA_TREE_REASONING':''}):
                with patch.object(sys,'argv',['ai_runner.py','extract','--auto','--provider','openai']):
                    ai_runner.main()
                self.assertTrue(read_outcome(root,'extract','nonce')['verified'])
                with patch.object(sys,'argv',['ai_runner.py','cover','--auto','--provider','openai','--language','fr']):
                    with self.assertRaises(SystemExit) as error:ai_runner.main()
                self.assertEqual(error.exception.code,1)
                self.assertEqual(read_outcome(root,'cover','nonce')['status'],'failed')
            self.assertEqual(calls,[('extract',{'auto':True,'provider':'openai','language':None}),
                                    ('cover',{'auto':True,'provider':'openai','language':'fr'})])
        finally:
            os.chdir(previous)
            cleanup_repo(temporary)
