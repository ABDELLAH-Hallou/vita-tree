"""Portable PDF filenames derived from parsed CV headers."""
from html.parser import HTMLParser
import re
import unicodedata
from pylatexenc.latexwalker import LatexWalker, LatexMacroNode, LatexWalkerError
from pylatexenc.latex2text import LatexNodes2Text
from .latex import context, parse_document


class DocumentText(HTMLParser):
    """Copy the supported Structure rendering without inventing new wording."""
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {'br', 'p', 'div', 'section', 'li', 'h1', 'h2', 'h3'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        self.handle_starttag(tag, [])

    def handle_data(self, data):
        self.parts.append(data)


def cover_outputs(source):
    if not source:
        return None
    document = parse_document(source)
    reader = DocumentText()
    if not document['error'] and not document['warnings']:
        reader.feed(document['html'])
    text = '\n'.join(' '.join(line.split()) for line in ''.join(reader.parts).splitlines() if line.strip())
    return dict(text=text or None, characters=len(text), short=None,
                textLimitation=None if text else 'This template needs PDF rendering. Select and copy its text from the PDF.',
                shortLimitation='A short version needs a separate wording and review step. This connection does not provide it; no extra AI request was made.')


class HeaderName(HTMLParser):
    def __init__(self):
        super().__init__()
        self.started = self.done = False
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        if not self.started:
            classes = dict(attrs).get('class', '').split()
            if 'cv-name' in classes or 'cv-center' in classes:
                self.started = True
                self.depth = 1
        elif tag == 'br':
            self.done = True
        else:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.started and not self.done:
            self.depth -= 1
            self.done = self.depth == 0

    def handle_data(self, data):
        if self.started and not self.done:
            self.parts.append(data)


def cv_filename(source, side='current'):
    name = ''
    try:
        nodes, _, _ = LatexWalker(source, latex_context=context(), tolerant_parsing=False).get_latex_nodes()
        for node in nodes:
            if isinstance(node, LatexMacroNode) and node.macroname == 'name':
                args = [arg for arg in node.nodeargd.argnlist if arg is not None]
                if args:
                    name = LatexNodes2Text().nodelist_to_text([args[0]])
                    break
    except (ValueError, RecursionError, LatexWalkerError):
        pass
    if not name:
        reader = HeaderName()
        reader.feed(parse_document(source)['html'])
        name = ''.join(reader.parts).strip()
    name = unicodedata.normalize('NFKC', name)
    name = ''.join(char if char.isalnum() or char in '_-' else '_' for char in name)
    name = re.sub('_+', '_', name).strip('_-')[:80]
    suffix = '-original' if side == 'original' else ''
    return 'cv' + ('-' + name if name else '') + suffix + '.pdf'
