import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from vita_tree.workspace import Workspace, ConflictError, digest
from support import SOURCE, cleanup_repo, init_repo, git


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.temp.name))
        self.control = self.root / '.git/ai-control'
        self.control.mkdir()
        self.workspace = Workspace(self.root)
        self.labels = []
        self.environment = patch.dict(os.environ, {'VITA_TEST_CONTROL': str(self.control), 'VITA_TEST_SECRET': 'private-fixture-value'})
        self.environment.start()
        self.command = patch.object(self.workspace, 'vita_command', return_value=[sys.executable, str(Path(__file__).with_name('fake_ai_process.py'))])
        self.command.start()
        def fake_compile(folder, entry, engine='auto', output=None):
            output=output or folder/'__vt_output';output.mkdir(parents=True,exist_ok=True)
            pdf=output/(Path(entry).stem+'.pdf');pdf.write_bytes(b'%PDF-1.7\nsynthetic cover fixture')
            return {'pdf':pdf,'engine':'pdflatex','warnings':[]}
        self.cover_compile=patch('vita_tree.pdf.compile_document',side_effect=fake_compile)
        self.cover_builder=self.cover_compile.start()

    def tearDown(self):
        for label in self.labels:
            self.release(label)
        self.workspace.close()
        for thread in list(self.workspace._ai_threads):
            thread.join(timeout=15)
            self.assertFalse(thread.is_alive())
        self.cover_compile.stop()
        self.command.stop()
        self.environment.stop()
        cleanup_repo(self.temp)

    def branch(self, label, mode='success'):
        self.labels.append(label)
        return self.workspace.create('master', label, json.dumps({'label': label, 'mode': mode}), digest(SOURCE))

    def start(self, branch, **kwargs):
        return self.workspace.start_ai(branch['branch'], branch['revision'], branch['jobRevision'], **kwargs)

    def release(self, label):
        (self.control / (label + '.release')).touch()

    def wait(self, predicate):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.04)
        self.fail('Timed out waiting for controlled AI process')

    def finished(self, ident):
        self.wait(lambda: self.workspace.get_job(ident)['status'] not in self.workspace.ACTIVE_STATUSES)
        return self.workspace.get_job(ident)

    def test_all_processes_start_without_queue_and_branches_are_isolated(self):
        branches = [self.branch(label) for label in ('first', 'second', 'third')]
        run_config = Path(branches[2]['worktree']) / '.vita/config.json'
        run_config.parent.mkdir(exist_ok=True)
        run_config.write_text('{"marker":"captured-at-start"}')
        first, second, third = [self.start(branch, language=language) for branch, language in zip(branches, ('en', 'fr', 'de'))]
        run_config.write_text('{"marker":"changed-after-start"}')
        self.wait(lambda: all((self.control / (label + '.started')).exists() for label in ('first', 'second', 'third')))
        self.assertEqual(self.workspace.get_job(third['id'])['status'], 'running')
        self.assertFalse(any((self.control / (label + '.finished')).exists() for label in ('first', 'second', 'third')))
        with self.assertRaises(ConflictError):
            self.start(branches[0])
        for branch in branches:
            self.assertEqual(self.workspace.release_worktree(branch['branch'])['reason'], 'active')
            with self.assertRaises(ConflictError):
                self.workspace.save(branch['branch'], 'main.tex', branch['revision'], 'overwrite')
            with self.assertRaises(ConflictError):
                self.workspace.commit_preview(branch['branch'])
        other = self.branch('independent')
        self.workspace.save(other['branch'], 'main.tex', other['revision'], SOURCE + '\n% independent edit')
        self.release('second')
        self.assertEqual(self.finished(second['id'])['status'], 'succeeded')
        self.wait(lambda: (self.control / 'third.started').exists())
        self.assertEqual(self.workspace.get_job(first['id'])['status'], 'running')
        self.release('third'); self.release('first')
        for record, language in zip((first, second, third), ('en', 'fr', 'de')):
            result = self.finished(record['id'])
            self.assertEqual(result['status'], 'succeeded', result)
            self.assertEqual(result['language'], language)
            snapshot = self.workspace.snapshot(record['branch'])
            self.assertIn(record['branch'] + ' systems', snapshot['content'])
            self.assertEqual(snapshot['original'], SOURCE)
            self.assertEqual(snapshot['artifacts']['analyze']['content'], '# ' + record['branch'] + ' analyze')
            retained = self.workspace.job_result(record['id'])['files']
            self.assertEqual(retained['original/main.tex'], SOURCE)
            self.assertIn(record['branch'], retained['main.tex'])
        self.assertLess(float((self.control/'first.started').read_text()), float((self.control/'second.finished').read_text()))
        self.assertLess(float((self.control/'second.started').read_text()), float((self.control/'first.finished').read_text()))
        retained_config = self.workspace.root / 'runs' / third['id'] / '.vita/config.json'
        self.assertEqual(json.loads(retained_config.read_text())['marker'], 'captured-at-start')
        public = json.dumps(self.workspace.list_jobs())
        for secret in ('private-fixture-value', 'VITA_TEST_SECRET', SOURCE, 'source', 'env', 'runPath'):
            self.assertNotIn(secret, public)

    def test_failure_validation_and_external_conflicts_preserve_files(self):
        for label, mode in (('provider', 'provider-fail'), ('validation', 'invalid'), ('conflict', 'success')):
            with self.subTest(mode=mode):
                branch = self.branch(label, mode); record = self.start(branch)
                self.wait(lambda: (self.control / (label + '.started')).exists())
                if label == 'conflict':
                    (Path(branch['worktree']) / 'main.tex').write_text(SOURCE + '\n% external')
                self.release(label)
                result = self.finished(record['id'])
                self.assertEqual(result['status'], 'failed', result)
                expected = SOURCE + ('\n% external' if label == 'conflict' else '')
                self.assertEqual(self.workspace.read(label, 'main.tex'), expected)
                self.assertNotIn('private-fixture-value', json.dumps(result))
                self.assertIsNotNone(result['finishedAt'])

    def test_restart_keeps_history_and_review_flags_and_interrupts_active_jobs(self):
        done = self.start(self.branch('done')); self.release('done'); self.finished(done['id'])
        self.workspace.review_job(done['id'])
        running = self.start(self.branch('running'))
        another = self.start(self.branch('another'))
        self.assertEqual(another['status'], 'running')
        self.workspace.close()
        self.release('running')
        self.release('another')
        for thread in list(self.workspace._ai_threads):
            thread.join(timeout=15)
        reopened = Workspace(self.root)
        self.assertTrue(reopened.get_job(done['id'])['reviewed'])
        for ident in (running['id'], another['id']):
            self.assertEqual(reopened.get_job(ident)['status'], 'interrupted')
            self.assertFalse(reopened.get_job(ident)['reviewed'])
        reopened.review_job(running['id'])
        self.assertFalse(reopened.get_job(another['id'])['reviewed'])
        self.assertEqual(reopened.read('running', 'main.tex'), SOURCE)
        self.assertEqual(reopened.job_result(another['id'])['files']['original/main.tex'], SOURCE)
        reopened.close()

    def test_unclean_restart_marks_persisted_active_job_interrupted(self):
        record = {'id': 'a'*32, 'branch': 'master', 'status': 'running', 'step': 'adapt', 'createdAt': time.time(), 'reviewed': False}
        self.workspace._persist_job(record)
        recovered = Workspace(self.root)
        self.assertEqual(recovered.get_job(record['id'])['status'], 'interrupted')
        self.assertIsNotNone(recovered.get_job(record['id'])['finishedAt'])
        recovered.close()

    def test_release_clean_owned_worktree_allows_checkout_and_recreation(self):
        branch = self.branch('releasable')
        worktree = Path(branch['worktree'])
        git(worktree, 'add', 'job.md', 'main.tex'); git(worktree, 'commit', '-m', 'Job fixture')
        before = git(worktree, 'rev-parse', 'HEAD')
        release = self.workspace.release_worktree('releasable')
        self.assertTrue(release['released'], release)
        self.assertFalse(worktree.exists())
        git(self.root, 'checkout', 'releasable')
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.workspace.release_worktree('releasable')['reason'], 'external')
        git(self.root, 'checkout', 'master')
        snapshot = self.workspace.snapshot('releasable')
        self.workspace.save('releasable', 'main.tex', snapshot['revision'], SOURCE + '\n% reopened')
        self.assertTrue(worktree.is_dir())
        self.assertIn('reopened', self.workspace.read('releasable', 'main.tex'))

    def test_leave_during_run_releases_worktree_only_after_it_finishes_clean(self):
        branch = self.branch('leave-running', 'provider-fail')
        worktree = Path(branch['worktree'])
        git(worktree, 'add', 'main.tex', 'job.md'); git(worktree, 'commit', '-m', 'Saved input')
        record = self.start(branch)
        self.wait(lambda: (self.control / 'leave-running.started').exists())
        self.assertEqual(self.workspace.release_worktree('leave-running')['reason'], 'active')
        self.assertTrue(worktree.exists())
        self.release('leave-running')
        self.assertEqual(self.finished(record['id'])['status'], 'failed')
        self.wait(lambda: not worktree.exists())
        git(self.root, 'checkout', 'leave-running')

    def test_pdf_export_keeps_worktree_until_preview_finishes(self):
        from vita_tree.pdf import PDFCompiler
        branch = self.branch('preview')
        worktree = Path(branch['worktree'])
        git(worktree, 'add', 'main.tex', 'job.md'); git(worktree, 'commit', '-m', 'Saved input')
        compiler = PDFCompiler(self.workspace)
        with patch.object(compiler, '_compile', side_effect=lambda *args: self.workspace.release_worktree('preview')):
            self.assertEqual(compiler.compile('preview', 'current', 'auto')['reason'], 'active')
        self.assertFalse(worktree.exists())
        self.assertNotIn('preview', self.workspace._previewing)

    def test_release_preserves_dirty_ignored_locked_and_external_worktrees(self):
        branch = self.branch('keep')
        worktree = Path(branch['worktree'])
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'dirty')
        git(worktree, 'add', 'job.md'); git(worktree, 'commit', '-m', 'Job fixture')
        (worktree / 'main.tex').write_text(SOURCE + '\n% local')
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'dirty')
        (worktree / 'main.tex').write_text(SOURCE)
        (worktree / '.gitignore').write_text('local-secret\n')
        git(worktree, 'add', '.gitignore'); git(worktree, 'commit', '-m', 'Ignore fixture')
        (worktree / 'local-secret').write_text('preserve-me')
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'dirty')
        self.assertEqual((worktree / 'local-secret').read_text(), 'preserve-me')
        (worktree / 'local-secret').unlink()
        git(self.root, 'worktree', 'lock', str(worktree))
        self.assertEqual(self.workspace.release_worktree('keep')['reason'], 'locked')
        git(self.root, 'worktree', 'unlock', str(worktree))
        external = self.root / '.git/external-worktree'
        git(self.root, 'worktree', 'add', '-b', 'external', str(external))
        self.assertEqual(self.workspace.release_worktree('external')['reason'], 'external')
        self.assertTrue(external.exists())

    def pipeline_source(self):
        source = self.root / '.git/fake-vita'
        prompts = source / 'vita/assets/prompts'
        prompts.mkdir(parents=True, exist_ok=True)
        for step in ('extract', 'review', 'cover'):
            (prompts / (step + '.md')).write_text('Fixture task')
        self.workspace.vita_source = source

    def pipeline_branch(self, label, **options):
        branch = self.branch(label)
        self.workspace.save(label, 'job.md', branch['jobRevision'], json.dumps({'label': label, 'pipeline': True, **options}))
        return self.workspace.snapshot(label)

    def test_full_pipeline_retains_reports_states_and_selected_routing(self):
        self.pipeline_source()
        branch = self.pipeline_branch('pipeline', extraction=True)
        shared = self.root / '.vita/skills/adapt/style.md'
        shared.parent.mkdir(parents=True); shared.write_text('Shared writing instructions')
        local = Path(branch['worktree']) / '.vita/skills/adapt/style.md'
        local.parent.mkdir(parents=True); local.write_text('Branch-specific writing instructions')
        record = self.start(branch, workflow={'extract': True, 'review': True, 'cover': True})
        local.write_text('Changed after launch')
        self.release('pipeline')
        result = self.finished(record['id'])
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertEqual([stage['id'] for stage in result['stages']], ['extract', 'analyze', 'adapt', 'review', 'cover', 'validating'])
        for stage in result['stages']:
            self.assertEqual(stage['status'], 'succeeded')
            self.assertLessEqual(stage['startedAt'], stage['finishedAt'])
        for left, right in zip(result['stages'], result['stages'][1:]):
            self.assertLessEqual(left['finishedAt'], right['startedAt'])
        retained_skill = self.workspace.root / 'runs' / record['id'] / '.vita/skills/adapt/style.md'
        self.assertEqual(retained_skill.read_text(), 'Branch-specific writing instructions')
        self.assertNotIn('writing instructions', json.dumps(self.workspace.list_jobs()))
        snapshot = self.workspace.snapshot('pipeline')
        self.assertEqual(set(snapshot['artifacts']), {'extract', 'analyze', 'adapt', 'review', 'delta', 'cover'})
        self.assertIn('Initial analysis', snapshot['artifacts']['analyze']['content'])
        retained = self.workspace.job_result(record['id'])['files']
        for filename in ('job.json', 'job.toon', 'analysis.json', 'review.json', 'delta.json', 'delta.md'):
            self.assertIn('.vita/results/' + filename, retained)
            self.assertEqual(self.workspace.read('pipeline', '.vita/results/' + filename), retained['.vita/results/' + filename])
        self.assertIn('Dear hiring team', self.workspace.read('pipeline', 'cover-letter.tex'))
        review = self.workspace.commit_preview('pipeline')
        self.assertIn('cover-letter.tex', [file['path'] for file in review['files']])
        reopened = Workspace(self.root)
        self.assertEqual(reopened.get_job(record['id'])['stages'], result['stages'])
        reopened.close()

    def test_pipeline_failure_blocks_downstream_and_preserves_branch(self):
        self.pipeline_source()
        for failure in ('extract', 'review', 'cover'):
            branch = self.pipeline_branch('fail-' + failure, fail=failure, extraction=True)
            record = self.start(branch, workflow={'extract': True, 'review': True, 'cover': True})
            self.release(branch['branch'])
            result = self.finished(record['id'])
            self.assertEqual(result['status'], 'failed', result)
            stages = {item['id']: item for item in result['stages']}
            self.assertEqual(stages[failure]['status'], 'failed')
            self.assertEqual(stages['validating']['status'], 'blocked')
            self.assertEqual(self.workspace.read(branch['branch'], 'main.tex'), SOURCE)
            self.assertEqual(self.workspace.snapshot(branch['branch'])['artifacts'], {})

    def test_cover_pdf_is_retained_previewed_and_saved_without_modifying_cv(self):
        from vita_tree.pdf import PDFCompiler, PDFExistsError
        self.pipeline_source();branch=self.pipeline_branch('cover-pdf')
        record=self.start(branch,workflow={'steps':['cover']});self.release('cover-pdf')
        result=self.finished(record['id']);self.assertEqual(result['status'],'succeeded',result)
        self.assertIn('PDF ready',result['message'])
        self.assertEqual(self.workspace.read('cover-pdf','main.tex'),SOURCE)
        self.assertEqual(self.workspace.job_result(record['id'])['coverPdf'],{'runId':record['id']})
        compiler=PDFCompiler(self.workspace)
        with self.assertRaisesRegex(ValueError,'Start the Cover letter step first'):
            compiler.compile('master','current','auto','cover')
        preview=compiler.compile('cover-pdf','current','auto','cover',record['id'])
        self.assertEqual(preview['filename'],'cover-letter-Jordan_Lee.pdf')
        saved=compiler.save(preview['id'],'cover-pdf')
        self.assertTrue(Path(saved['path']).read_bytes().startswith(b'%PDF-'))
        with self.assertRaises(PDFExistsError):compiler.save(preview['id'],'cover-pdf')
        other=self.branch('other-cover')
        with self.assertRaises(ConflictError):compiler.compile(other['branch'],'current','auto','cover',record['id'])
        current=self.workspace.read('cover-pdf','cover-letter.tex')
        from vita_tree.workspace import atomic_write
        atomic_write(Path(branch['worktree'])/'cover-letter.tex',current+'% changed')
        with self.assertRaises(ConflictError):compiler.save(preview['id'],'cover-pdf')
        # A retained PDF still opens after restarting the server/workspace.
        reopened=Workspace(self.root)
        try:self.assertIsNotNone(reopened.cover_pdf_result(record['id']))
        finally:reopened.close()

    def test_cover_compilation_failure_preserves_branch_and_source_for_inspection(self):
        self.pipeline_source();branch=self.pipeline_branch('cover-tex-failure')
        location=Path(branch['worktree']);(location/'cover-letter.tex').write_text('previous letter')
        # Recapture source revisions after adding a previous letter.
        self.cover_builder.side_effect=ValueError('private-provider-canary: missing TeX package')
        record=self.start(branch,workflow={'steps':['cover']});self.release('cover-tex-failure')
        result=self.finished(record['id']);self.assertEqual(result['status'],'failed',result)
        self.assertIn('cover-letter PDF could not be created',result['message'])
        self.assertNotIn('private-provider-canary',str(result))
        self.assertEqual(self.workspace.read('cover-tex-failure','main.tex'),SOURCE)
        self.assertEqual((location/'cover-letter.tex').read_text(),'previous letter')
        self.assertIn('cover-letter.tex',self.workspace.job_result(record['id'])['files'])
        self.assertIsNone(self.workspace.job_result(record['id'])['coverPdf'])
        self.assertEqual(next(stage['status'] for stage in result['stages'] if stage['id']=='cover'),'failed')

    def test_invalid_cover_and_report_conflict_preserve_local_work(self):
        self.pipeline_source()
        branch = self.pipeline_branch('invalid-cover', invalid_cover=True)
        record = self.start(branch, workflow={'cover': True})
        self.release('invalid-cover')
        result = self.finished(record['id'])
        self.assertEqual(result['status'], 'failed', result)
        self.assertEqual(next(stage['status'] for stage in result['stages'] if stage['id']=='cover'), 'failed')
        self.assertEqual(result['stages'][-1]['status'], 'blocked')
        self.assertEqual(self.workspace.read('invalid-cover', 'main.tex'), SOURCE)
        branch = self.pipeline_branch('report-conflict')
        record = self.start(branch, workflow={'review': True})
        self.wait(lambda: (self.control / 'report-conflict.started').exists())
        report = Path(branch['worktree']) / '.vita/results/review.md'
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text('Manual review: preserve this')
        self.release('report-conflict')
        self.assertEqual(self.finished(record['id'])['status'], 'failed')
        self.assertEqual(report.read_text(), 'Manual review: preserve this')
        self.assertEqual(self.workspace.read('report-conflict', 'main.tex'), SOURCE)

    def test_optional_steps_require_capability_and_boolean_choices(self):
        self.workspace.vita_source = None
        branch = self.branch('legacy')
        for options in ({'extract': True}, {'cover': 'yes'}, {'unknown': True}, []):
            with self.assertRaises(ValueError):
                self.start(branch, workflow=options)
        record = self.start(branch)
        self.release('legacy')
        result = self.finished(record['id'])
        self.assertEqual(result['status'], 'succeeded')
        states = {stage['id']: stage['status'] for stage in result['stages']}
        self.assertEqual(states['extract'], 'skipped')
        self.assertEqual(states['review'], 'skipped')
        self.assertEqual(states['cover'], 'skipped')

    def test_each_step_runs_alone_and_only_updates_its_outputs(self):
        self.pipeline_source()
        for step in ('extract', 'analyze', 'adapt', 'review', 'cover', 'validating'):
            with self.subTest(step=step):
                branch = self.pipeline_branch('only-' + step)
                location = Path(branch['worktree'])
                previous = location / '.vita/results/cover.md'
                previous.parent.mkdir(parents=True, exist_ok=True)
                previous.write_text('Previous letter report')
                meta = self.workspace.metadata(branch['branch'])
                record = self.start(branch, workflow={'steps': [step]})
                self.release(branch['branch'])
                result = self.finished(record['id'])
                self.assertEqual(result['status'], 'succeeded', result)
                self.assertEqual({t['id'] for t in result['stages'] if t['status'] == 'succeeded'}, {step, 'validating'})
                calls = {p.name.split('.')[-2] for p in self.control.glob(branch['branch'] + '.*.started')}
                self.assertEqual(calls, set() if step == 'validating' else {step})
                if step != 'adapt':
                    self.assertEqual(self.workspace.read(branch['branch'], 'main.tex'), SOURCE)
                    self.assertEqual(self.workspace.metadata(branch['branch']), meta)
                if step != 'cover':
                    self.assertEqual(previous.read_text(), 'Previous letter report')

    def test_separate_runs_reuse_matching_analysis_and_preserve_comparison(self):
        self.pipeline_source()
        branch = self.pipeline_branch('separate', extraction=True, require_analysis=True)
        self.release('separate')
        for step in ('extract', 'analyze', 'adapt', 'review', 'cover', 'adapt'):
            # The second adaptation is a legitimate no-op, not a failed run.
            record = self.start(branch, workflow={'steps': [step]})
            self.assertEqual(self.finished(record['id'])['status'], 'succeeded', self.workspace.get_job(record['id']))
            branch = self.workspace.snapshot('separate')
            if step == 'adapt':
                original = branch['original']
            elif step in ('review', 'cover'):
                self.assertEqual(branch['original'], original)
        self.assertIn('delta', branch['artifacts'])
        self.assertIn('analyze', branch['artifacts'])
        # Analyze invalidates the old score comparison, without erasing the review.
        record = self.start(branch, workflow={'steps': ['analyze']})
        self.assertEqual(self.finished(record['id'])['status'], 'succeeded')
        snapshot = self.workspace.snapshot('separate')
        self.assertNotIn('delta', snapshot['artifacts'])
        self.assertIn('review', snapshot['artifacts'])

    def test_stale_analysis_is_not_reused_and_stale_delta_is_removed(self):
        self.pipeline_source()
        branch = self.pipeline_branch('stale-analysis', forbid_analysis=True)
        results = Path(branch['worktree']) / '.vita/results'
        results.mkdir(parents=True, exist_ok=True)
        (results / 'analysis.json').write_text(json.dumps({'metadata': {'job_sha256': 'old-job'}}))
        (results / 'analyze.md').write_text('Advice for another job')
        (results / 'delta.md').write_text('Old comparison')
        record = self.start(branch, workflow={'steps': ['review']})
        self.assertEqual(self.finished(record['id'])['status'], 'succeeded')
        self.assertFalse((results / 'delta.md').exists())
        self.assertEqual((results / 'analyze.md').read_text(), 'Advice for another job')
        record = self.start(self.workspace.snapshot(branch['branch']), workflow={'steps': ['adapt']})
        self.assertEqual(self.finished(record['id'])['status'], 'succeeded')

    def test_report_only_mutation_and_conflict_do_not_overwrite_branch(self):
        self.pipeline_source()
        branch = self.pipeline_branch('unexpected', modify_cv='review')
        record = self.start(branch, workflow={'steps': ['review']})
        self.assertEqual(self.finished(record['id'])['status'], 'failed')
        self.assertEqual(self.workspace.read('unexpected', 'main.tex'), SOURCE)
        branch = self.pipeline_branch('single-conflict', hold='review')
        record = self.start(branch, workflow={'steps': ['review']})
        self.wait(lambda: (self.control / 'single-conflict.review.started').exists())
        (Path(branch['worktree']) / 'main.tex').write_text(SOURCE + '\n% external edit')
        (self.control / 'single-conflict.review.release').touch()
        self.assertEqual(self.finished(record['id'])['status'], 'failed')
        self.assertTrue(self.workspace.read('single-conflict', 'main.tex').endswith('% external edit'))

    def test_validate_requires_neither_cli_nor_job_and_ai_requires_saved_inputs(self):
        branch = self.workspace.snapshot('master')
        with patch.object(self.workspace, 'vita_command', return_value=None):
            record = self.start(branch, workflow={'steps': ['validating']})
            self.assertEqual(self.finished(record['id'])['status'], 'succeeded')
        with self.assertRaisesRegex(ValueError, 'job description'):
            self.start(branch, workflow={'steps': ['analyze']})
        with self.assertRaises(ConflictError):
            self.start({**branch, 'revision': 'stale'}, workflow={'steps': ['analyze']})

    def test_extraction_is_independent_of_cv_syntax_but_validation_reports_it(self):
        self.pipeline_source()
        branch = self.pipeline_branch('extract-with-incomplete-cv')
        self.workspace.save(branch['branch'], 'main.tex', branch['revision'], 'Incomplete LaTeX source')
        branch = self.workspace.snapshot(branch['branch'])
        record = self.start(branch, workflow={'steps': ['extract']})
        self.assertEqual(self.finished(record['id'])['status'], 'succeeded')
        self.assertEqual(self.workspace.read(branch['branch'], 'main.tex'), 'Incomplete LaTeX source')
        record = self.start(branch, workflow={'steps': ['validating']})
        result = self.finished(record['id'])
        self.assertEqual(result['status'], 'failed')
        self.assertIn('not parseable', result['message'])
