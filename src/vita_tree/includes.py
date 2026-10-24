"""Bounded, static navigation of project-local LaTeX files, never TeX expansion.

Literal paths are relative to the project root, as in Vita CV's context builder.
Files stay separate: no concatenation that could move offsets or change TeX input.
"""
import hashlib
import json
import re
from pathlib import PurePosixPath

from pylatexenc.latexwalker import LatexWalker, LatexMacroNode, LatexWalkerError

from .latex import context, DEFINITIONS
from .security import snapshot_excluded

MAX_FILES = 64
MAX_BYTES = 8_000_000
MAX_DEPTH = 16


def discover(entry, read):
    """Return readable files and actionable diagnostics using a guarded reader."""
    files, diagnostics, edges = {}, [], []
    total = 0

    def problem(path, offset, code, message, origin=None):
        if len(diagnostics) < 128:
            diagnostics.append(dict(path=path, sourcePath=origin or path, offset=offset, code=code, message=message))

    def visit(path, stack):
        nonlocal total
        if path in stack:
            problem(stack[-1], 0, 'cycle', f'Include cycle reaches {path}. Break the cycle in Source.')
            return
        if path in files:
            return
        if len(files) >= MAX_FILES or len(stack) >= MAX_DEPTH:
            problem(path, 0, 'limit', 'Include navigation limit reached (64 files / 16 levels). Split the project or open the remaining files externally.')
            return
        try:
            source = read(path)
            if source is None:
                origin = stack[-1] if stack else path
                offset = next((offset for parent,offset,target in reversed(edges) if parent==origin and target==path),0)
                problem(path, offset, 'missing', f'{path} is missing. Restore it or correct the include path in {origin} using Source.', origin)
                return
            size = len(source.encode('utf-8'))
            if size > 2_000_000 or total + size > MAX_BYTES:
                problem(path, 0, 'limit', 'Include navigation exceeds the 2 MB per-file / 8 MB project limit. Open this file externally.')
                return
        except (ValueError, OSError, UnicodeError):
            problem(path, 0, 'unreadable', f'{path} cannot be opened safely. Use a regular UTF-8 file with the exact Git filename and case; resolve merge conflicts externally. Linked, ignored and excluded files are not supported.')
            return
        total += size
        files[path] = source
        try:
            nodes, _, _ = LatexWalker(source, latex_context=context(), tolerant_parsing=False).get_latex_nodes()
        except (ValueError, RecursionError, LatexWalkerError):
            problem(path, 0, 'syntax', f'Cannot discover every include in {path}. Check Source or use Check setup; Structure does not execute TeX.')
            return

        def walk(nodes):
            for node in nodes or []:
                if len(edges) >= 256:
                    problem(path, node.pos, 'limit', 'Include reference limit reached (256). Open remaining files externally.')
                    return
                if isinstance(node, LatexMacroNode):
                    name = node.macroname
                    if name in DEFINITIONS:
                        if re.search(r'\\(?:input|include)\b',source[node.pos:node.pos+node.len]):
                            problem(path,node.pos,'unsupported','Includes inside command/environment definitions are not expanded by file navigation. Edit the definition in Source and open its include externally; PDF and Vita CV retain their own resolution.')
                        continue  # Macro bodies are not executed here.
                    if name in {'input', 'include'}:
                        raw = source[node.pos:node.pos + node.len]
                        match = re.fullmatch(r'\\(?:input|include)\s*\{([^{}]+)\}', raw)
                        target = match[1].strip() if match else ''
                        if not target or re.search(r'[\x00-\x1f\\{}#$%~^&:*?\[\]]', target):
                            problem(path, node.pos, 'unsupported', 'Use a literal braced local include, such as \\input{sections/experience}. Computed paths and unbraced inputs need an external editor.')
                            continue
                        candidate = PurePosixPath(target)
                        if not candidate.suffix:
                            candidate = candidate.with_suffix('.tex')
                        target = candidate.as_posix()
                        if candidate.is_absolute() or '..' in candidate.parts or candidate.suffix.lower() != '.tex' or snapshot_excluded(target):
                            problem(path, node.pos, 'unsafe', 'Include blocked: use a .tex path inside the project without parent traversal or excluded folders. Edit the include command in Source.')
                            continue
                        edges.append((path, node.pos, target))
                        visit(target, (*stack, path))
                        continue
                    if name in {'includeonly', 'import', 'subimport', 'subfile', 'InputIfFileExists'}:
                        problem(path, node.pos, 'unsupported', 'Conditional include selection, import/subfiles packages and computed includes are not evaluated. File views are approximate; use Source and PDF for these constructs.')
                walk(getattr(node, 'nodelist', None))
                for arg in getattr(getattr(node, 'nodeargd', None), 'argnlist', []) or []:
                    if arg is not None:
                        walk([arg])
        try:
            walk(nodes)
        except RecursionError:
            problem(path, 0, 'limit', 'Source nesting exceeds static navigation limits. Use an external editor and Check setup.')

    visit(entry, ())
    revision = hashlib.sha256(json.dumps({'files': files, 'edges': edges, 'diagnostics': diagnostics}, sort_keys=True).encode()).hexdigest()
    return dict(files=files, diagnostics=diagnostics, revision=revision)


def project(workspace, name, *, commit=None, originals=None):
    """Use exactly the safe tracked/nonignored file boundary of project snapshots."""
    from .workspace import read_text, safe_path
    from .server import run_git, git_document
    location = None if commit else workspace.location(name)
    root = location or workspace.repository
    if location and not originals:
        return local(location, workspace.document_path)
    else:
        commit = commit or workspace.head(name)
        names = run_git(root, 'ls-tree', '-r', '-z', commit, strip=False)
        allowed = {line.split('\t', 1)[1] for line in names.split('\0') if line.startswith(('100644 ', '100755 ')) and '\t' in line}
        blocked = {line.split('\t', 1)[1] for line in names.split('\0') if '\t' in line} - allowed
    def read(path):
        if snapshot_excluded(path):
            raise ValueError('Excluded source')
        if originals and path in originals:
            return originals[path]
        if path in blocked:
            raise ValueError('Linked or non-file Git entry')
        if path not in allowed:
            if location and safe_path(root, path).exists():
                raise ValueError('Ignored source')
            return None
        if location:
            target = safe_path(root, path)
            return read_text(target) if target.is_file() else None
        # Read verified regular Git blobs, independently of paths in another
        # branch's checkout. No filesystem include or symlink is followed.
        return git_document(root, commit, path)
    return discover(workspace.document_path, read)


def local(root, entry, overrides=None):
    from .workspace import read_text, safe_path
    from .server import run_git
    names = run_git(root, 'ls-files', '-z', '--stage', '--cached', '--others', '--exclude-standard', strip=False)
    allowed, blocked = set(), set()
    for record in filter(None,names.split('\0')):
        match = re.fullmatch(r'([0-7]{6}) [0-9a-f]+ ([0-3])\t(.+)',record,re.S)
        if match:
            (allowed if match[1] in {'100644','100755'} and match[2]=='0' else blocked).add(match[3])
        else:
            allowed.add(record)
    def read(path):
        target = safe_path(root, path)
        if path in blocked or snapshot_excluded(path) or (path not in allowed and target.exists()):
            raise ValueError('Excluded or ignored source')
        if overrides and path in overrides:
            return overrides[path]
        return read_text(target) if path in allowed and target.is_file() else None
    return discover(entry, read)
