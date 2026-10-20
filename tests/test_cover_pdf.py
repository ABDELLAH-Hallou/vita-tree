import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from vita_tree.pdf import compile_document
from support import cleanup_repo


class CoverCompilerTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='.vita-tree-test-',dir=Path.cwd())
        self.root=Path(self.temp.name)
        (self.root/'cover-letter.tex').write_text(r'\documentclass{article}\begin{document}Fixture letter\end{document}')

    def tearDown(self):
        cleanup_repo(self.temp)

    def test_cover_compiler_uses_safe_flags_and_the_cover_entry(self):
        output=self.root/'compiled'
        calls=[]
        def engine(args,**kwargs):
            calls.append(args)
            if '--version' in args:return subprocess.CompletedProcess(args,0,b'MiKTeX',b'')
            self.assertIn('-no-shell-escape',args)
            self.assertIn('--disable-installer',args)
            self.assertIn('--disable-write18',args)
            self.assertEqual(args[-1],'./cover-letter.tex')
            self.assertEqual(kwargs['cwd'],self.root)
            self.assertEqual(kwargs['env']['openin_any'],'p')
            self.assertEqual(kwargs['env']['openout_any'],'p')
            (output/'cover-letter.pdf').write_bytes(b'%PDF-1.7\nfixture')
            return subprocess.CompletedProcess(args,0,b'LaTeX Warning: fixture',b'')
        with patch('vita_tree.pdf.shutil.which',return_value='fixture-engine'),patch('vita_tree.pdf.subprocess.run',side_effect=engine):
            result=compile_document(self.root,'cover-letter.tex',output=output)
        self.assertEqual(result['pdf'],output/'cover-letter.pdf')
        self.assertEqual(result['engine'],'pdflatex')
        self.assertTrue(result['warnings'])
        self.assertEqual(len(calls),3)

    def test_missing_engine_and_timeout_are_actionable(self):
        with patch('vita_tree.pdf.shutil.which',return_value=None):
            with self.assertRaisesRegex(ValueError,'Install MiKTeX or TeX Live'):
                compile_document(self.root,'cover-letter.tex')
        calls=[subprocess.CompletedProcess([],0,b'engine',b''),subprocess.TimeoutExpired('fixture',90)]
        with patch('vita_tree.pdf.shutil.which',return_value='fixture-engine'),patch('vita_tree.pdf.subprocess.run',side_effect=calls):
            with self.assertRaisesRegex(ValueError,'longer than 90 seconds'):
                compile_document(self.root,'cover-letter.tex')
