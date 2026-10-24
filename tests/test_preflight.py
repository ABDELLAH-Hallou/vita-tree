"""Captured project checks with synthetic files and controlled local tools."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_jobs as job_support
from support import SOURCE,git
from vita_tree import preflight
from vita_tree.pdf import CompilationError
from vita_tree.workspace import Workspace,ConflictError,digest


class SetupTests(unittest.TestCase):
    setUp=job_support.JobTests.setUp
    tearDown=job_support.JobTests.tearDown
    branch=job_support.JobTests.branch
    start=job_support.JobTests.start
    wait=job_support.JobTests.wait
    finished=job_support.JobTests.finished
    release=job_support.JobTests.release
    pipeline_source=job_support.JobTests.pipeline_source
    pipeline_branch=job_support.JobTests.pipeline_branch

    def check(self,branch,**options):
        return self.workspace.check_setup(branch['branch'],branch['revision'],branch['jobRevision'],**options)

    def codes(self,result):return [c['code'] for c in result['checks']]

    def test_valid_project_uses_a_disposable_copy_and_preserves_every_project_file(self):
        branch=self.branch('project');location=Path(branch['worktree'])
        (location/'local.cls').write_text('synthetic class')
        original=git(location,'status','--porcelain')
        def tool(folder,entry,**options):
            self.assertNotEqual(folder,location)
            self.assertTrue((folder/'local.cls').exists())
            self.assertFalse((folder/'.vita/.env').exists())
            built=self.fake_compile(folder,entry,**options)
            (folder/'main.tex').write_text('synthetic tool side effect')
            return built
        self.cover_builder.side_effect=tool
        result=self.check(branch)
        self.assertTrue(result['ready']);self.assertIn('compiled',self.codes(result))
        self.assertEqual(result['revision'],branch['revision'])
        self.assertEqual((location/'main.tex').read_text(),SOURCE)
        self.assertEqual(git(location,'status','--porcelain'),original)
        self.assertFalse(self.workspace.jobs)
        self.assertFalse(list((self.workspace.root/'preflight').iterdir()))

    def test_missing_entry_is_guided_without_rewriting_the_project(self):
        (self.root/'main.tex').unlink()
        result=self.workspace.check_setup('master')
        self.assertFalse(result['ready']);self.assertIn('entry_missing',self.codes(result))
        self.cover_builder.assert_not_called();self.assertFalse((self.root/'main.tex').exists())
        self.assertFalse(self.workspace.jobs)

    def test_input_encoding_error_preserves_bytes(self):
        raw=b'\xffSYNTHETIC-NON-UTF8';(self.root/'main.tex').write_bytes(raw)
        result=self.workspace.check_setup('master')
        self.assertFalse(result['ready']);self.assertIn('input_encoding',self.codes(result))
        self.assertEqual((self.root/'main.tex').read_bytes(),raw);self.cover_builder.assert_not_called()

    def test_old_project_preview_cannot_satisfy_a_new_compilation(self):
        branch=self.branch('stale-preview');location=Path(branch['worktree'])
        old=location/'__vt_output/main.pdf';old.parent.mkdir();old.write_bytes(b'%PDF-1.7\nstale synthetic preview')
        git(location,'add','--force','__vt_output/main.pdf')
        def no_output(folder,entry,engine='auto',output=None):
            self.assertIsNotNone(output);self.assertFalse(output.is_relative_to(folder))
            self.assertFalse((output/'main.pdf').exists())
            raise ValueError('The tool produced no document')
        self.cover_builder.side_effect=no_output
        result=self.check(branch)
        self.assertFalse(result['ready']);self.assertIn('compile_failed',self.codes(result))
        self.assertEqual(old.read_bytes(),b'%PDF-1.7\nstale synthetic preview')

    def test_other_entry_can_be_checked_for_direct_pdf_without_advertising_ai_support(self):
        (self.root/'other.tex').write_text(SOURCE,encoding='utf-8');self.workspace.document_path='other.tex'
        result=self.workspace.check_setup('master')
        self.assertFalse(result['ready']);self.assertIn('entry_contract',self.codes(result));self.assertIn('compiled',self.codes(result))
        self.assertTrue(self.cover_builder.called)

    def test_configuration_errors_and_entry_contract_are_actionable_before_compilation(self):
        branch=self.branch('settings');config=Path(branch['worktree'])/'.vita';config.mkdir(exist_ok=True)
        for name,raw,code in [('config.json','{','configuration_invalid'),('config.json','[]','configuration_invalid'),
                              ('config.json','{"tex_entry":"other.tex"}','entry_contract'),
                              ('config.json','{"tex_entry":false}','configuration_invalid'),
                              ('extensions.json','{"llm_providers":[]}','configuration_invalid')]:
            path=config/name;path.write_text(raw)
            with self.subTest(raw=raw):
                result=self.check(branch);self.assertFalse(result['ready']);self.assertIn(code,self.codes(result))
                self.assertEqual(path.read_text(),raw)
            path.unlink()
        self.cover_builder.assert_not_called()

    def test_missing_engine_package_font_and_timeout_have_distinct_safe_actions(self):
        branch=self.branch('dependencies')
        cases=[(CompilationError('engine_missing','private engine path'),'engine_missing',None),
               (ValueError("! LaTeX Error: File `synthetic-missing.sty' not found."),'missing_package','synthetic-missing.sty'),
               (ValueError("! LaTeX Error: File `private/folder/local.cls' not found."),'missing_package','local.cls'),
               (ValueError("! LaTeX Error: File `image.png' not found."),'missing_file','image.png'),
               (ValueError('Package fontspec Error: The font "SyntheticFont" cannot be found.'),'missing_font',None),
               (ValueError('The fontspec package requires either XeTeX or LuaTeX.'),'engine_mismatch',None),
               (CompilationError('compile_timeout','private log'),'compile_timeout',None),
               (ValueError('private raw compiler output'),'compile_failed',None)]
        for error,code,target in cases:
            with self.subTest(code=code):
                self.cover_builder.side_effect=error;result=self.check(branch)
                self.assertFalse(result['ready']);check=next(c for c in result['checks'] if c['code']==code)
                self.assertEqual(check.get('target'),target)
                self.assertNotIn('private',json.dumps(result));self.assertNotIn(str(Path(branch['worktree'])),json.dumps(result))

    def test_structure_failure_does_not_override_a_successful_compiler(self):
        branch=self.branch('structure')
        with patch('vita_tree.latex.parse_document',return_value={'warnings':[],'error':'Synthetic unsupported structure'}):
            result=self.check(branch)
        self.assertTrue(result['ready']);self.assertIn('structure_limited',self.codes(result));self.assertIn('compiled',self.codes(result))
        self.assertEqual(self.workspace.read('structure','main.tex'),SOURCE)

    def test_invalid_raw_provider_settings_are_not_hidden_by_the_selected_route(self):
        branch=self.branch('raw-settings');path=Path(branch['worktree'])/'.vita/extensions.json';path.parent.mkdir(exist_ok=True)
        raw='{"llm_providers":{"codex":null}}';path.write_text(raw,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'extensions.json'):
            self.start(branch,provider='codex')
        self.assertEqual(path.read_text(encoding='utf-8'),raw);self.assertFalse(self.workspace.jobs)

    def test_changed_draft_or_include_or_configuration_invalidates_the_result(self):
        branch=self.branch('changing');location=Path(branch['worktree'])
        (location/'included.tex').write_text('before')
        for relative,after in [('main.tex',SOURCE+'\n% external'),('included.tex','after'),('.vita/config.json','{"author":"Synthetic"}')]:
            path=location/relative;before=path.read_text() if path.exists() else None
            def tool(folder,entry,**options):
                result=self.fake_compile(folder,entry,**options);path.parent.mkdir(exist_ok=True);path.write_text(after);return result
            self.cover_builder.side_effect=tool
            with self.subTest(relative=relative),self.assertRaisesRegex(ConflictError,'changed during setup'):
                self.check(branch)
            self.assertEqual(path.read_text(),after)
            if before is None:path.unlink()
            else:path.write_text(before)
        with self.assertRaisesRegex(ConflictError,'saved draft changed'):
            self.check({**branch,'revision':'a'*64})
        self.assertFalse(self.workspace._setup_checks);self.assertFalse(self.workspace._previewing)

    def test_snapshot_mismatch_stops_before_the_compiler(self):
        branch=self.branch('capture');location=Path(branch['worktree']);asset=location/'included.tex';asset.write_text('captured')
        from vita_tree.pdf import export_snapshot
        def race(*args,**options):
            asset.write_text('concurrent edit');return export_snapshot(*args,**options)
        with patch('vita_tree.pdf.export_snapshot',side_effect=race),self.assertRaisesRegex(ConflictError,'snapshot was captured'):
            self.check(branch)
        self.cover_builder.assert_not_called();self.assertEqual(asset.read_text(),'concurrent edit')

    def test_failed_preflight_calls_no_ai_and_survives_restart(self):
        branch=self.branch('blocked')
        self.cover_builder.side_effect=ValueError("File `synthetic-package.sty' not found. private raw log")
        run=self.start(branch);result=self.finished(run['id'])
        self.assertEqual(result['status'],'failed');self.assertFalse(result['preflight']['ready'])
        self.assertFalse((self.control/'blocked.started').exists());self.assertEqual(result['checkpointSteps'],[])
        self.assertNotIn('private raw log',json.dumps(result));self.assertEqual(self.workspace.read('blocked','main.tex'),SOURCE)
        reopened=Workspace(self.root)
        try:self.assertIn('missing_package',self.codes(reopened.get_job(run['id'])['preflight']))
        finally:reopened.close()

    def test_concurrent_edit_during_automatic_check_stops_before_ai(self):
        branch=self.branch('auto-conflict');location=Path(branch['worktree'])
        def tool(folder,entry,**options):
            built=self.fake_compile(folder,entry,**options);(location/'main.tex').write_text(SOURCE+'\n% changed during preflight');return built
        self.cover_builder.side_effect=tool
        result=self.finished(self.start(branch)['id'])
        self.assertEqual(result['status'],'failed');self.assertIn('draft changed during setup',result['message'])
        self.assertFalse(result['preflight']['ready'])
        self.assertFalse((self.control/'auto-conflict.started').exists())
        self.assertIn('changed during preflight',self.workspace.read('auto-conflict','main.tex'))

    def test_engine_selection_is_captured_and_retry_preserves_it(self):
        self.pipeline_source();branch=self.pipeline_branch('engine-retry');self.release('engine-retry')
        flag=self.control/'engine-retry.cover.fail';flag.touch()
        parent=self.finished(self.start(branch,workflow={'steps':['analyze','adapt','cover']},engine='xelatex')['id'])
        self.assertEqual(parent['compileEngine'],'xelatex');self.assertEqual(parent['preflight']['engine'],'xelatex')
        flag.unlink();current=self.workspace.snapshot('engine-retry')
        plan=self.workspace.resume_ai(parent['id'],current['revision'],current['jobRevision'],preview=True)
        run=self.workspace.resume_ai(parent['id'],current['revision'],current['jobRevision'],token=plan['token'])
        child=self.finished(run['id']);self.assertEqual(child['status'],'succeeded',child)
        self.assertEqual(child['compileEngine'],'xelatex')
        self.assertTrue(all(call.kwargs.get('engine',call.args[2] if len(call.args)>2 else None)=='xelatex' for call in self.cover_builder.call_args_list))

    def test_public_history_rejects_unrecognized_fields_and_redacts_known_targets(self):
        secret='synthetic-secret.sty'
        report=preflight.public_result({'engine':'pdflatex','checks':[{'code':'missing_package','target':secret,'message':'unsafe source'}],'source':'private source'},[secret])
        self.assertNotIn(secret,json.dumps(report));self.assertNotIn('unsafe source',json.dumps(report));self.assertNotIn('private source',json.dumps(report))
        self.assertIsNone(preflight.public_result({'checks':{'arbitrary':'value'}}))


if __name__=='__main__':unittest.main()
