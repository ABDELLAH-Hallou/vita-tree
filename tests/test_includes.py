"""Synthetic multi-file CVs: identity, optimistic writes and project boundaries."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from support import init_repo, cleanup_repo, git
from vita_tree import includes
from vita_tree.workspace import Workspace, ConflictError, digest
from vita_tree.pdf import PDFCompiler
from vita_tree.latex import parse_document

MAIN = r'''\documentclass{article}
\begin{document}
Root text. \input{sections/experience}
\input{education.tex}
\end{document}
'''
EXPERIENCE = r'''\section{Experience}
Identical employer.
\input{sections/details}
'''
EDUCATION = '\\section{Education}\nIdentical employer.\n'
DETAILS = 'Nested synthetic achievement.\n'


class IncludeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.vita-tree-test-', dir=Path.cwd())
        self.root = init_repo(Path(self.temp.name))
        (self.root/'sections').mkdir()
        for path, value in {'main.tex': MAIN, 'sections/experience.tex': EXPERIENCE,
                            'sections/details.tex': DETAILS, 'education.tex': EDUCATION}.items():
            (self.root/path).write_text(value, encoding='utf-8')
        git(self.root, 'add', '.'); git(self.root, 'commit', '-m', 'Synthetic includes')
        self.workspace = Workspace(self.root)

    def tearDown(self):
        cleanup_repo(self.temp)

    def test_nested_files_have_local_offsets_and_duplicate_text_never_crosses_files(self):
        snapshot = self.workspace.snapshot('master')
        files = {item['path']: item for item in snapshot['files']}
        self.assertEqual(set(files), {'main.tex', 'sections/experience.tex', 'sections/details.tex', 'education.tex'})
        self.assertEqual(snapshot['includeDiagnostics'], [])
        file = files['sections/experience.tex']
        key, leaf = next((key,leaf) for key,leaf in file['document']['leaves'].items() if 'Identical employer' in leaf['text'])
        self.assertEqual(leaf['path'], file['path'])
        self.assertIn('Identical employer', file['content'][leaf['start']:leaf['end']])
        result = self.workspace.save('master', file['path'], file['revision'], leaf=key, text='Changed & verified', project_revision=snapshot['projectRevision'])
        self.assertIn(r'Changed \& verified', result['content'])
        self.assertEqual((self.root/'education.tex').read_text(), EDUCATION)
        self.assertEqual((self.root/'main.tex').read_text(), MAIN)

    def test_dependency_and_file_changes_reject_stale_edits(self):
        snapshot = self.workspace.snapshot('master')
        for changed in ('education.tex', 'sections/experience.tex', 'main.tex'):
            old = (self.root/changed).read_text()
            (self.root/changed).write_text(old+'\n% external edit')
            with self.assertRaises(ConflictError):
                self.workspace.save('master', 'sections/details.tex', digest(DETAILS), 'Do not overwrite', project_revision=snapshot['projectRevision'])
            self.assertEqual((self.root/'sections/details.tex').read_text(), DETAILS)
            (self.root/changed).write_text(old)
        with self.assertRaises(ConflictError):
            self.workspace.save('master', 'sections/details.tex', digest(DETAILS), 'Missing graph revision')
        with self.assertRaises(ValueError):
            self.workspace.save('master', 'unrelated.tex', digest(''), 'Not an include', project_revision=snapshot['projectRevision'])

    def test_missing_cycles_unsupported_and_comment_definition_discovery(self):
        source = MAIN.replace(r'\input{education.tex}', r'''\input{missing}
\input{../escape}\input{/absolute}\input{.git/private}\input{code.py}
\input{\dynamic}\input unbraced\import{x}{y}\includeonly{sections/experience}
% \input{commented}
\newcommand{\later}{\input{not-executed}}
''')
        (self.root/'main.tex').write_text(source)
        (self.root/'sections/details.tex').write_text(r'\input{main}')
        result = includes.project(self.workspace, 'master')
        codes = {item['code'] for item in result['diagnostics']}
        self.assertTrue({'missing', 'cycle', 'unsupported', 'unsafe'} <= codes, result)
        self.assertFalse(any('commented' in item['path'] or 'not-executed' in item['path'] for item in result['diagnostics']))
        self.assertNotIn('missing.tex', result['files'])

    def test_traversal_symlinks_ignored_and_secret_directories_cannot_be_edited(self):
        for target in ('../outside', '.env/secret', '.vita/secret', 'secret[ab]', 'C:/outside'):
            (self.root/'main.tex').write_text(MAIN+r'\input{'+target+'}')
            result = includes.project(self.workspace, 'master')
            self.assertTrue(result['diagnostics'], target)
            self.assertNotIn(target+'.tex', result['files'])
        (self.root/'main.tex').write_text(MAIN+r'\input{private}')
        (self.root/'.gitignore').write_text('private.tex\n')
        (self.root/'private.tex').write_text('Private synthetic content')
        snapshot = self.workspace.snapshot('master')
        self.assertNotIn('private.tex', {file['path'] for file in snapshot['files']})
        self.assertNotIn('Private synthetic content', str(snapshot))
        self.assertNotIn('private.tex', self.workspace.publish_paths(self.root))
        try:
            (self.root/'linked.tex').symlink_to(self.root/'education.tex')
        except OSError:
            self.skipTest('Creating a symlink requires OS support/permission')
        (self.root/'main.tex').write_text(MAIN+r'\input{linked}')
        self.assertNotIn('linked.tex', includes.project(self.workspace, 'master')['files'])
        with self.assertRaises(ValueError):
            self.workspace.save('master','linked.tex',digest(EDUCATION),'Unsafe',project_revision=self.workspace.snapshot('master')['projectRevision'])

    def test_branch_captures_include_drafts_originals_and_restart(self):
        (self.root/'sections/details.tex').write_text('Uncommitted included draft')
        snapshot = self.workspace.snapshot('master')
        branch = self.workspace.create('master','application','Synthetic role',snapshot['revision'],project_revision=snapshot['projectRevision'])
        location = Path(branch['worktree'])
        self.assertEqual((location/'sections/details.tex').read_text(), 'Uncommitted included draft')
        (location/'sections/details.tex').write_text('New included version')
        restored = Workspace(self.root).snapshot('application')
        file = next(file for file in restored['files'] if file['path']=='sections/details.tex')
        self.assertEqual(file['original'], 'Uncommitted included draft')
        self.assertIn('+New included version', file['diff'])
        self.assertEqual((self.root/'sections/details.tex').read_text(), 'Uncommitted included draft')
        with self.assertRaises(ConflictError):
            self.workspace.create('application','stale','Role',branch['revision'],project_revision=branch['projectRevision'])

    def test_deleted_include_is_not_resurrected_on_new_application(self):
        (self.root/'education.tex').unlink()
        branch = self.workspace.create('master','missing','Synthetic role',digest(MAIN))
        self.assertFalse((Path(branch['worktree'])/'education.tex').exists())
        self.assertTrue(any(item['code']=='missing' for item in branch['includeDiagnostics']))
        self.assertIn('education.tex',{file['path'] for file in self.workspace.commit_preview('missing')['files']})

    def test_include_changes_are_reviewed_and_committed_only_after_confirmation(self):
        git(self.root,'init','--bare',str(self.root/'.git/remote.git'))
        git(self.root,'remote','add','origin',str(self.root/'.git/remote.git'))
        branch = self.workspace.create('master','application','Role',digest(MAIN))
        location = Path(branch['worktree'])
        (location/'education.tex').write_text('Reviewed education edit')
        (location/'unrelated.tex').write_text('Unrelated')
        preview = self.workspace.commit_preview('application')
        self.assertEqual({file['path'] for file in preview['files']}, {'education.tex','job.md'})
        (location/'sections/details.tex').write_text('Changed during review')
        with self.assertRaises(ConflictError):
            self.workspace.commit_and_push('application','Synthetic update',preview['review'])
        preview = self.workspace.commit_preview('application')
        self.workspace.commit_and_push('application','Synthetic update',preview['review'])
        self.assertEqual(git(location,'show','--format=','--name-only','HEAD').splitlines(), ['education.tex','job.md','sections/details.tex'])
        self.assertEqual(git(location,'status','--porcelain','--','unrelated.tex'), '?? unrelated.tex')

    def test_compilation_uses_original_included_draft_and_export_rejects_stale_pdf(self):
        (self.root/'sections/details.tex').write_text('Captured original draft')
        branch = self.workspace.create('master','pdf','Role',digest(MAIN))
        location = Path(branch['worktree']);(location/'sections/details.tex').write_text('Current included version')
        compiler = PDFCompiler(self.workspace)
        seen = []
        def compile_fixture(folder, entry, engine):
            self.assertEqual(entry, 'main.tex')
            value = (folder/'sections/details.tex').read_text()
            seen.append(value)
            output=folder/'output.pdf';output.write_bytes(b'%PDF-1.7\nfixture')
            return dict(pdf=output, engine='pdflatex', warnings=[])
        with patch('vita_tree.pdf.compile_document',side_effect=compile_fixture):
            before = compiler.compile('pdf','original','auto')
            after = compiler.compile('pdf','current','auto')
        self.assertEqual(seen, ['Captured original draft','Current included version'])
        (location/'sections/details.tex').write_text('Changed after compilation')
        with self.assertRaises(ConflictError):compiler.save(after['id'],'pdf')
        with self.assertRaises(ConflictError):compiler.save(before['id'],'pdf')

    def test_include_edit_during_compilation_does_not_publish_a_preview(self):
        compiler = PDFCompiler(self.workspace)
        def compile_fixture(folder, entry, engine):
            (self.root/'education.tex').write_text('Concurrent education')
            output=folder/'output.pdf';output.write_bytes(b'%PDF-1.7\nfixture')
            return dict(pdf=output, engine='pdflatex', warnings=[])
        with patch('vita_tree.pdf.compile_document',side_effect=compile_fixture):
            with self.assertRaisesRegex(ConflictError,'included files changed'):
                compiler.compile('master','current','auto')
        self.assertFalse(compiler.results)
        self.assertEqual((self.root/'education.tex').read_text(),'Concurrent education')

    def test_pending_entry_include_is_in_commit_review_without_unrelated_tex(self):
        (self.root/'new.tex').write_text('New synthetic section')
        (self.root/'unrelated.tex').write_text('Not referenced')
        pending=MAIN.replace(r'\end{document}',r'\input{new}\end{document}')
        preview=self.workspace.commit_preview('master',source_revision=digest(MAIN),source_content=pending)
        self.assertEqual({file['path'] for file in preview['files']},{'main.tex','new.tex'})

    def test_resource_limits_and_duplicate_includes(self):
        graph = includes.discover('main.tex', {'main.tex':r'\input{a}\input{a}', 'a.tex':'same'}.get)
        self.assertEqual(set(graph['files']), {'main.tex','a.tex'})
        values = {f'{i}.tex':r'\input{'+str(i+1)+'}' for i in range(30)}
        graph = includes.discover('0.tex', values.get)
        self.assertEqual(len(graph['files']), 16)
        self.assertTrue(any(item['code']=='limit' for item in graph['diagnostics']))

    def test_committed_view_reads_regular_includes_without_creating_a_worktree(self):
        git(self.root,'update-ref','refs/remotes/origin/remote-only','HEAD')
        snapshot=self.workspace.snapshot('remote-only')
        self.assertIsNone(snapshot['worktree'])
        self.assertFalse(snapshot['editable'])
        files={item['path']:item for item in snapshot['files']}
        self.assertEqual(files['sections/details.tex']['content'],DETAILS)
        self.assertEqual(files['education.tex']['content'],EDUCATION)

    def test_git_symlink_placeholder_is_not_an_editable_include(self):
        # Windows with core.symlinks=false checks out a symlink as a regular file.
        # Its Git identity must still exclude it from the editable source graph.
        target=self.root/'placeholder.tex';target.write_text('education.tex',encoding='utf-8')
        blob=git(self.root,'hash-object','-w',str(target))
        git(self.root,'update-index','--add','--cacheinfo',f'120000,{blob},placeholder.tex')
        (self.root/'main.tex').write_text(MAIN+r'\input{placeholder}',encoding='utf-8')
        graph=includes.project(self.workspace,'master')
        self.assertNotIn('placeholder.tex',graph['files'])
        self.assertTrue(any(item['code']=='unreadable' for item in graph['diagnostics']))

    def test_include_directives_are_not_editable_prose(self):
        parsed=parse_document(MAIN,'main.tex')
        self.assertIn('sections/experience',parsed['html'])
        self.assertFalse(any('sections/experience' in item['text'] or 'education.tex' in item['text'] for item in parsed['leaves'].values()))

    def test_committed_symlink_is_diagnosed_as_blocked_and_preserved_on_copy(self):
        git(self.root,'config','core.symlinks','false')
        target=self.root/'placeholder.tex';target.write_text('education.tex',encoding='utf-8')
        blob=git(self.root,'hash-object','-w',str(target))
        git(self.root,'update-index','--add','--cacheinfo',f'120000,{blob},placeholder.tex')
        source=MAIN+r'\input{placeholder}'
        (self.root/'main.tex').write_text(source,encoding='utf-8')
        git(self.root,'add','main.tex');git(self.root,'commit','-m','Synthetic Git symlink')
        git(self.root,'update-ref','refs/remotes/origin/remote-link','HEAD')
        snapshot=self.workspace.snapshot('remote-link')
        item=next(item for item in snapshot['includeDiagnostics'] if item['path']=='placeholder.tex')
        self.assertEqual(item['code'],'unreadable')
        branch=self.workspace.create('remote-link','link-copy','Role',digest(source))
        self.assertEqual((Path(branch['worktree'])/'placeholder.tex').read_text(),'education.tex')

    def test_snapshot_copy_must_match_captured_included_files(self):
        from vita_tree.pdf import export_snapshot
        def changed(repository,commit,target,working=None):
            export_snapshot(repository,commit,target,working)
            (target/'education.tex').write_text('Unexpected captured version',encoding='utf-8')
        with patch('vita_tree.pdf.export_snapshot',side_effect=changed),patch('vita_tree.pdf.compile_document') as compiler:
            with self.assertRaisesRegex(ConflictError,'while capturing this PDF'):
                PDFCompiler(self.workspace).compile('master','current','auto')
            compiler.assert_not_called()

    def test_header_fragment_is_rendered_once_with_its_origin(self):
        document=parse_document(r'\name{Synthetic Candidate}', 'contact.tex')
        self.assertEqual(document['html'].count('cv-name'),1)
        self.assertTrue(all(item['path']=='contact.tex' for item in document['leaves'].values()))

    def test_nested_include_auxiliary_directory_cannot_escape_output(self):
        output=self.root/'compiler-output';output.mkdir()
        outside=self.root/'.git/outside-output';outside.mkdir()
        sentinel=outside/'preserved.txt';sentinel.write_text('Synthetic sentinel')
        try:(output/'sections').symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('Directory symlinks require OS support/permission')
        from vita_tree.pdf import compile_document
        with patch('vita_tree.pdf.engine_executable') as engine:
            with self.assertRaisesRegex(ValueError,'Symlink'):
                compile_document(self.root,'main.tex',output=output)
            engine.assert_not_called()
        self.assertEqual(sentinel.read_text(),'Synthetic sentinel')
