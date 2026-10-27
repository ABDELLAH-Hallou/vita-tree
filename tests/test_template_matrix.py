"""Portable corpus/source tests run without a TeX installation or AI provider."""
import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from template_matrix import (after_expectations, apply_edits, load_corpus, make_repository,
                             sources, structure, sweep_leaves)
from run_template_matrix import compile_case, inspect_boxes, package_versions, missing_miktex_format
from review_template_matrix import review_report
import json
import subprocess
from support import cleanup_repo
from vita_tree.pdf import CompilationError
from vita_tree.preflight import compile_failure
from vita_tree.observability import Diagnostics
from vita_tree.workspace import Workspace, ConflictError


class TemplateMatrixTests(unittest.TestCase):
    def test_missing_format_probe_never_builds_or_installs_it(self):
        with patch('run_template_matrix.engine_executable', return_value='trusted-kpsewhich'), patch('run_template_matrix.subprocess.run') as run:
            run.return_value = subprocess.CompletedProcess([], 1, b'', b'')
            self.assertTrue(missing_miktex_format('lualatex', Path.cwd(), {}))
            self.assertEqual(run.call_args.args[0], ['trusted-kpsewhich', '--engine=luahbtex', '--format=fmt', 'lualatex.fmt'])
            run.return_value = subprocess.CompletedProcess([], 0, b'installed-format', b'')
            self.assertFalse(missing_miktex_format('lualatex', Path.cwd(), {}))

    def test_visual_signoff_requires_every_matching_page_and_explicit_observations(self):
        from template_matrix import sha
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'page.png').write_bytes(b'synthetic-image')
            report = dict(results=[dict(id='fixture', engines=dict(xelatex=[dict(snapshot='before', pages=[
                dict(number=1, image='page.png', imageSha256=sha(b'synthetic-image'))])]))])
            path = root/'results.json'; path.write_text(json.dumps(report))
            self.assertEqual(review_report(path), 1)
            with self.assertRaises(AssertionError): review_report(path, True)
            ledger = root/'visual-review.json'; data=json.loads(ledger.read_text())
            data['reviewer']='Synthetic reviewer';data['pages'][0].update(status='pass', notes='Synthetic review test')
            ledger.write_text(json.dumps(data))
            self.assertEqual(review_report(path, True), 1)
            (root/'page.png').write_bytes(b'changed')
            with self.assertRaisesRegex(AssertionError,'page changed'): review_report(path, True)

    def test_recorded_package_versions_keep_dates_and_exclude_local_paths(self):
        self.assertEqual(package_versions('*File List*\n geometry.sty 2020/01/02 v5.9 Page Geometry\n secret.sty private/local/path\n ***********'),
                         ['geometry.sty 2020/01/02 v5.9 Page Geometry'])

    def test_versioned_hashes_and_feature_contract(self):
        corpus = load_corpus()
        features = {feature for fixture in corpus['fixtures'] for feature in fixture['features']}
        self.assertTrue({'custom-environments', 'macro-arguments', 'escaped-text', 'tables',
                         'minipage-columns', 'nested-files', 'unicode', 'rtl', 'long-document'} <= features)
        self.assertEqual(len(corpus['fixtures']), 11)
        self.assertTrue(all(fixture['limits'] for fixture in corpus['fixtures']))

    def test_every_exposed_leaf_stays_inside_its_originating_span(self):
        count = escaped = 0
        for fixture in load_corpus()['fixtures']:
            with self.subTest(fixture=fixture['id']):
                files = sources(fixture)
                documents, _ = structure(fixture, files)
                result = sweep_leaves(documents, files)
                count += result['checkedLeaves']
                escaped += result['decodedMacroOrSpecialLeaves']
        self.assertGreaterEqual(count, 300)
        self.assertGreaterEqual(escaped, 10)

    def test_named_edits_use_workspace_conflicts_and_preserve_all_other_files(self):
        for fixture in load_corpus()['fixtures']:
            if not fixture['edits']:
                continue
            with self.subTest(fixture=fixture['id']):
                temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
                workspace = None
                try:
                    repo = make_repository(Path(temp.name), fixture)
                    workspace = Workspace(repo, diagnostics=Diagnostics(repo/'.git/test-logs'))
                    current, edits = apply_edits(workspace, fixture)
                    self.assertEqual(len(edits), len(fixture['edits']))
                    structure(after_expectations(fixture), current)
                    # A captured graph cannot authorize a save against a later draft.
                    snapshot = workspace.snapshot('master')
                    change = fixture['edits'][0]
                    file = next(item for item in snapshot['files'] if item['path'] == change['path'])
                    (repo/change['path']).write_text(current[change['path']]+'\n% external edit', encoding='utf-8')
                    with self.assertRaises(ConflictError):
                        workspace.save('master', change['path'], file['revision'], content='wrong revision',
                                       project_revision=snapshot['projectRevision'])
                    self.assertIn('external edit', (repo/change['path']).read_text(encoding='utf-8'))
                finally:
                    if workspace:
                        workspace.close()
                        workspace.diagnostics.close()
                    cleanup_repo(temp)

    def test_page_checks_detect_clipping_overlap_omission_and_orphans(self):
        xml = '''<html><page width="100" height="100">
          <word xMin="-2" yMin="10" xMax="30" yMax="20">Heading</word>
          <word xMin="5" yMin="10" xMax="35" yMax="20">Overlap</word>
          </page><page width="100" height="100">
          <word xMin="10" yMin="10" xMax="30" yMax="20">Entry</word></page></html>'''
        _, problems = inspect_boxes(xml, {'required': ['Missing'], 'perPage': {'1': ['Entry']},
                                          'associations': [['Heading', 'Entry']]})
        self.assertEqual({p['kind'] for p in problems},
                         {'clipping', 'overlap', 'omission', 'page_omission', 'orphaned_association'})
        pages, problems = inspect_boxes(xml.replace('xMin="-2"', 'xMin="1"').replace('yMin="10" xMax="35" yMax="20"',
                                 'yMin="30" xMax="35" yMax="40"'), {'required': ['Heading', 'Entry']})
        self.assertEqual(len(pages), 2)
        self.assertEqual(problems, [])

    def test_dependency_errors_are_not_parser_defects(self):
        self.assertEqual(compile_failure(CompilationError('engine_missing', 'Unavailable'))['code'], 'engine_missing')
        self.assertEqual(compile_failure(ValueError("File `matrix-missing.sty' not found"))['code'], 'missing_package')
        self.assertEqual(compile_failure(ValueError('Unbalanced group'))['code'], 'compile_failed')
        fixture = next(f for f in load_corpus()['fixtures'] if f['id'] == 'invalid-source')
        documents, _ = structure(fixture, sources(fixture))
        self.assertTrue(documents['main.tex']['error'])

    def test_compiler_cannot_mutate_the_snapshot_even_when_compilation_fails(self):
        fixture = copy.deepcopy(load_corpus()['fixtures'][0])
        def mutate(folder, *args):
            (folder/'main.tex').write_text('Changed by compiler', encoding='utf-8')
            raise ValueError('Failed compiler')
        with tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd()) as temporary:
            with patch('run_template_matrix.compile_document', side_effect=mutate), patch('run_template_matrix.engine_executable', side_effect=ValueError()):
                with self.assertRaisesRegex(AssertionError, 'modified captured source'):
                    compile_case(Path(temporary), fixture, sources(fixture), 'pdflatex', 'before', {})
