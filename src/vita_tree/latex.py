"""Syntax-aware, source-mapped reading view. TeX remains the layout authority."""
from __future__ import annotations

import html
import re

from pylatexenc.latexwalker import (
    LatexWalker, LatexCharsNode, LatexMacroNode, LatexGroupNode,
    LatexEnvironmentNode, LatexCommentNode, LatexMathNode, LatexSpecialsNode,
    get_default_latex_context_db, LatexWalkerError, LatexWalkerParseError,
    LatexWalkerEndOfStream,
)
from pylatexenc.macrospec import MacroSpec, EnvironmentSpec, MacroStandardArgsParser, ParsedMacroArgs
from pylatexenc.latex2text import LatexNodes2Text


# Definition bodies are token lists, not independently balanced environments or
# math expressions. In particular, newenvironment splits begin/end across two
# arguments. Read balanced braces without expanding or interpreting those tokens.
DEFINITIONS = {"newenvironment": 2, "renewenvironment": 2, "provideenvironment": 2,
               "newcommand": 1, "renewcommand": 1, "providecommand": 1,
               "DeclareRobustCommand": 1}


class DefinitionArgsParser(MacroStandardArgsParser):
    def __init__(self, bodies):
        super().__init__("*{[[")
        self.bodies = bodies

    def parse_args(self, w, pos, parsing_state=None):
        prefix, _, length = super().parse_args(w, pos, parsing_state=parsing_state)
        end = pos + length
        args = list(prefix.argnlist)
        for _ in range(self.bodies):
            start = end
            depth = 0
            try:
                while True:
                    token = w.get_token(end, environments=False, parsing_state=parsing_state)
                    end = token.pos + token.len
                    if token.tok == 'comment':
                        continue
                    if token.tok == 'brace_open':
                        depth += 1
                    elif token.tok == 'brace_close':
                        depth -= 1
                        if depth < 0:
                            raise LatexWalkerParseError('Unexpected closing brace in definition', s=w.s, pos=token.pos)
                    if depth == 0:
                        break
            except LatexWalkerEndOfStream:
                raise LatexWalkerParseError('Incomplete command or environment definition', s=w.s, pos=start) from None
            # An opaque node retains the exact source range, including comments.
            # It is never rendered or exposed as an editable Structure leaf.
            args.append(w.make_node(LatexGroupNode, pos=start, len=end-start,
                                    nodelist=[], delimiters=('{', '}'), parsing_state=parsing_state))
        return ParsedMacroArgs(argspec=self.argspec + '{' * self.bodies, argnlist=args), pos, end-pos


def context():
    db = get_default_latex_context_db()
    db.add_context_category("vita", macros=[
        *(MacroSpec(name, DefinitionArgsParser(bodies)) for name, bodies in DEFINITIONS.items()),
        MacroSpec("name", "{"), MacroSpec("address", "{"),
        MacroSpec("href", "[{{"), MacroSpec("url", "{"),
        MacroSpec("resumeItem", "{"), MacroSpec("resumeSubheading", "{{{{"),
        MacroSpec("resumeProjectHeading", "{{"),
        MacroSpec("resumeSubItem", "{{"),
        MacroSpec("resumeSubHeadingListStart", ""), MacroSpec("resumeSubHeadingListEnd", ""),
        MacroSpec("resumeItemListStart", ""), MacroSpec("resumeItemListEnd", ""),
    ], environments=[EnvironmentSpec("rSection", "{"),
                     EnvironmentSpec("rSubsection", "{{{{"),
                     EnvironmentSpec("tabularx", "{{")], prepend=True)
    return db


ESCAPES = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
           "%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_",
           "$": r"\$", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def escape_text(text: str) -> str:
    return "".join(ESCAPES.get(char, char) for char in text)


class Renderer:
    def __init__(self, source: str):
        self.source = source
        self.warnings: set[str] = set()
        self.leaves: dict[str, dict] = {}
        self.converter = LatexNodes2Text()

    def leaf(self, node, text=None):
        raw = self.source[node.pos:node.pos + node.len]
        if text is None:
            text = raw
        if not text.strip():
            return "<br><br>" if "\n\n" in text.replace("\r", "") else " "
        key = str(node.pos)
        self.leaves[key] = {"start": node.pos, "end": node.pos + node.len, "text": text}
        return f'<span data-leaf="{key}">{html.escape(text)}</span>'

    def args(self, node):
        return [a for a in getattr(getattr(node, "nodeargd", None), "argnlist", []) if a is not None]

    def sequence(self, nodes):
        result = []
        # Font declarations apply to the rest of their enclosing group.
        close = []
        for node in nodes or []:
            if isinstance(node, LatexMacroNode) and node.macroname in {"bf", "bfseries", "em", "itshape", "it"}:
                tag = "strong" if node.macroname in {"bf", "bfseries"} else "em"
                result.append(f"<{tag}>")
                close.insert(0, f"</{tag}>")
            else:
                result.append(self.node(node))
        return "".join(result + close)

    def table(self, nodes):
        rows, cells, cell = [], [], []
        def finish_cell():
            cells.append("<td>" + self.sequence(cell) + "</td>")
            cell.clear()
        def finish_row():
            finish_cell()
            rows.append("<tr>" + "".join(cells) + "</tr>")
            cells.clear()
        for node in nodes:
            if isinstance(node, LatexSpecialsNode) and node.specials_chars == "&":
                finish_cell()
            elif isinstance(node, LatexMacroNode) and node.macroname in {"\\", "tabularnewline"}:
                finish_row()
            else:
                cell.append(node)
        if any(self.source[n.pos:n.pos+n.len].strip() for n in cell):
            finish_row()
        return '<table class="cv-table"><tbody>' + "".join(rows) + "</tbody></table>"

    def listing(self, nodes, ordered=False):
        items, current = [], []
        for node in nodes:
            if isinstance(node, LatexMacroNode) and node.macroname == "item":
                if current:
                    items.append(self.sequence(current))
                current = []
            else:
                current.append(node)
        if current:
            items.append(self.sequence(current))
        items = [x for x in items if re.sub(r"<[^>]*>", "", x).strip()]
        tag = "ol" if ordered else "ul"
        return f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>"

    def node(self, node):
        if isinstance(node, LatexCommentNode):
            return ""
        if isinstance(node, LatexCharsNode):
            # TeX dimension assignments are layout, not visible prose.
            if re.fullmatch(r"\s*-?[\d.]+(?:pt|em|ex|cm|mm|in)\s*", node.chars):
                return ""
            return self.leaf(node)
        if isinstance(node, LatexGroupNode):
            return self.sequence(node.nodelist)
        if isinstance(node, LatexMathNode):
            self.warnings.add("Math is shown as text in Structure; use PDF for typesetting.")
            return '<span class="math">' + html.escape(self.converter.node_to_text(node)) + '</span>'
        if isinstance(node, LatexSpecialsNode):
            return self.leaf(node, self.converter.node_to_text(node))
        if isinstance(node, LatexEnvironmentNode):
            name, args = node.environmentname, self.args(node)
            if name in {"tabular", "tabular*", "tabularx"}:
                return self.table(node.nodelist)
            if name in {"itemize", "enumerate"}:
                return self.listing(node.nodelist, name == "enumerate")
            body = self.sequence(node.nodelist)
            if name == "rSection":
                return '<section class="cv-section"><h2>' + self.node(args[0]) + '</h2>' + body + '</section>'
            if name == "rSubsection":
                return '<div class="cv-entry">' + ' · '.join(self.node(a) for a in args) + body + '</div>'
            if name == "center":
                return '<div class="cv-center">' + body + '</div>'
            if name not in {"document", "flushleft", "flushright", "minipage"}:
                self.warnings.add(f"Environment {name}: approximate layout in Structure.")
            return body
        if isinstance(node, LatexMacroNode):
            name, args = node.macroname, self.args(node)
            if name in DEFINITIONS:
                self.warnings.add("Custom definitions are preserved, not expanded in Structure. Use PDF for exact rendering.")
                return ""
            value = lambda: self.node(args[-1]) if args else ""
            if name in {"name", "title"}:
                return '<h1 class="cv-name">' + value() + '</h1>'
            if name == "address":
                return '<div class="cv-contact">' + value().replace('<br>', ' · ') + '</div>'
            if name in {"section", "subsection", "subsubsection"}:
                return '<h2>' + value() + '</h2>'
            tags = {"textbf": "strong", "textit": "em", "emph": "em", "underline": "u", "texttt": "code"}
            if name in tags:
                return f'<{tags[name]}>' + value() + f'</{tags[name]}>'
            if name == "href":
                return value()  # selectable labels; no accidental navigation while editing
            if name in {"url", "textnormal", "textrm", "textsf", "mbox", "MakeUppercase"}:
                return value()
            if name in {"\\", "newline", "linebreak", "par"}:
                return "<br>"
            if name in {"pagebreak", "newpage", "clearpage"}:
                return '<hr class="cv-pagebreak" aria-label="Page break">'
            if name == "hfill":
                return '<span class="cv-gap"> </span>'
            if name in {"quad", "qquad", ",", ";", " ", "enspace"}:
                return "&ensp;"
            if name in {"resumeItem", "resumeSubItem"}:
                return '<div class="cv-bullet">• ' + ' '.join(self.node(a) for a in args) + '</div>'
            if name in {"resumeSubheading", "resumeProjectHeading"}:
                return '<div class="cv-entry">' + ' · '.join(self.node(a) for a in args) + '</div>'
            if name in {"input", "include"}:
                self.warnings.add("Included files render in PDF; edit them in your source editor.")
                return '<div class="unsupported">Included file: ' + value() + '</div>'
            if name in {"vspace", "hspace", "setlength", "addtolength", "itemsep", "noindent", "smallskip", "medskip", "bigskip", "small", "footnotesize", "scriptsize", "tiny", "large", "Large", "LARGE", "huge", "Huge", "normalsize", "centering", "raggedright", "hline", "maketitle", "label", "pagestyle", "thispagestyle"} or name.startswith("resumeItemList") or name.startswith("resumeSubHeadingList"):
                return ""
            if name in {"%", "&", "#", "_", "$", "{", "}", "textbackslash", "textasciitilde", "textasciicircum", "LaTeX", "TeX", "textbullet", "textendash", "textemdash", "'", '`', '"', "^", "~", "c", "ss"}:
                return self.leaf(node, self.converter.node_to_text(node))
            self.warnings.add(f"\\{name}: use PDF for exact rendering; source is preserved.")
            return ''.join(self.node(a) for a in args)
        return ""


def lint_source(source: str) -> list[dict]:
    """Report the first syntax problem; ranges use browser UTF-16 offsets.

    Definition bodies are balanced token lists, not expanded document content.
    This does not expand arbitrary macros or validate installed TeX packages.
    """
    try:
        LatexWalker(source, latex_context=context(), tolerant_parsing=False).get_latex_nodes()
    except (ValueError, RecursionError, LatexWalkerError) as error:
        pos = max(0, min(getattr(error, "pos", 0) or 0, len(source)))
        offset = len(source[:pos].encode("utf-16-le", errors="surrogatepass")) // 2
        end = offset + len(source[pos:pos + 1].encode("utf-16-le", errors="surrogatepass")) // 2
        message = getattr(error, "msg", str(error))
        severity = "error"
        if isinstance(error, RecursionError):
            message = "Source nesting exceeds the syntax check limit. Compile the PDF to validate it."
            severity = "warning"
        return [{"from": offset, "to": end, "severity": severity,
                 "message": message, "source": "LaTeX syntax"}]
    return []


def parse_document(source: str) -> dict:
    renderer = Renderer(source)
    try:
        nodes, _, _ = LatexWalker(source, latex_context=context(), tolerant_parsing=False).get_latex_nodes()
        doc = next((n for n in nodes if isinstance(n, LatexEnvironmentNode) and n.environmentname == "document"), None)
        header = [n for n in nodes if isinstance(n, LatexMacroNode) and n.macroname in {"name", "address", "title"}]
        result = renderer.sequence(header) + renderer.sequence(doc.nodelist if doc else nodes)
        return {"html": result, "leaves": renderer.leaves, "warnings": sorted(renderer.warnings), "error": None}
    except (ValueError, RecursionError, LatexWalkerError) as error:
        return {"html": "", "leaves": {}, "warnings": [], "error": f"Cannot parse this LaTeX: {error}"}


def replace_leaf(source: str, key: str, text: str) -> str:
    leaf = parse_document(source)["leaves"].get(str(key))
    if leaf is None:
        raise ValueError("This text has changed. Reload the document before editing.")
    return source[:leaf["start"]] + escape_text(text) + source[leaf["end"]:]
