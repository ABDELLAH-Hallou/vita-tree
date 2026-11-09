"""Versioned synthetic templates and independent source-preservation oracles."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata

from vita_tree import includes
from vita_tree.latex import parse_document, replace_leaf
from support import git, init_repo

CORPUS = Path(__file__).parent/'fixtures/template_matrix'
ENGINES = ('pdflatex', 'xelatex', 'lualatex')


class MatrixFailure(AssertionError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode('utf-8')).hexdigest()


def normalized(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKC', value)
                           if unicodedata.category(c) != 'Cf').split())


class VisibleText(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.feed(value)

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {'div', 'section', 'h1', 'h2', 'p', 'li', 'table', 'td', 'tr', 'br', 'hr'}:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        self.handle_starttag(tag, [])


def load_corpus(root=CORPUS):
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['schemaVersion'] == 1 and manifest['corpusVersion'] == '1.0.0'
    assert manifest['license'] == 'MIT'
    seen = set()
    for fixture in manifest['fixtures']:
        assert re.fullmatch('[a-z][a-z0-9-]+', fixture['id']) and fixture['id'] not in seen
        seen.add(fixture['id'])
        assert re.fullmatch(r'\d+\.\d+\.\d+', fixture['version'])
        assert fixture['entry'] == 'main.tex' and fixture['entry'] in fixture['files']
        assert set(fixture['engines']) <= set(ENGINES)
        assert fixture['structure']['status'] in {'supported', 'approximate', 'unsupported', 'invalid'}
        for name, ref in fixture['files'].items():
            for value in (name, ref['fixture']):
                path = PurePosixPath(value)
                assert not path.is_absolute() and '..' not in path.parts and '\\' not in value
            path = root/ref['fixture']
            assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve())
            assert sha(path.read_bytes()) == ref['sha256'], f"Fixture hash changed: {fixture['id']}/{name}"
    return manifest


def sources(fixture):
    return {name: (CORPUS/ref['fixture']).read_text(encoding='utf-8') for name, ref in fixture['files'].items()}


def hashes(files):
    return {name: sha(value) for name, value in sorted(files.items())}


def structure(fixture, files):
    graph = includes.discover(fixture['entry'], files.get)
    documents = {name: parse_document(value, name) for name, value in graph['files'].items()}
    if fixture['structure']['status'] == 'invalid':
        assert documents[fixture['entry']]['error'], 'Invalid-source control was accepted'
    else:
        if any(doc['error'] for doc in documents.values()):
            raise MatrixFailure('parser_defect', 'Valid template hit a parser defect')
        visible = normalized(' '.join(''.join(VisibleText(doc['html']).parts) for doc in documents.values()))
        for text in fixture['structure']['required']:
            if normalized(text) not in visible:
                raise MatrixFailure('rendering_defect', f'Missing Structure text: {text}')
        for text in fixture['structure']['absent']:
            assert normalized(text) not in visible, f'Unsupported expansion was invented: {text}'
    codes = {item['code'] for item in graph['diagnostics']}
    assert codes == set(fixture['structure']['diagnostics']), graph['diagnostics']
    return documents, graph


def sweep_leaves(documents, files):
    """Exercise every leaf, including decoded escapes, with an independent oracle.

    Only the selected span may change. This sweep is not a claim that every
    hypothetical edit compiles; planned edits also go through Workspace and TeX.
    """
    count = escaped = 0
    for name, document in documents.items():
        for key, leaf in document['leaves'].items():
            source = files[name]
            assert leaf['path'] == name
            assert 0 <= leaf['start'] < leaf['end'] <= len(source)
            candidate = replace_leaf(source, key, 'Matrix & 50% {edit}')
            expected = source[:leaf['start']] + r'Matrix \& 50\% \{edit\}' + source[leaf['end']:]
            assert candidate == expected, f'Edit escaped its source span: {name}:{key}'
            assert parse_document(candidate)['error'] is None
            count += 1
            escaped += source[leaf['start']:leaf['end']].startswith('\\')
    return {'checkedLeaves': count, 'decodedMacroOrSpecialLeaves': escaped}


def make_repository(target, fixture):
    init_repo(target)
    for name, value in sources(fixture).items():
        path = target/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8', newline='\n')
    git(target, 'add', '.')
    git(target, 'commit', '-m', 'Synthetic matrix ' + fixture['id'] + ' ' + fixture['version'])
    return target


def apply_edits(workspace, fixture, branch='master'):
    before = sources(fixture)
    expected = dict(before)
    records = []
    for change in fixture['edits']:
        snapshot = workspace.snapshot(branch)
        file = next(item for item in snapshot['files'] if item['path'] == change['path'])
        candidates = [(key, leaf) for key, leaf in file['document']['leaves'].items() if leaf['text'] == change['find']]
        key, leaf = candidates[change['occurrence']]
        assert leaf['path'] == change['path']
        source = expected[change['path']]
        replacement = source[:leaf['start']] + change['replacementSource'] + source[leaf['end']:]
        result = workspace.save(branch, change['path'], file['revision'], leaf=key, text=change['replacement'],
                                project_revision=snapshot['projectRevision'])
        assert result['content'] == replacement, f"Source edit changed syntax outside {change['path']}:{key}"
        expected[change['path']] = replacement
        location = workspace.location(branch)
        actual = {name: (location/name).read_bytes() for name in expected}
        assert actual == {name: value.encode('utf-8') for name, value in expected.items()}, 'Untouched source file changed'
        assert parse_document(replacement)['error'] is None
        records.append({'path': change['path'], 'start': leaf['start'], 'end': leaf['end'], 'kind': change['kind'],
                        'before': sha(source), 'after': sha(replacement), 'untouchedPrefix': sha(source[:leaf['start']]),
                        'untouchedSuffix': sha(source[leaf['end']:])})
    return expected, records


def after_expectations(fixture):
    """Update literal test anchors; no expectations are inferred from PDF output."""
    result = json.loads(json.dumps(fixture))
    for change in fixture['edits']:
        for area in ('structure', 'pdf'):
            result[area]['required'] = [text.replace(change['find'], change['replacement'])
                                        for text in result[area]['required']]
        result['pdf']['perPage'] = {page: [text.replace(change['find'], change['replacement']) for text in texts]
                                    for page, texts in result['pdf']['perPage'].items()}
        result['pdf']['associations'] = [[text.replace(change['find'], change['replacement']) for text in pair]
                                         for pair in result['pdf']['associations']]
    return result
