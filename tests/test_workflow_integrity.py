"""Focused workflow regressions using synthetic inputs; no provider requests."""
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from vita_tree.workflow import clean_stages, plan, reusable_reports, transition
from vita_tree.workspace import digest
from support import SOURCE
import test_jobs as support


class EvidenceTests(unittest.TestCase):
    def test_analysis_without_matching_input_evidence_is_not_reused(self):
        reports = {'.vita/results/analysis.json': json.dumps({'metadata': {'job_sha256': 'job'}}),
                   '.vita/results/analysis.md': 'Advice for a previous CV'}
        self.assertEqual(reusable_reports(reports, 'job'), {})
        self.assertEqual(reusable_reports(reports, 'job', evidence={'analyze': 'old'},
                                          expected={'analyze': 'new'}), {})
        self.assertEqual(reusable_reports(reports, 'job', evidence={'analyze': 'same'},
                                          expected={'analyze': 'same'}), reports)

    def test_review_is_a_persistent_nonfailure_state(self):
        stages = transition(plan({'steps': ['adapt', 'cover']}, {'cover': True}), step='adapt')
        waiting = transition(stages, terminal='awaiting_review')
        self.assertEqual(next(s for s in waiting if s['id'] == 'adapt')['status'], 'review')
        self.assertEqual(next(s for s in waiting if s['id'] == 'cover')['status'], 'pending')
        self.assertEqual(clean_stages(waiting), waiting)


class WorkspaceIntegrityTests(unittest.TestCase):
    def setUp(self):
        support.JobTests.setUp(self)
        self.workspace.vita_source = None

    tearDown = support.JobTests.tearDown
    branch = support.JobTests.branch
    release = support.JobTests.release
    wait = support.JobTests.wait
    finished = support.JobTests.finished
    start = support.JobTests.start
    pipeline_source = support.JobTests.pipeline_source
    pipeline_branch = support.JobTests.pipeline_branch

    def test_optional_extract_does_not_block_an_independent_analysis(self):
        branch = self.branch('no-extract')
        self.release('no-extract')
        missing = dict(state='missing', revision=None, approvedRevision=None, token='missing')
        with patch('vita_tree.requirements_review.supported', return_value=True), patch(
                'vita_tree.requirements_review.state', return_value=missing):
            run = self.start(branch, workflow={'steps': ['analyze']})
            result = self.finished(run['id'])
            self.wait(lambda: not self.workspace._ai_threads)
        self.assertEqual(result['status'], 'succeeded', result)
        self.assertFalse((self.control/'no-extract.extract.calls').exists())
        self.assertIn('analyze', self.workspace.snapshot(branch['branch'])['artifacts'])

    def test_pending_requirements_create_a_review_state_instead_of_startup_failure(self):
        branch = self.branch('pending-start')
        pending = dict(state='pending', revision='a'*64, approvedRevision=None, token='pending')
        with patch('vita_tree.requirements_review.supported', return_value=True), patch(
                'vita_tree.requirements_review.state', return_value=pending):
            run = self.start(branch, workflow={'steps': ['analyze']})
            result = self.finished(run['id'])
            self.wait(lambda: not self.workspace._ai_threads)
        self.assertEqual(result['status'], 'awaiting_review')
        self.assertEqual(result['requirementsDraft'], 'a'*64)
        self.assertFalse(list(self.control.glob('*.calls')))

    def test_automatic_pending_requirements_use_the_explicit_policy(self):
        branch = self.branch('auto-pending')
        pending = dict(state='pending', revision='a'*64, approvedRevision=None, token='pending')
        with patch('vita_tree.requirements_review.supported', return_value=True), patch(
                'vita_tree.requirements_review.state', return_value=pending), patch(
                'vita_tree.requirements_review.view', return_value=pending), patch(
                'vita_tree.requirements_review.change') as approve, patch.object(self.workspace, 'continue_review') as continued:
            run = self.start(branch, workflow={'steps': ['analyze']}, review_policy='automatic')
            self.wait(lambda: not self.workspace._ai_threads)
        approve.assert_called_once_with(self.workspace, branch['branch'], 'pending', 'a'*64,
                                        approve=True, confirmed=True, automatic=True)
        self.assertEqual(continued.call_args.args[0], run['id'])

    def test_final_cv_pdf_is_saved_with_exact_source_provenance(self):
        branch = self.branch('final-pdf')
        self.release('final-pdf')
        run = self.start(branch, workflow={'steps': ['adapt']})
        result = self.finished(run['id'])
        self.assertEqual(result['status'], 'succeeded', result)
        location = Path(branch['worktree'])
        self.assertTrue((location/'cv-final.pdf').read_bytes().startswith(b'%PDF-'))
        metadata = json.loads((location/'.vita/results/final-pdfs.json').read_text())['cv-final.pdf']
        self.assertEqual(metadata['source'], digest(self.workspace.read(branch['branch'], 'main.tex')))
        self.assertEqual(metadata['runId'], run['id'])
        self.assertEqual(metadata['engine'], 'pdflatex')
        self.assertIsNotNone(self.workspace.final_pdf_result(branch['branch'], 'cv'))
        self.workspace.save(branch['branch'], 'main.tex', metadata['source'], SOURCE+'\n% later edit')
        self.assertIsNone(self.workspace.final_pdf_result(branch['branch'], 'cv'))

    def test_native_completed_applications_get_local_pdf_checks_without_ai(self):
        branch = self.branch('native-final-pdf')
        manager = self.workspace.jobenu
        with patch.object(manager, 'entries', return_value=[{'branch': branch['branch'], 'status': 'complete', 'workspace': branch['worktree']}]):
            manager.finalize_outputs({'id': 'f'*32})
        run = next(iter(self.workspace.jobs.values()))
        self.assertEqual(self.finished(run['id'])['status'], 'succeeded')
        self.assertTrue((Path(branch['worktree'])/'cv-final.pdf').exists())
        self.assertFalse(list(self.control.glob('*.calls')))

    def test_analysis_is_reused_only_until_its_cv_changes(self):
        self.pipeline_source()
        branch = self.pipeline_branch('matching-context', require_analysis=True)
        self.release('matching-context')
        first = self.start(branch, workflow={'steps': ['analyze']})
        self.assertEqual(self.finished(first['id'])['status'], 'succeeded')
        self.wait(lambda: not self.workspace._ai_threads)
        branch = self.workspace.snapshot(branch['branch'])
        second = self.start(branch, workflow={'steps': ['adapt']})
        self.assertEqual(self.finished(second['id'])['status'], 'succeeded')
        self.wait(lambda: not self.workspace._ai_threads)
        branch = self.workspace.snapshot(branch['branch'])
        third = self.start(branch, workflow={'steps': ['review']})
        # The fixture deliberately refuses Review without matching analysis.
        result = self.finished(third['id'])
        self.assertTrue(result['contextInvalidated'])
        self.assertEqual(result['status'], 'failed')

    def test_pdf_failure_preserves_source_and_reuses_completed_ai(self):
        branch = self.branch('compile-recovery')
        self.release('compile-recovery')
        def fail_adapted_pdf(folder, entry, engine='auto', output=None):
            # Let setup compile the original CV; fail only after tailoring.
            if entry == 'main.tex' and (folder/entry).read_text(encoding='utf-8') != branch['content']:
                raise ValueError('Synthetic final compilation failure')
            return self.fake_compile(folder, entry, engine, output)
        with patch('vita_tree.pdf.compile_document', side_effect=fail_adapted_pdf):
            run = self.start(branch, workflow={'steps': ['adapt']})
            result = self.finished(run['id'])
            self.wait(lambda: not self.workspace._ai_threads)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['preflight']['ready'], result)
        self.assertIn('adapt', result['checkpointSteps'], result)
        self.assertEqual(next(stage['status'] for stage in result['stages'] if stage['id'] == 'validating'), 'failed')
        self.assertEqual(self.workspace.read(branch['branch'], 'main.tex'), SOURCE)
        self.assertFalse((Path(branch['worktree'])/'cv-final.pdf').exists())
        snapshot = self.workspace.snapshot(branch['branch'])
        preview = self.workspace.resume_ai(run['id'], snapshot['revision'], snapshot['jobRevision'], preview=True)
        self.assertEqual(preview['reuse'], ['adapt'])
        retry = self.workspace.resume_ai(run['id'], snapshot['revision'], snapshot['jobRevision'], token=preview['token'])
        self.assertEqual(self.finished(retry['id'])['status'], 'succeeded')
        self.assertEqual(len((self.control/'compile-recovery.adapt.calls').read_text().splitlines()), 1)

    def test_child_inherits_saved_settings_without_sharing_mutable_state(self):
        settings = self.workspace.save_ai_settings('master', {'default': {'provider': 'codex', 'model': 'fixture-shared'},
                                                             'steps': {'cover': {'model': 'fixture-cover'}}})
        child = self.branch('settings-child')
        self.assertEqual(self.workspace.ai_settings(child['branch']), settings)
        updated = self.workspace.save_ai_settings('master', {'default': {'provider': 'codex', 'model': 'fixture-updated'}})
        self.assertNotEqual(updated, settings)
        self.assertEqual(self.workspace.ai_settings(child['branch']), settings)
        self.assertEqual(self.workspace.metadata(child['branch'])['aiSettingsOrigin'], 'master')

    def test_imported_runs_are_in_the_global_monitor_and_acknowledged_individually(self):
        runs = [dict(id=key * 32, source='jobenu', branch='imported', status='awaiting_review',
                     createdAt=1, reviewed=False) for key in ('a', 'b')]
        with patch.object(self.workspace.jobenu, 'history', return_value=runs):
            self.assertEqual({r['id'] for r in self.workspace.list_jobs()['runs']}, {r['id'] for r in runs})
            self.workspace.review_job(runs[0]['id'])
            self.assertTrue(self.workspace.get_job(runs[0]['id'])['reviewed'])
            self.assertFalse(self.workspace.get_job(runs[1]['id'])['reviewed'])

    def test_review_reserves_only_its_application(self):
        from vita_tree.workspace import ConflictError
        first, other = self.branch('reviewed'), self.branch('independent-review')
        errors = []
        def edit():
            try:
                self.workspace.save(first['branch'], 'job.md', first['jobRevision'], 'changed')
            except ConflictError:
                errors.append('conflict')
            self.workspace.save(other['branch'], 'job.md', other['jobRevision'], 'independent')
        with self.workspace.review_guard(first['branch']):
            thread = threading.Thread(target=edit)
            thread.start(); thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ['conflict'])
        self.assertEqual(digest(self.workspace.read(other['branch'], 'job.md')), digest('independent'))

    def test_failed_publication_rolls_back_source_and_pdf_together(self):
        from vita_tree.publication import pdf_content, publish
        branch = self.branch('atomic-pdf')
        output = self.root/'synthetic.pdf'
        output.write_bytes(b'%PDF-1.7\nsynthetic')
        with self.assertRaisesRegex(ValueError, 'Synthetic'):
            with publish(self.workspace, 'a'*32, branch['branch'],
                         {'main.tex': SOURCE+'\n% reviewed', 'cv-final.pdf': pdf_content(output)}):
                raise ValueError('Synthetic publication failure')
        self.assertEqual(self.workspace.read(branch['branch'], 'main.tex'), SOURCE)
        self.assertFalse((Path(branch['worktree'])/'cv-final.pdf').exists())

    def test_factual_approval_preserves_engine_and_compiles_parser_limited_sources(self):
        from vita_tree import factual_review
        from test_factual_contract import report as make_report
        branch = self.branch('review-engine')
        for step, character in [('cover', 'c'), ('adapt', 'd')]:
            with self.subTest(step=step):
                ident = character*32
                self.workspace.jobs[ident] = dict(id=ident, branch=branch['branch'], status='awaiting_review',
                                                 compileEngine='lualatex', attempt=1)
                stage = self.workspace.root/'runs'/ident
                stage.mkdir(parents=True)
                (stage/'main.tex').write_text(SOURCE, encoding='utf-8')
                (stage/'cover-letter.tex').write_text(SOURCE, encoding='utf-8')
                proposal = make_report(SOURCE, SOURCE.replace('Python', 'Rust'), step)
                proposal['target'] = 'cover-letter.tex' if step == 'cover' else 'main.tex'
                manifest = dict(state='pending', revision=proposal['revision'], key='b'*64)
                from vita_tree.checkpoints import fingerprint
                def backend(workspace, scratch, request):
                    (scratch/proposal['target']).write_text(proposal['document'], encoding='utf-8')
                    return dict(report={**proposal, 'status': 'approved', 'application_status': 'applied'}, omitted=False)
                with patch.object(factual_review, '_load', return_value=(manifest, proposal)), patch.object(
                        factual_review, '_matching'), patch.object(factual_review, '_stage_matches', return_value=True), patch.object(
                        factual_review, 'backend', side_effect=backend), patch.object(factual_review, 'view', return_value={'state': 'resolved'}), patch(
                        'vita_tree.checkpoints.write_checkpoint', return_value=True), patch(
                        'vita_tree.latex.parse_document', return_value={'error': 'Synthetic rendering limitation'}):
                    result = self.workspace.apply_factual_review(ident, proposal['revision'], fingerprint(manifest),
                        [{'id': item['id'], 'action': 'accept'} for item in proposal['changes']], True)
                self.assertEqual(result['state'], 'resolved')
                self.assertEqual(self.cover_builder.call_args.kwargs['engine'], 'lualatex')
                saved = json.loads((self.workspace.root/'factual-reviews'/ident/'manifest.json').read_text())
                self.assertEqual(saved['state'], 'resolved')
                self.assertEqual(self.workspace.read(branch['branch'], 'main.tex'), SOURCE)


class CoverTextTests(unittest.TestCase):
    def test_copyable_text_preserves_language_and_does_not_invent_short_wording(self):
        from vita_tree.exports import cover_outputs
        outputs = cover_outputs(r'\documentclass{article}\begin{document}Bonjour, merci pour votre attention.\end{document}')
        self.assertEqual(outputs['text'], 'Bonjour, merci pour votre attention.')
        self.assertEqual(outputs['characters'], len(outputs['text']))
        self.assertIsNone(outputs['short'])
        self.assertIn('no extra AI request', outputs['shortLimitation'])


class PendingPDFCheckpointTests(unittest.TestCase):
    def test_compilation_can_be_retried_from_verified_cover_source(self):
        import tempfile
        from vita_tree import checkpoints
        from support import cleanup_repo
        temporary = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        try:
            root = Path(temporary.name)/'checkpoints'
            files = {name: None for name in checkpoints.ARTIFACTS}
            files.update({'main.tex': SOURCE, 'cover-letter.tex': SOURCE})
            outcome = dict(status='success', verified=True, backend=None)
            saved = checkpoints.write_checkpoint(root, 'a'*32, 'cover', 'b'*64, files, outcome, pdf_pending=True)
            self.assertTrue(saved)
            manifest, restored = checkpoints.load_checkpoint(root, 'a'*32, 'cover')
            self.assertTrue(manifest['pdfPending'])
            self.assertEqual(restored['cover-letter.tex'], SOURCE)
            self.assertFalse((root/('a'*32)/'cover/cover-letter.pdf').exists())
        finally:
            cleanup_repo(temporary)
