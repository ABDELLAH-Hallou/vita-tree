import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from support import init_repo, cleanup_repo
from vita_tree.workspace import Workspace
from vita_tree.outcomes import safe_outcome, read_outcome
from vita_tree.provider_status import provider_error, failure, generation_result


def error(category='overloaded', model='fixture-model'):
    return {'schema_version':1,'code':'provider_error','category':category,'provider':'gemini','model':model,
            'step':'extract','status':503,'retryable':category in {'overloaded','rate_limit','timeout'},
            'attempts':3,'max_attempts':3,'exhausted':True,'retry_after_seconds':2,
            'action':'PRIVATE-PROMPT-CANARY','raw':'PRIVATE-KEY-CANARY'}


def outcome(category='overloaded'):
    return {'schema_version':1,'status':'failed','error':error(category),
            'attempts':[{'number':i,'category':category} for i in range(1,4)]}


class ContractTests(unittest.TestCase):
    def test_typed_contract_preserves_category_route_budget_and_not_prose(self):
        for category in ('overloaded','authentication','invalid_model','rate_limit','quota_exceeded','invalid_json','validation_error'):
            native=safe_outcome(outcome(category))
            info=failure({'status':'failed','backend':native})
            self.assertEqual(info['category'],category)
            self.assertEqual(info['provider'],'gemini');self.assertEqual(info['model'],'fixture-model')
            self.assertEqual(info['attempts'],3);self.assertEqual(info['httpStatus'],503)
            self.assertNotIn('PRIVATE',json.dumps(native));self.assertNotIn('PRIVATE',json.dumps(info))
        self.assertIn('Wait',failure({'status':'failed','backend':safe_outcome(outcome())})['action'])
        self.assertIn('Reconnect',failure({'status':'failed','backend':safe_outcome(outcome('authentication'))})['action'])

    def test_secrets_unknown_contract_and_malformed_metadata(self):
        self.assertIsNone(provider_error({**error(),'schema_version':2}))
        self.assertIsNone(provider_error({**error(),'schema_version':True}))
        self.assertIsNone(provider_error({**error(),'category':[]}))
        self.assertIsNone(provider_error({**error(),'retryable':1}))
        sanitized=provider_error({**error(),'model':'hidden-session-credential','provider':[]},['hidden-session-credential'])
        self.assertIsNone(sanitized['model']);self.assertIsNone(sanitized['provider'])
        native=safe_outcome({**outcome(),'error':error(model='hidden-session-credential')},['hidden-session-credential'])
        self.assertNotIn('hidden-session-credential',json.dumps(native))
        self.assertIsNone(failure({'status':'success','backend':native}))
        unknown=failure({'status':'failed','backend':None})
        self.assertIsNone(unknown['retryable']);self.assertIsNone(unknown['attempts'])
        self.assertIn('No credential problem',unknown['action'])

    def test_parent_read_and_history_reload_revalidate_typed_error(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd(),prefix='.vita-tree-test-') as folder:
            root=Path(folder); dest=root/'.vita/results';dest.mkdir(parents=True)
            value={'schemaVersion':1,'adapter':'vita-python-api-v1','step':'extract','executionId':'execution',
                   'status':'failed','verified':False,'backend':safe_outcome(outcome())}
            (dest/'tree-extract.outcome.json').write_text(json.dumps(value),encoding='utf-8')
            read=read_outcome(root,'extract','execution')
            restored=Workspace._safe_outcomes({'extract':read})['extract']
            self.assertEqual(restored['backend']['providerError']['attempts'],3)
            self.assertEqual(failure(restored)['category'],'overloaded')

    def test_discovery_cannot_claim_generation_and_unknown_response_fails(self):
        base={'schema_version':1,'check':'generation','status':'success','generation_verified':True,'may_consume_usage':True,
              'provider':'gemini','model':'fixture','attempts':1}
        self.assertTrue(generation_result(base)['generationVerified'])
        for changed in ({'check':'discovery'},{'schema_version':2},{'may_consume_usage':False}):
            with self.assertRaises(ValueError):generation_result({**base,**changed})


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path.cwd(),prefix='.vita-tree-test-')
        self.root=init_repo(Path(self.temp.name));self.workspace=Workspace(self.root)
        self.command=[sys.executable,str(Path(__file__).with_name('fake_generation_check.py').resolve())]
        self.patcher=patch.object(self.workspace,'vita_command',return_value=self.command);self.patcher.start()
        self.connection=self.workspace.add_connection('Fixture account','gemini','plain-secret-canary')['id']
    def tearDown(self):
        self.patcher.stop();cleanup_repo(self.temp)
    def setup(self, model='fixture'):
        return {'default':{'provider':'gemini','model':model,'reasoning':'','connection':self.connection},'steps':{}}
    def check(self, model='fixture', **kwargs):
        return self.workspace.check_generation('master','extract',self.setup(model),**kwargs)

    def test_explicit_confirmation_and_missing_session_do_not_invoke(self):
        with patch('vita_tree.generation_check.invoke') as invoke:
            with self.assertRaisesRegex(ValueError,'Confirm'):self.check()
            self.workspace.remove_connection(self.connection)
            with self.assertRaisesRegex(ValueError,'connection'):self.check(confirmed=True)
            invoke.assert_not_called()

    def test_real_child_inherited_and_overridden_routes_no_application_changes(self):
        before=self.workspace.snapshot('master');settings=self.setup()
        shared=self.workspace.check_generation('master','extract',settings,True)
        self.assertTrue(shared['generationVerified']);self.assertEqual(shared['origin'],'shared')
        settings['steps']['extract']={**settings['default'],'model':'overloaded'}
        custom=self.workspace.check_generation('master','extract',settings,True)
        self.assertEqual(custom['origin'],'step_override');self.assertFalse(custom['generationVerified'])
        self.assertEqual(custom['failure']['category'],'overloaded');self.assertEqual(custom['attempts'],3)
        self.assertEqual(custom['provider'],'gemini');self.assertEqual(custom['model'],'overloaded')
        self.assertEqual(self.workspace.snapshot('master')['content'],before['content'])
        self.assertFalse(self.workspace.jobs)
        self.assertFalse(list(self.workspace.root.glob('generation-check-*')))
        self.assertFalse(list((self.workspace.root/'ai-settings').glob('*')))

    def test_codex_check_uses_its_own_git_root_and_cleans_up(self):
        from vita_tree import generation_check
        (self.root/'AGENTS.md').write_text('private-project-instructions',encoding='utf-8')
        invoke=generation_check.invoke
        locations=[]
        def observed(args, **kwargs):
            stage=Path(kwargs['cwd']);locations.append(stage)
            self.assertFalse(stage.resolve().is_relative_to(self.root.resolve()))
            self.assertTrue((stage/'.git').is_dir())
            return invoke(args,**kwargs)
        with patch.object(generation_check,'invoke',side_effect=observed):
            result=self.workspace.check_generation('master','analyze',{'default':{'provider':'codex','model':'fixture-codex'}},True)
        self.assertTrue(result['generationVerified'])
        self.assertTrue(locations);self.assertTrue(all(not path.exists() for path in locations))
        self.assertNotIn('private-project-instructions',json.dumps(result))

    @unittest.skipUnless(os.name == 'nt', 'Windows 8.3 temporary-directory aliases')
    def test_generation_checks_accept_windows_short_temp_paths(self):
        import ctypes
        from vita_tree import generation_check

        with tempfile.TemporaryDirectory(prefix='vita-tree-long-temporary-folder-') as folder:
            get_short_path = ctypes.WinDLL('kernel32', use_last_error=True).GetShortPathNameW
            get_short_path.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint)
            get_short_path.restype = ctypes.c_uint
            buffer = ctypes.create_unicode_buffer(32768)
            if not get_short_path(folder, buffer, len(buffer)):
                raise ctypes.WinError(ctypes.get_last_error())
            alias = Path(buffer.value)
            if alias == alias.resolve():
                self.skipTest('8.3 aliases are disabled on the temporary volume')
            self.assertTrue(alias.samefile(folder))
            invoke = generation_check.invoke
            locations = []

            def observed(args, **kwargs):
                locations.append(Path(kwargs['cwd']))
                return invoke(args, **kwargs)

            with patch.object(tempfile, 'tempdir', str(alias)), patch.object(generation_check, 'invoke', side_effect=observed):
                api = self.check(confirmed=True)
                codex = self.workspace.check_generation('master', 'analyze', {
                    'default': {'provider': 'codex', 'model': 'fixture-codex'}}, True)
            self.assertTrue(api['generationVerified'])
            self.assertTrue(codex['generationVerified'])
            self.assertEqual(len(locations), 2)
            self.assertTrue(all(path != path.resolve() for path in locations))
            self.assertTrue(all(not path.exists() for path in locations))
            self.assertFalse(self.workspace._generation_checks)

    def test_permanent_failures_secret_redaction_and_future_contract(self):
        for category in ('authentication','invalid_model','rate_limit','invalid_json'):
            result=self.check(category,confirmed=True)
            self.assertEqual(result['failure']['category'],category)
            self.assertEqual(result['failure']['retryable'],category=='rate_limit')
            self.assertNotIn('PRIVATE',json.dumps(result));self.assertNotIn('plain-secret-canary',json.dumps(result))
        secret=self.check('secret',confirmed=True)
        self.assertIsNone(secret['model']);self.assertNotIn('plain-secret-canary',json.dumps(secret))
        for model in ('future','wrong-route','unreported'):
            with self.assertRaises(ValueError):self.check(model,confirmed=True)
        redacted=self.check('fixture@revision',confirmed=True)
        self.assertTrue(redacted['generationVerified']);self.assertIsNone(redacted['model'])
        self.assertFalse(self.workspace._generation_checks)

    def test_timeout_unknown_attempts_and_duplicate_guard(self):
        with patch('vita_tree.generation_check.invoke',side_effect=subprocess.TimeoutExpired('ignored',180,stderr='PRIVATE')):
            result=self.check(confirmed=True)
        self.assertFalse(result['generationVerified']);self.assertIsNone(result['attempts'])
        self.assertNotIn('PRIVATE',json.dumps(result))
        self.workspace._generation_checks={('master','extract')}
        with self.assertRaisesRegex(ValueError,'already running'):self.check(confirmed=True)
        self.workspace._generation_checks.clear()

    def test_duplicate_guard_does_not_lock_other_steps_or_navigation(self):
        from vita_tree import generation_check
        entered=threading.Event();release=threading.Event();results=[];errors=[]
        invoke=generation_check.invoke
        def held(args, **kwargs):
            if args[args.index('--model')+1]=='slow':
                entered.set()
                if not release.wait(10):raise AssertionError('Check held the workspace lock')
            return invoke(args,**kwargs)
        def worker():
            try:results.append(self.check('slow',confirmed=True))
            except Exception as exc:errors.append(exc)
        with patch.object(generation_check,'invoke',side_effect=held):
            thread=threading.Thread(target=worker);thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaisesRegex(ValueError,'already running'):self.check(confirmed=True)
                self.assertEqual(self.workspace.snapshot('master')['branch'],'master')
                other=self.workspace.check_generation('master','review',self.setup(),True)
                self.assertTrue(other['generationVerified'])
            finally:release.set();thread.join(timeout=15)
        self.assertFalse(thread.is_alive());self.assertFalse(errors,errors)
        self.assertTrue(results[0]['generationVerified']);self.assertFalse(self.workspace._generation_checks)

    def test_retry_lineage_configuration_change_is_visible(self):
        parent={'id':'a'*32,'status':'failed','stepConfig':{'extract':self.setup()['default']},'attempt':1}
        self.workspace.jobs[parent['id']]=parent
        child={**parent,'id':'b'*32,'parentRunId':parent['id'],'attempt':2}
        self.assertFalse(self.workspace._public_job(child)['configurationChanged'])
        child['stepConfig']={'extract':{**parent['stepConfig']['extract'],'model':'changed'}}
        self.assertTrue(self.workspace._public_job(child)['configurationChanged'])


if __name__=='__main__':unittest.main()
