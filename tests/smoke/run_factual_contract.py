"""Exercise Tree against real Vita CV factual-changes/1, without providers."""
import argparse
import json
import os
from pathlib import Path
import sys
import unittest
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from test_jobs import JobTests
from support import SOURCE
from vita_tree.workspace import Workspace, ConflictError, digest
from vita_tree import checkpoints, factual_review


class FactualWorkflowTests(unittest.TestCase):
    tearDown = JobTests.tearDown
    wait = JobTests.wait
    finished = JobTests.finished
    release = JobTests.release

    def setUp(self):
        JobTests.setUp(self)
        import vita
        self.workspace.vita_source = Path(vita.__file__).resolve().parent.parent
        self.command.stop()
        self.command = patch.object(self.workspace, 'vita_command', return_value=[sys.executable, str(Path(__file__).with_name('factual_ai.py'))])
        self.command.start()

    def prepare(self, steps=None, previous_cover=None, asset=None):
        branch = self.workspace.create('master', 'facts', json.dumps({'label': 'facts', 'pipeline': True}), digest(SOURCE))
        from requirements_fixtures import seed
        seed(self.workspace, 'facts')
        if previous_cover is not None:
            (Path(branch['worktree'])/'cover-letter.tex').write_text(previous_cover, encoding='utf-8')
        if asset:
            (Path(branch['worktree'])/'style.md').write_text(asset, encoding='utf-8')
        self.labels.append('facts');self.release('facts')
        run = self.workspace.start_ai('facts', branch['revision'], branch['jobRevision'], provider='codex',
                                      workflow={'steps': steps or ['extract', 'analyze', 'adapt', 'cover']})
        result = self.finished(run['id'])
        self.assertEqual(result['status'], 'failed', result)
        self.assertEqual(result['factualReview']['state'], 'pending', result)
        self.assertEqual(self.workspace.read('facts', 'main.tex'), SOURCE)
        return branch, result

    def choices(self, view, mode='mixed'):
        if mode != 'mixed':
            return [{'id': item['id'], 'action': mode} for item in view['items']]
        self.assertEqual(len(view['items']), 3, view)
        return [{'id': view['items'][0]['id'], 'action': 'accept'},
                {'id': view['items'][1]['id'], 'action': 'reject'},
                {'id': view['items'][2]['id'], 'action': 'edit', 'text': r'Languages & Python, SQL, TypeScript \\'}]

    def apply(self, run, mode='mixed'):
        view = self.workspace.factual_review(run['id'])
        return self.workspace.apply_factual_review(run['id'], view['revision'], view['token'], self.choices(view, mode), True)

    def retry(self, run, **changes):
        snap = self.workspace.snapshot('facts')
        plan = self.workspace.resume_ai(run['id'], snap['revision'], snap['jobRevision'], preview=True, **changes)
        child = self.workspace.resume_ai(run['id'], snap['revision'], snap['jobRevision'], token=plan['token'], **changes)
        return plan, self.finished(child['id'])

    def test_approve_continue_publishes_once_and_repeated_submit_reuses_child(self):
        branch, parent = self.prepare(['adapt'])
        self.apply(parent)
        child = self.workspace.continue_review(parent['id'], branch['revision'], branch['jobRevision'])
        duplicate = self.workspace.continue_review(parent['id'], branch['revision'], branch['jobRevision'])
        self.assertEqual(child['id'], duplicate['id'])
        final = self.finished(child['id'])
        self.assertEqual(final['status'], 'succeeded', final)
        self.assertEqual(final['parentRunId'], parent['id'])
        self.assertIn('adapt', final['checkpointSteps'])
        self.assertIn('TypeScript', self.workspace.read('facts', 'main.tex'))
        self.assertNotIn('Built OOP services', self.workspace.read('facts', 'main.tex'))

    def test_automatic_full_pipeline_records_policy_and_publishes_after_validation(self):
        branch = self.workspace.create('master', 'automatic', json.dumps({'label':'automatic','pipeline':True}), digest(SOURCE))
        self.labels.append('automatic');self.release('automatic')
        with patch.dict(os.environ, {'VITA_TEST_CANONICAL':'1'}):
            run = self.workspace.start_ai('automatic',branch['revision'],branch['jobRevision'],provider='codex',
                workflow={'steps':['extract','analyze','adapt','cover']},review_policy='automatic')
            deadline=time.monotonic()+180
            while self.workspace._ai_threads and time.monotonic()<deadline:time.sleep(.1)
            self.assertFalse(self.workspace._ai_threads, 'Automatic chain did not finish within 180 seconds')
        runs = [r for r in self.workspace.list_jobs()['runs'] if r['branch']=='automatic']
        final = runs[0]
        self.assertEqual(final['status'],'succeeded',runs)
        self.assertEqual(len(runs),4,runs)
        self.assertTrue(all(r['reviewPolicy']=='automatic' for r in runs))
        self.assertEqual(final['rootRunId'],run['id'])
        self.assertEqual(self.workspace.snapshot('automatic')['original'],SOURCE)
        self.assertIn('dependable systems',self.workspace.read('automatic','main.tex'))
        self.assertIn('Built OOP services',self.workspace.read('automatic','cover-letter.tex'))
        for record in runs:
            if record.get('factualReview'):
                provenance=self.workspace.factual_review(record['id'])['provenance']
                self.assertEqual(provenance['method'],'automatic_run_policy')
                self.assertEqual(provenance['actor'],'automatic_policy')
        from vita_tree import requirements_review
        context=requirements_review.context_for(self.workspace,'automatic')
        _,_,marker=requirements_review.paths(self.workspace,context)
        self.assertEqual(requirements_review.read(marker)['method'],'automatic_run_policy')

    def test_approved_draft_changed_before_continuation_stops_safely(self):
        branch,parent=self.prepare(['adapt'])
        self.apply(parent)
        self.workspace.save('facts','main.tex',branch['revision'],SOURCE+'\n% local draft')
        with self.assertRaises(ConflictError):
            self.workspace.continue_review(parent['id'],branch['revision'],branch['jobRevision'])
        snapshot=self.workspace.snapshot('facts')
        with self.assertRaisesRegex(ConflictError,'no longer matches'):
            self.workspace.continue_review(parent['id'],snapshot['revision'],snapshot['jobRevision'])
        self.assertIn('local draft',self.workspace.read('facts','main.tex'))
        self.assertEqual(len(self.workspace.list_jobs()['runs']),1)

    def test_mixed_decisions_matching_cover_restart_and_atomic_publication(self):
        branch, parent = self.prepare()
        view = self.workspace.factual_review(parent['id'])
        self.assertTrue(all(item['sources'] and item['unresolvedMeaning'] for item in view['items']))
        self.assertFalse(parent['resumeAvailable'])
        with self.assertRaisesRegex(ConflictError, 'factual'):
            self.workspace.resume_ai(parent['id'], branch['revision'], branch['jobRevision'], preview=True)
        resolved = self.apply(parent)
        self.assertEqual(resolved['state'], 'resolved')
        self.assertEqual(resolved['provenance']['method'], 'explicit_ui_review')
        self.assertEqual(self.workspace.read('facts', 'main.tex'), SOURCE)
        self.workspace.close()
        self.command.stop()
        self.workspace = Workspace(self.root, vita_source=self.workspace.vita_source)
        self.command = patch.object(self.workspace, 'vita_command', return_value=[sys.executable, str(Path(__file__).with_name('factual_ai.py'))])
        self.command.start()
        self.assertEqual(self.workspace.factual_review(parent['id'])['provenance'], resolved['provenance'])
        plan, cover = self.retry(parent)
        self.assertEqual(plan['reuse'], ['extract', 'analyze', 'adapt'])
        self.assertEqual(cover['factualReview']['step'], 'cover', cover)
        letter = self.workspace.factual_review(cover['id'])
        self.assertIn('dependable systems', letter['proposed'])
        self.assertIn('TypeScript', letter['proposed'])
        self.assertNotIn('Built OOP services', letter['proposed'])
        self.apply(cover, 'accept')
        plan, final = self.retry(cover)
        self.assertEqual(plan['reuse'], ['extract', 'analyze', 'adapt', 'cover'])
        self.assertEqual(final['status'], 'succeeded', final)
        snap = self.workspace.snapshot('facts')
        self.assertEqual(snap['original'], SOURCE)
        self.assertIn('dependable systems', snap['content']);self.assertNotIn('OOP', snap['cover'])
        provenance = json.loads((Path(snap['worktree'])/'.vita/results/adapt.decisions.json').read_text(encoding='utf-8'))
        self.assertEqual([d['action'] for d in provenance['decisions']], ['accept', 'reject', 'edit'])

    def test_cancellation_missing_decisions_and_stale_saved_or_captured_drafts(self):
        branch, run = self.prepare(['adapt'])
        view = self.workspace.factual_review(run['id'])
        token = view['token']
        # Opening/closing a panel does not submit a decision or alter the token.
        self.assertEqual(self.workspace.factual_review(run['id'])['token'], token)
        with self.assertRaisesRegex(ValueError, 'Confirm'):
            self.workspace.apply_factual_review(run['id'], view['revision'], token, self.choices(view))
        with self.assertRaisesRegex(ValueError, 'every change'):
            self.workspace.apply_factual_review(run['id'], view['revision'], token, [], True)
        self.workspace.save('facts', 'main.tex', branch['revision'], SOURCE+'\n% editor draft')
        with self.assertRaisesRegex(ConflictError, 'changed'):
            self.apply(run)
        self.assertIn('editor draft', self.workspace.read('facts', 'main.tex'))
        self.assertEqual(self.workspace.factual_review(run['id'])['state'], 'pending')
        self.workspace.save('facts', 'main.tex', digest(SOURCE+'\n% editor draft'), SOURCE)
        stage = self.workspace.root/'runs'/run['id']/'main.tex'
        stage.write_text(SOURCE+'\n% external retained-draft edit', encoding='utf-8')
        with self.assertRaisesRegex(ConflictError, 'captured draft changed'):
            self.apply(run)

    def test_concurrent_external_edit_and_failed_decision_leave_pending_original(self):
        branch, run = self.prepare(['adapt'])
        original = factual_review.backend
        def changed(workspace, stage, request):
            result = original(workspace, stage, request)
            (Path(branch['worktree'])/'main.tex').write_text(SOURCE+'\n% concurrent edit', encoding='utf-8')
            return result
        with patch.object(factual_review, 'backend', side_effect=changed):
            with self.assertRaises(ConflictError):self.apply(run)
        self.assertEqual(self.workspace.factual_review(run['id'])['state'], 'pending')
        self.assertIsNone(checkpoints.load_checkpoint(self.workspace.root/'checkpoints', run['id'], 'adapt'))
        self.assertIn('concurrent edit', self.workspace.read('facts', 'main.tex'))

    def test_rejected_changes_and_changed_inputs_invalidate_downstream(self):
        branch, parent = self.prepare()
        self.apply(parent, 'reject')
        plan, cover = self.retry(parent)
        self.assertEqual(plan['reuse'], ['extract', 'analyze', 'adapt'])
        self.assertNotIn('dependable systems', self.workspace.factual_review(cover['id'])['proposed'])
        self.apply(cover, 'reject')
        plan, final = self.retry(cover)
        self.assertEqual(final['status'], 'succeeded', final)
        self.assertEqual(self.workspace.read('facts', 'main.tex'), SOURCE)
        self.assertFalse(self.workspace.read('facts', 'cover-letter.tex'))
        self.assertIsNone(self.workspace.cover_pdf_result(final['id']))

    def test_changed_route_invalidates_reviewed_checkpoint_and_does_not_autoapprove(self):
        branch, parent = self.prepare()
        self.apply(parent)
        plan, repeated = self.retry(parent, ai_config={'default': {'provider': 'codex', 'model': 'different'}})
        self.assertEqual(plan['reuse'], [])
        self.assertEqual(repeated['factualReview']['state'], 'pending')
        self.assertEqual(self.workspace.read('facts', 'main.tex'), SOURCE)

    def test_interrupted_review_commit_requires_review_after_restart_and_can_retry_different_choices(self):
        branch, run = self.prepare(['adapt'])
        write = factual_review._write
        def interrupted(path, value):
            if path.name == 'manifest.json' and value.get('state') == 'resolved':
                raise OSError('synthetic review commit failure')
            return write(path, value)
        with patch.object(factual_review, '_write', side_effect=interrupted):
            with self.assertRaises(OSError):self.apply(run)
        self.workspace.close()
        self.command.stop()
        self.workspace = Workspace(self.root, vita_source=self.workspace.vita_source)
        self.command = patch.object(self.workspace, 'vita_command', return_value=[sys.executable, str(Path(__file__).with_name('factual_ai.py'))])
        self.command.start()
        self.assertEqual(self.workspace.factual_review(run['id'])['state'], 'pending')
        self.assertFalse(self.workspace.get_job(run['id'])['resumeAvailable'])
        self.assertIsNone(checkpoints.load_checkpoint(self.workspace.root/'checkpoints', run['id'], 'adapt'))
        # A leftover checkpoint cannot authorize an unresolved review.
        with self.assertRaises(ConflictError):self.retry(run)
        self.apply(run, 'reject')
        plan, final = self.retry(run)
        self.assertEqual(plan['reuse'], ['adapt'])
        self.assertEqual(final['status'], 'succeeded', final)
        self.assertEqual(self.workspace.read('facts', 'main.tex'), SOURCE)

    def test_damaged_review_marker_cannot_authorize_a_checkpoint_after_restart(self):
        branch, run = self.prepare(['adapt'])
        self.apply(run)
        marker = self.workspace.root/'factual-reviews'/run['id']/'manifest.json'
        marker.write_text('{"state":"resolved","revision":"private-wording"}', encoding='utf-8')
        self.workspace.close()
        self.command.stop()
        self.workspace = Workspace(self.root, vita_source=self.workspace.vita_source)
        self.command = patch.object(self.workspace, 'vita_command', return_value=[sys.executable, str(Path(__file__).with_name('factual_ai.py'))])
        self.command.start()
        public = self.workspace.get_job(run['id'])
        self.assertEqual(public['factualReview']['state'], 'unavailable')
        self.assertNotIn('private-wording', json.dumps(public))
        self.assertFalse(public['resumeAvailable'])
        self.assertIsNone(checkpoints.load_checkpoint(self.workspace.root/'checkpoints', run['id'], 'adapt'))
        with self.assertRaises(ConflictError):self.retry(run)

    def test_include_configuration_and_job_changes_cannot_approve_stale_sources(self):
        branch, run = self.prepare(['adapt'])
        worktree = Path(branch['worktree'])
        for name, content in [('extra.tex', 'New included input'), ('.vita/config.json', '{"language":"fr"}'), ('job.md', 'Changed job')]:
            path = worktree/name;previous = path.read_bytes() if path.is_file() else None
            path.parent.mkdir(parents=True, exist_ok=True);path.write_text(content, encoding='utf-8')
            with self.assertRaisesRegex(ConflictError, 'changed'):self.apply(run)
            if previous is None:path.unlink()
            else:path.write_bytes(previous)
        self.assertEqual(self.workspace.factual_review(run['id'])['state'], 'pending')

    def test_existing_cover_draft_is_captured_and_preserved_when_letter_is_rejected(self):
        previous = SOURCE.replace('reliable systems', 'previous letter draft')
        branch, run = self.prepare(['cover'], previous_cover=previous)
        self.assertEqual(self.workspace.factual_review(run['id'])['original'], previous)
        self.apply(run, 'reject')
        plan, final = self.retry(run)
        self.assertEqual(plan['reuse'], ['cover'])
        self.assertEqual(final['status'], 'succeeded', final)
        self.assertEqual(self.workspace.read('facts', 'cover-letter.tex'), previous)

    def test_retained_style_or_configuration_edits_conflict_without_touching_application(self):
        branch, run = self.prepare(['adapt'], asset='Captured application style')
        stage = self.workspace.root/'runs'/run['id']
        for name in ('style.md', '.vita/extensions.json'):
            path = stage/name;before = path.read_bytes()
            path.write_text('External retained-input edit', encoding='utf-8')
            with self.assertRaisesRegex(ConflictError, 'captured draft changed'):self.apply(run)
            path.write_bytes(before)
        self.assertEqual(self.workspace.read('facts', 'main.tex'), SOURCE)
        self.apply(run)
        plan, final = self.retry(run)
        self.assertEqual(plan['reuse'], ['adapt'])
        self.assertEqual(final['status'], 'succeeded', final)


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--vita-source', type=Path)
    args = parser.parse_args()
    if args.vita_source:
        sys.path.insert(0, str(args.vita_source.resolve()))
        os.environ['PYTHONPATH'] = str(args.vita_source.resolve()) + os.pathsep + os.environ.get('PYTHONPATH', '')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FactualWorkflowTests))
    raise SystemExit(not result.wasSuccessful())


if __name__ == '__main__':main()
