import unittest
from vita_tree.latex import parse_document, replace_leaf, lint_source
from support import SOURCE, CUSTOM_ENVIRONMENT_SOURCE


class LatexTests(unittest.TestCase):
    def test_custom_environment_definition_preserves_body_and_source_mapped_edits(self):
        doc = parse_document(CUSTOM_ENVIRONMENT_SOURCE)
        self.assertIsNone(doc['error'])
        self.assertEqual(lint_source(CUSTOM_ENVIRONMENT_SOURCE), [])
        self.assertIn('Sample experience.', doc['html'])
        self.assertTrue(any('approximate layout' in warning for warning in doc['warnings']))
        key, leaf = next((key, leaf) for key, leaf in doc['leaves'].items()
                         if leaf['text'] == 'Sample experience.')
        edited = replace_leaf(CUSTOM_ENVIRONMENT_SOURCE, key, 'Updated & reviewed.')
        self.assertEqual(edited, CUSTOM_ENVIRONMENT_SOURCE[:leaf['start']] +
                         r'Updated \& reviewed.' + CUSTOM_ENVIRONMENT_SOURCE[leaf['end']:])
        self.assertIsNone(parse_document(edited)['error'])

    def test_lint_offset_after_custom_definition_remains_utf16(self):
        source = CUSTOM_ENVIRONMENT_SOURCE.replace('Sample experience.', '\U0001f600 Sample experience.')
        diagnostic, = lint_source(source + '}')
        offset = len(source.encode('utf-16-le')) // 2
        self.assertEqual((diagnostic['from'], diagnostic['to']), (offset, offset + 1))

    def test_definition_bodies_are_tokens_not_live_environments_or_math(self):
        for definition in (
            r'\newenvironment*{wrapped}[1][x]{\begin{list}{}{}}{\end{list}}',
            r'\renewenvironment{wrapped}{\begin{list}{}{}}{\end{list}}',
            r'\provideenvironment{wrapped}{\begin{list}{}{}}{\end{list}}',
            r'\newcommand{\startlist}{\begin{list}{}{}}',
            r'\renewcommand\stoplist{\end{list}}',
            r'\providecommand*{\startmath}{$}',
            r'\DeclareRobustCommand{\stopmath}{$}',
        ):
            with self.subTest(definition=definition):
                source = r'\begin{document}' + definition + 'Visible text.' + r'\end{document}'
                doc = parse_document(source)
                self.assertIsNone(doc['error'])
                self.assertIn('Visible text.', doc['html'])
                self.assertNotIn('startlist', doc['html'])
                self.assertEqual([leaf['text'] for leaf in doc['leaves'].values()], ['Visible text.'])
                self.assertTrue(any('not expanded' in warning for warning in doc['warnings']))
                self.assertEqual(lint_source(source), [])

    def test_definition_scanner_respects_comments_escapes_and_nested_braces(self):
        source = (r'\newenvironment{wrapped}{\begin{list}{}{\textbf{nested}} \{ \} \%' +
                  '\n% ignored } { \\end{document}\n' +
                  r'}{\end{list}}\begin{document}After definition.\end{document}')
        doc = parse_document(source)
        self.assertIsNone(doc['error'])
        self.assertEqual(lint_source(source), [])
        leaf = next(iter(doc['leaves'].values()))
        self.assertEqual(source[leaf['start']:leaf['end']], 'After definition.')

    def test_incomplete_definitions_and_actual_body_errors_still_fail(self):
        for source in (
            r'\newenvironment{x}{\begin{list}',
            r'\newenvironment{x}{start}',
            r'\newcommand{\example}{unclosed',
            CUSTOM_ENVIRONMENT_SOURCE.replace('Sample experience.', r'\textbf{unclosed'),
            CUSTOM_ENVIRONMENT_SOURCE.replace(r'\end{indentsection}', r'\end{wrong}'),
        ):
            with self.subTest(source=source):
                self.assertTrue(parse_document(source)['error'])
                self.assertEqual(lint_source(source)[0]['severity'], 'error')

    def test_lint_valid_comments_math_verbatim_and_custom_macros(self):
        source = r'\begin{document}\custom{Text} \% $x^2$ \verb|{|' + '\n% unmatched } in a comment\n' + r'\end{document}'
        self.assertEqual(lint_source(source), [])

    def test_lint_reports_braces_environments_and_math(self):
        for source in (r'\textbf{broken', r'\begin{itemize}\end{enumerate}', '$broken'):
            with self.subTest(source=source):
                diagnostics = lint_source(source)
                self.assertEqual(len(diagnostics), 1)
                self.assertEqual(diagnostics[0]['severity'], 'error')
                self.assertTrue(diagnostics[0]['message'])
                self.assertLessEqual(diagnostics[0]['to'], len(source))

    def test_lint_positions_use_utf16_for_non_bmp_characters(self):
        diagnostic, = lint_source('\U0001f600 }')
        self.assertEqual((diagnostic['from'], diagnostic['to']), (3, 4))

    def test_structure_nested_formatting_lists_tables(self):
        doc = parse_document(SOURCE)
        self.assertIsNone(doc["error"])
        self.assertIn('<section class="cv-section">', doc["html"])
        self.assertIn("<strong>", doc["html"])
        self.assertIn("<li>", doc["html"])
        self.assertIn('<table class="cv-table">', doc["html"])
        self.assertNotIn("linewidth", doc["html"])
        self.assertNotIn("documentclass", doc["html"])

    def test_leaf_edit_preserves_all_other_source(self):
        source = SOURCE.replace('Engineer building', '😀 Engineer building')
        doc = parse_document(source)
        key, leaf = next((k,v) for k,v in doc['leaves'].items() if v['text']=='reliable systems')
        result = replace_leaf(source,key,'safe & reliable 50% {systems}')
        self.assertEqual(result, source[:leaf['start']] + r'safe \& reliable 50\% \{systems\}' + source[leaf['end']:])
        self.assertIsNone(parse_document(result)['error'])

    def test_comments_and_hostile_html_are_not_rendered_as_markup(self):
        source = SOURCE.replace('Engineer building', '% hidden-secret\nEngineer <script>alert(1)</script> building')
        html = parse_document(source)['html']
        self.assertNotIn('hidden-secret', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_unbalanced_source_returns_error_without_hanging(self):
        doc = parse_document(r'\begin{document}\textbf{broken')
        self.assertTrue(doc['error'])

    def test_custom_macro_is_explicitly_reported(self):
        doc = parse_document(r'\begin{document}\mystery{Visible}\end{document}')
        self.assertTrue(doc['warnings'])
        self.assertIn('Visible', doc['html'])

    def test_hyperlink_target_is_not_duplicated_in_visible_content(self):
        source = r'\name{Example}\address{\href{mailto:test@example.com}{Email} \\ City}\begin{document}\href{https://example.com}{\textbf{Portfolio}}\end{document}'
        doc = parse_document(source)
        self.assertIsNone(doc['error'])
        self.assertNotIn('mailto:',doc['html'])
        self.assertNotIn('https:',doc['html'])
        self.assertIn('Portfolio',doc['html'])
        self.assertIn(' · ',doc['html'])
