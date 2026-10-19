"""Portable PDF filenames derived from parsed CV headers."""
from html.parser import HTMLParser
import re
import unicodedata
from pylatexenc.latexwalker import LatexWalker, LatexMacroNode, LatexWalkerError
from pylatexenc.latex2text import LatexNodes2Text
from .latex import context, parse_document


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
