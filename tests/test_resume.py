import json
from pathlib import Path
import unittest
from unittest.mock import patch

from support import SOURCE
import test_jobs as job_support
from vita_tree.workspace import Workspace, ConflictError, digest
from vita_tree import checkpoints
from vita_tree.publication import publish, put


class ResumeTests(unittest.TestCase):
    setUp = job_support.JobTests.setUp
    tearDown = job_support.JobTests.tearDown
    branch = job_support.JobTests.branch
    start = job_support.JobTests.start
    release = job_support.JobTests.release
    wait = job_support.JobTests.wait
    finished = job_support.JobTests.finished
    pipeline_source = job_support.JobTests.pipeline_source
    pipeline_branch = job_support.JobTests.pipeline_branch

    def prepare(self, label='recovery', fail='cover', steps=None, **options):
        self.pipeline_source()
        branch = self.pipeline_branch(label, **options)
        self.release(label)
        flag = self.control / (label + '.' + fail + '.fail')
        flag.touch()
        record = self.start(branch, workflow={'steps': steps or ['extract','analyze','adapt','cover']})
        result = self.finished(record['id'])
        self.assertEqual(result['status'], 'failed', result)
        self.assertEqual(self.workspace.read(label, 'main.tex'), SOURCE)
        return branch, result, flag

    def preview(self, parent, **options):
        branch = self.workspace.snapshot(parent['branch'])
        return self.workspace.resume_ai(parent['id'], branch['revision'], branch['jobRevision'], preview=True, **options)

    def retry(self, parent, plan=None, **options):
        plan = plan or self.preview(parent, **options)
        branch = self.workspace.snapshot(parent['branch'])
        record = self.workspace.resume_ai(parent['id'], branch['revision'], branch['jobRevision'], token=plan['token'], **options)
        return self.finished(record['id'])

    def calls(self, label, step):
        path = self.control / (label + '.' + step + '.calls')
        return path.read_text().splitlines() if path.exists() else []

    def test_failure_after_extract_reuses_only_verified_prefix(self):
        branch, parent, flag = self.prepare(fail='analyze')
        self.assertEqual(parent['checkpointSteps'], ['extract'])
        plan = self.preview(parent)
        self.assertEqual(plan['reuse'], ['extract'])
        self.assertEqual(plan['rerun'], ['analyze','adapt','cover'])
        flag.unlink()
        child = self.retry(parent, plan)
        self.assertEqual(child['status'], 'succeeded', child)
        self.assertEqual(len(self.calls('recovery','extract')), 1)
        self.assertEqual(len(self.calls('recovery','analyze')), 2)
        self.assertEqual(child['parentRunId'], parent['id'])
        self.assertEqual(child['rootRunId'], parent['id'])
        self.assertEqual(child['attempt'], 2)
        self.assertEqual(child['stages'][0]['reusedFrom'], parent['id'])
        self.assertEqual(len(self.workspace.job_result(child['id'])['attemptHistory']), 2)
        self.assertNotIn('private-fixture-value', json.dumps(self.workspace.list_jobs()))

    def test_cover_retry_uses_matching_isolated_adaptation(self):
        branch, parent, flag = self.prepare()
        adapted = self.workspace.job_result(parent['id'])['files']['main.tex']
        self.assertNotEqual(adapted, SOURCE)
        plan = self.preview(parent)
        self.assertEqual(plan['reuse'], ['extract','analyze','adapt'])
        self.assertEqual(plan['rerun'], ['cover'])
        flag.unlink()
        child = self.retry(parent, plan)
        self.assertEqual(child['status'], 'succeeded', child)
        self.assertEqual(len(self.calls('recovery','adapt')), 1)
        self.assertEqual(self.calls('recovery','cover'), [digest(adapted)] * 2)
        self.assertEqual(self.workspace.read('recovery','main.tex'), adapted)
        self.assertIsNotNone(self.workspace.cover_pdf_result(child['id']))
        inspection=self.workspace.inspector.public_detail(child['id'])
        self.assertFalse(inspection['tree']['configurationChanged'])
        self.assertEqual(inspection['tree']['stepInputs']['cover']['source_sha256'],digest(adapted))
        self.assertEqual(child['traceId'],parent['traceId'])

    def test_repeated_retry_failure_preserves_draft_and_ancestors(self):
        branch, first, flag = self.prepare()
        second = self.retry(first)
        third = self.retry(second)
        self.assertEqual([second['status'], third['status']], ['failed','failed'])
        self.assertEqual(third['attempt'], 3)
        self.assertEqual(third['parentRunId'], second['id'])
        self.assertEqual(third['rootRunId'], first['id'])
        self.assertEqual(self.workspace.read('recovery','main.tex'), SOURCE)
        self.assertEqual(len(self.calls('recovery','adapt')), 1)
        for parent in (first, second, third):
            self.assertIsNotNone(checkpoints.load_checkpoint(self.workspace.root/'checkpoints', parent['id'], 'adapt'))
            self.assertIn('recovery systems', self.workspace.job_result(parent['id'])['files']['main.tex'])
        flag.unlink()
        final = self.retry(third)
        self.assertEqual(final['status'], 'succeeded', final)

    def test_changed_step_route_invalidates_only_affected_suffix(self):
        branch, parent, flag = self.prepare()
        cover = {'default': {'provider':'openai'}, 'steps': {'cover': {'model':'different-writer'}}}
        plan = self.preview(parent, ai_config=cover)
        self.assertEqual(plan['reuse'], ['extract','analyze','adapt'])
        self.assertEqual(plan['rerun'], ['cover'])
        analyze = {'default': {'provider':'openai'}, 'steps': {'analyze': {'model':'analysis-v2'}}}
        self.assertEqual(self.preview(parent, ai_config=analyze)['reuse'], ['extract'])
        shared = {'default': {'provider':'openai','model':'new-model'}}
        self.assertEqual(self.preview(parent, ai_config=shared)['reuse'], [])
        self.assertEqual(self.preview(parent, language='fr')['reuse'], ['extract','analyze'])

    def test_input_config_skill_criteria_and_dependency_changes_invalidate(self):
        branch, parent, flag = self.prepare()
        location = Path(branch['worktree'])
        changes = [
            (location/'main.tex', SOURCE+'\n% edited draft'),
            (location/'job.md', branch['job']+' '),
            (location/'.vita/config.json', '{"author":"Candidate"}'),
            (location/'.vita/skills/adapt/style.md', 'New writing instructions'),
            (location/'included.tex', 'New included source'),
        ]
        for path, changed in changes:
            with self.subTest(path=path.name):
                old = path.read_text() if path.exists() else None
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(changed)
                self.assertEqual(self.preview(parent)['reuse'], ['extract','analyze'] if path.name == 'style.md' else [])
                if old is None: path.unlink()
                else: path.write_text(old)
        store = self.workspace.root.parent/'vita/requirements'
        revision = 'a'*64
        approval = store/'approved'/(digest(branch['job'])+'.json')
        approval.parent.mkdir(parents=True)
        approval.write_text(json.dumps({'revision':revision}))
        target = store/'revisions'/(revision+'.json');target.parent.mkdir();target.write_text('{"criteria":"changed"}')
        self.assertEqual(self.preview(parent)['reuse'], [])
        approval.unlink();target.unlink()
        # Corrupt retained dependencies are detected, never copied into a retry.
        retained = self.workspace.root/'checkpoints'/parent['id']/'analyze/files/.vita/results/analysis.json'
        retained.write_text('{"changed":true}')
        self.assertEqual(self.preview(parent)['reuse'], ['extract'])

    def test_reviewed_plan_cannot_be_submitted_after_inputs_change(self):
        branch, parent, flag = self.prepare()
        plan = self.preview(parent)
        self.workspace.save('recovery','main.tex',branch['revision'],SOURCE+'\n% user draft')
        current = self.workspace.snapshot('recovery')
        with self.assertRaisesRegex(ConflictError, 'plan changed'):
            self.workspace.resume_ai(parent['id'], current['revision'], current['jobRevision'], token=plan['token'])
        self.assertEqual(self.workspace.read('recovery','main.tex'), SOURCE+'\n% user draft')

    def test_concurrent_edit_during_retry_stops_publication(self):
        branch, parent, flag = self.prepare(hold='cover')
        # The failure flag runs before the hold. Let the retry hold at Cover.
        flag.unlink()
        plan = self.preview(parent)
        child = self.workspace.resume_ai(parent['id'],branch['revision'],branch['jobRevision'],token=plan['token'])
        self.wait(lambda: (self.control/'recovery.cover.started').exists())
        changed = SOURCE+'\n% concurrent user edit'
        (Path(branch['worktree'])/'main.tex').write_text(changed)
        (self.control/'recovery.cover.release').touch()
        result = self.finished(child['id'])
        self.assertEqual(result['status'], 'failed', result)
        self.assertEqual(self.workspace.read('recovery','main.tex'), changed)
        self.assertIn('recovery systems',self.workspace.job_result(child['id'])['files']['main.tex'])

    def test_restart_restores_checkpoints_and_attempt_lineage(self):
        branch, parent, flag = self.prepare()
        self.workspace.close()
        source = self.workspace.vita_source
        command = self.workspace.vita_command()
        self.workspace = Workspace(self.root, vita_source=source)
        with patch.object(self.workspace,'vita_command',return_value=command):
            restored = self.workspace.get_job(parent['id'])
            self.assertTrue(restored['resumeAvailable'])
            self.assertEqual(self.preview(restored)['reuse'], ['extract','analyze','adapt'])
            flag.unlink()
            child = self.retry(restored)
        self.assertEqual(child['status'], 'succeeded', child)
        self.assertEqual(child['attempt'], 2)

    def test_reconnected_session_matches_credentials_not_ephemeral_connection_id(self):
        self.pipeline_source()
        branch=self.pipeline_branch('session-retry')
        self.release('session-retry')
        flag=self.control/'session-retry.cover.fail';flag.touch()
        first=self.workspace.add_connection('Original session','openai','same-private-test-credential')
        config={'default':{'provider':'openai','connection':first['id']}}
        parent=self.finished(self.start(branch,ai_config=config,workflow={'steps':['extract','analyze','adapt','cover']})['id'])
        self.assertEqual(parent['status'],'failed',parent)
        command=self.workspace.vita_command();source=self.workspace.vita_source
        self.workspace.close();self.workspace=Workspace(self.root,vita_source=source)
        matching=self.workspace.add_connection('Reconnected session','openai','same-private-test-credential')
        changed=self.workspace.add_connection('Different account','openai','different-private-test-credential')
        with patch.object(self.workspace,'vita_command',return_value=command):
            same={'default':{'provider':'openai','connection':matching['id']}}
            other={'default':{'provider':'openai','connection':changed['id']}}
            self.assertEqual(self.preview(parent,ai_config=same)['reuse'],['extract','analyze','adapt'])
            self.assertEqual(self.preview(parent,ai_config=other)['reuse'],[])
            flag.unlink();child=self.retry(parent,ai_config=same)
        self.assertEqual(child['status'],'succeeded',child)
        public=json.dumps(self.workspace.list_jobs())
        self.assertNotIn('same-private-test-credential',public)
        self.assertNotIn('different-private-test-credential',public)

    def test_restart_after_extract_marks_interrupted_and_resumes_verified_prefix(self):
        self.pipeline_source()
        branch = self.pipeline_branch('stopped',hold='analyze')
        self.release('stopped')
        parent = self.start(branch,workflow={'steps':['extract','analyze','adapt','cover']})
        self.wait(lambda:(self.control/'stopped.analyze.started').exists())
        self.assertIsNotNone(checkpoints.load_checkpoint(self.workspace.root/'checkpoints',parent['id'],'extract'))
        command = self.workspace.vita_command()
        source = self.workspace.vita_source
        self.workspace.close()
        (self.control/'stopped.analyze.release').touch()
        for thread in list(self.workspace._ai_threads):thread.join(timeout=15)
        self.workspace = Workspace(self.root,vita_source=source)
        with patch.object(self.workspace,'vita_command',return_value=command):
            restored = self.workspace.get_job(parent['id'])
            self.assertEqual(restored['status'],'interrupted')
            self.assertEqual(self.preview(restored)['reuse'],['extract'])
            child = self.retry(restored)
        self.assertEqual(child['status'],'succeeded',child)
        self.assertEqual(len(self.calls('stopped','extract')),1)

    def test_successful_cover_checkpoint_retains_pdf_after_publication_failure(self):
        branch, parent, flag = self.prepare()
        flag.unlink()
        # Force a failure after all backend steps and PDF validation complete.
        with patch('vita_tree.publication.put',side_effect=OSError('Synthetic write failure')):
            child = self.retry(parent)
        self.assertEqual(child['status'],'failed',child)
        self.assertEqual(self.workspace.read('recovery','main.tex'),SOURCE)
        self.assertIn('cover',child['checkpointSteps'])
        final = self.retry(child)
        self.assertEqual(final['status'],'succeeded',final)
        self.assertIsNotNone(self.workspace.cover_pdf_result(final['id']))
        self.assertEqual(len(self.calls('recovery','cover')),2)

    def test_unverified_cli_and_expired_checkpoints_retry_from_start(self):
        branch, parent, flag = self.prepare(legacy_cli=True)
        self.assertEqual(parent['checkpointSteps'], [])
        self.assertEqual(self.preview(parent)['reuse'], [])
        # Repeated failures never bless old outputs merely because files exist.
        child = self.retry(parent)
        self.assertEqual(child['checkpointSteps'], [])
        self.assertEqual(len(self.calls('recovery','adapt')), 2)

    def test_checkpoint_cleanup_is_bounded_and_preserves_application_and_history(self):
        branch, parent, flag = self.prepare()
        result = checkpoints.cleanup(self.workspace.root/'checkpoints',self.workspace.jobs,
                                     now=parent['finishedAt']+checkpoints.RETENTION_SECONDS+1)
        self.assertIn(parent['id'], result['removed'])
        self.assertEqual(self.preview(parent)['reuse'], [])
        self.assertEqual(self.workspace.read('recovery','main.tex'),SOURCE)
        self.assertIn('main.tex', self.workspace.job_result(parent['id'])['files'])
        self.assertTrue((self.workspace.root/'job-history'/(parent['id']+'.json')).exists())

    def test_publication_write_failure_rolls_back_all_files_and_metadata(self):
        branch = self.pipeline_branch('atomic')
        location = Path(branch['worktree'])
        before_meta = self.workspace.metadata_path('atomic').read_text()
        calls = []
        def fail_once(path, value):
            calls.append(path)
            if len(calls) == 2: raise OSError('Synthetic disk failure')
            put(path,value)
        with patch('vita_tree.publication.put',side_effect=fail_once):
            with self.assertRaises(OSError):
                with publish(self.workspace,'b'*32,'atomic',{'@metadata':'{}','main.tex':SOURCE+'new'}):
                    self.fail('Publication should fail')
        self.assertEqual((location/'main.tex').read_text(),SOURCE)
        self.assertEqual(self.workspace.metadata_path('atomic').read_text(),before_meta)

    def test_pending_rollback_blocks_worktree_release_and_edits_until_restart(self):
        branch = self.pipeline_branch('pending-recovery')
        before_meta = self.workspace.metadata_path(branch['branch']).read_text()
        calls=[]
        def deny_rollback(path,value):
            calls.append(path)
            if len(calls)>1:raise PermissionError('Synthetic permission failure')
            put(path,value)
        with patch('vita_tree.publication.put',side_effect=deny_rollback):
            with self.assertRaises(PermissionError):
                with publish(self.workspace,'d'*32,branch['branch'],{'@metadata':'{}','main.tex':'New text'}):
                    self.fail('Publication should fail')
        self.assertFalse(self.workspace.release_worktree(branch['branch'])['released'])
        with self.assertRaisesRegex(ConflictError,'recovery is pending'):
            self.workspace.save(branch['branch'],'main.tex',branch['revision'],'Overwrite')
        self.workspace.close()
        self.workspace=Workspace(self.root)
        self.assertEqual(self.workspace.metadata_path(branch['branch']).read_text(),before_meta)
        self.assertEqual(self.workspace.read(branch['branch'],'main.tex'),SOURCE)
        self.assertNotIn(branch['branch'],self.workspace._pending_publications)

    def test_restart_rolls_back_interrupted_publication_but_preserves_external_edits(self):
        branch = self.pipeline_branch('interrupted-publication')
        location = Path(branch['worktree'])
        (location/'main.tex').write_text('partial new CV')
        report = location/'.vita/results/adapt.md';report.parent.mkdir(parents=True);report.write_text('external user report')
        journal = self.workspace.root/'publications'/('c'*32+'.json');journal.parent.mkdir()
        journal.write_text(json.dumps({'schemaVersion':1,'branch':branch['branch'],'entries':{
            'main.tex':{'old':SOURCE,'new':'partial new CV'},
            '.vita/results/adapt.md':{'old':None,'new':'AI report'}}}))
        self.workspace.close()
        self.workspace=Workspace(self.root)
        self.assertEqual((location/'main.tex').read_text(), SOURCE)
        self.assertEqual(report.read_text(), 'external user report')
        self.assertFalse(journal.exists())
