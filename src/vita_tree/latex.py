"""Syntax-aware, source-mapped reading view. TeX remains the layout authority."""
from __future__ import annotations

import html
import re

from pylatexenc.latexwalker import (
    LatexWalker, LatexCharsNode, LatexMacroNode, LatexGroupNode,
    LatexEnvironmentNode, LatexCommentNode, LatexMathNode, LatexSpecialsNode,
    get_default_latex_context_db, LatexWalkerError,
)
from pylatexenc.macrospec import MacroSpec, EnvironmentSpec
from pylatexenc.latex2text import LatexNodes2Text


def context():
    db = get_default_latex_context_db()
    db.add_context_category("vita", macros=[
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
