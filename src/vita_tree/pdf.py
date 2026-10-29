"""Compile repository snapshots with the real TeX engine, without shell escape."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
import tempfile

from .server import run_git
from .workspace import safe_path, atomic_write, ConflictError, read_text
from .fileio import atomic_write_bytes
from .exports import cv_filename
from .security import snapshot_excluded, compiler_environment, engine_executable
from .processes import run_owned


class CompilationError(ValueError):
    def __init__(self, category, message):
        super().__init__(message)
        self.category = category


def export_snapshot(repository: Path, commit: str, target: Path, working: Path | None = None):
    target.mkdir(parents=True, exist_ok=True)
    total = 0
    # Spool compressed bytes to disk, rather than allocating an unbounded archive
    # in memory before checking its expanded entries. Disk/OS quotas remain external.
    with tempfile.TemporaryFile() as archive:
        subprocess.run(["git", "archive", "--format=zip", commit], cwd=repository,
                       stdout=archive, stderr=subprocess.PIPE, check=True, timeout=30)
        if archive.tell() > 100_000_000:
            raise ValueError('The compressed CV snapshot exceeds 100 MB')
        archive.seek(0)
        _extract_snapshot(archive, target)
    if working:
        names = run_git(working, "ls-files", "-z", "--cached", "--others", "--exclude-standard", strip=False)
        names = set(names.split("\0")) - {""}
        if len(names) > 10000:
            raise ValueError('The application snapshot exceeds the 10000-file limit')
        for name in names:
            if snapshot_excluded(name):
                continue
            origin = safe_path(working, name)
            dest = safe_path(target, name)
            if origin.is_file():
                total += origin.stat().st_size
                if total > 100_000_000:
                    raise ValueError("The application files are too large to create a PDF preview (maximum 100 MB)")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origin, dest)
            elif dest.is_file():
                dest.unlink()


def _extract_snapshot(archive, target):
    total = 0
    with zipfile.ZipFile(archive) as files:
        if len(files.infolist()) > 10000:
            raise ValueError('The CV snapshot exceeds the 10000-file limit')
        for entry in files.infolist():
            if entry.is_dir() or snapshot_excluded(entry.filename):
                continue
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("PDF previews do not support linked files. Use regular files in the application folder.")
            total += entry.file_size
            if total > 100_000_000:
                raise ValueError("The CV collection is too large to create a PDF preview (maximum 100 MB)")
            path = safe_path(target, entry.filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(files.read(entry))


def compile_document(folder: Path, document_path: str, engine='auto', output=None):
    """Compile a saved isolated document; never enable shell escape or installers."""
    if engine not in {'auto', 'pdflatex', 'xelatex', 'lualatex'}:
        raise ValueError('Choose a supported PDF engine in Advanced PDF settings')
    entry = safe_path(folder, document_path)
    source = read_text(entry)
    if not source.strip():
        raise FileNotFoundError('No saved LaTeX document is available to compile.')
    if engine == 'auto':
        engine = 'xelatex' if any(x in source for x in ('fontspec','polyglossia','unicode-math')) else 'pdflatex'
    # LuaTeX does not implement pdfTeX's first-line suppression switch (MiKTeX
    # rejects it). Refuse format/option directives instead of silently dropping
    # the protection or modifying the captured document.
    if engine == 'lualatex' and source.splitlines()[0].lstrip('\ufeff \t').startswith('%&'):
        raise ValueError('LuaLaTeX previews do not support %& first-line directives. Remove the directive and select the engine in PDF settings.')
    output = output or folder / '__vt_output'
    if output.is_symlink() or getattr(output,'is_junction',lambda:False)():
        raise ValueError('Linked compiler output folders are not supported')
    output.mkdir(parents=True, exist_ok=True)
    # TeX engines may need existing output subdirectories for include .aux
    # files. Create only bounded, verified local source paths, never TeX paths
    # computed by macros or paths supplied by a symlink.
    from .includes import discover
    def included_source(name):
        path = safe_path(folder, name)
        return read_text(path) if path.is_file() else None
    for name in discover(document_path, included_source)['files']:
        safe_path(output, name).parent.mkdir(parents=True, exist_ok=True)
    env = compiler_environment(folder, output)
    try:
        executable = engine_executable(engine, folder, env)
    except ValueError as error:
        raise CompilationError('engine_missing', str(error)) from error
    version = subprocess.run([executable, "--version"], env=env, cwd=folder,
                             stdin=subprocess.DEVNULL, capture_output=True, timeout=10).stdout.decode(errors="replace")
    flags = ["-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-no-shell-escape"]
    if "MiKTeX" in version:
        flags += ["--disable-installer", "--disable-write18"]
        if engine != 'lualatex':
            flags += ["--dont-parse-first-line"]
    elif engine != 'lualatex':
        flags += ["-no-parse-first-line"]
    command = [executable, *flags, "-output-directory=" + str(output), "./" + document_path]
    log = ""
    try:
        for _ in range(2):
            with tempfile.TemporaryFile() as captured:
                process = run_owned(command, cwd=folder, env=env, stdin=subprocess.DEVNULL,
                                         stdout=captured, stderr=subprocess.STDOUT, timeout=90)
                captured.seek(0,2)
                if captured.tell() > 2_000_000:
                    raise ValueError('PDF tool output exceeded the 2 MB diagnostic limit.')
                captured.seek(0)
                log = captured.read(2_000_000).decode('utf-8',errors='replace')
            if process.returncode:
                raise ValueError("Couldn’t create the PDF.\n" + log[-6000:])
    except subprocess.TimeoutExpired as error:
        raise CompilationError('compile_timeout', "Creating the PDF took longer than 90 seconds. Check the source formatting and installed PDF tools.") from error
    pdf = safe_path(output, entry.stem + '.pdf')
    if not pdf.is_file() or pdf.stat().st_size > 32_000_000:
        raise ValueError('The PDF tool did not produce a document within the 32 MB limit')
    with pdf.open('rb') as document:
        valid = document.read(5) == b'%PDF-'
    if not valid:
        raise ValueError('The PDF tool did not produce a document')
    warnings = [line.strip() for line in log.splitlines() if any(x in line for x in ('Overfull','Missing character','LaTeX Warning'))]
    return {'pdf': pdf, 'engine': engine, 'warnings': warnings}


class PDFExistsError(ConflictError):
    def __init__(self, filename, revision):
        super().__init__('A PDF with this name already exists in the application folder. Confirm replacement to continue.')
        self.filename, self.revision = filename, revision


class PDFCompiler:
    def __init__(self, workspace):
        self.workspace = workspace
        self.lock = threading.Lock()
        self.results: dict[str, Path] = {}
        self.previews = {}

    def compile(self, name: str, side: str, engine: str, document="cv", run_id=None):
        # Keep its worktree available if the user navigates away during export.
        with self.workspace.lock:
            self.workspace._previewing[name] = self.workspace._previewing.get(name, 0) + 1
        started = time.monotonic()
        try:
            with self.workspace.processes.scope():
                result = self._compile(name, side, engine, document, run_id)
            self.workspace.diagnostics.record('pdf_compiled', operation='compile_pdf', duration_ms=(time.monotonic()-started)*1000)
            return result
        except Exception as error:
            self.workspace.diagnostics.error('pdf_failed', error, operation='compile_pdf')
            raise
        finally:
            with self.workspace.lock:
                count = self.workspace._previewing[name] - 1
                if count:
                    self.workspace._previewing[name] = count
                else:
                    self.workspace._previewing.pop(name)
                    if name in self.workspace._release_requested:
                        self.workspace.release_worktree(name)

    def _compile(self, name: str, side: str, engine: str, document='cv', run_id=None):
        if engine not in {'auto','pdflatex','xelatex','lualatex'}:
            raise ValueError('Choose a supported PDF engine in Advanced PDF settings')
        if side not in {'original','current'} or document not in {'cv','cover'}:
            raise ValueError('Choose a supported PDF preview')
        if document == 'cover' and side != 'current' or run_id is not None and document != 'cover':
            raise ValueError('Cover letters have one generated version')
        with self.lock:
            snapshot = self.workspace.snapshot(name)
            source = snapshot['cover'] if document == 'cover' else snapshot['original' if side == 'original' else 'content']
            filename = ('cover-letter' + cv_filename(snapshot['content'])[2:]) if document == 'cover' else cv_filename(source, side)
            if run_id is not None:
                run = self.workspace.get_job(run_id)
                if run['branch'] != name:
                    raise ConflictError('This cover-letter PDF belongs to another application.')
                built = self.workspace.cover_pdf_result(run_id)
                if not built:
                    raise ValueError('This preparation has no cover-letter PDF. Check its status or create a preview from the saved cover letter.')
                source = read_text(safe_path(self.workspace.root / 'runs' / run_id, 'cover-letter.tex'))
                filename = 'cover-letter' + cv_filename(read_text(safe_path(self.workspace.root / 'runs' / run_id, 'main.tex')))[2:]
            else:
                if not source.strip():
                    raise ValueError('No cover letter has been saved for this application. Start the Cover letter step first.')
                ident = uuid.uuid4().hex
                folder = self.workspace.root / 'pdf' / ident
                working = self.workspace.location(name) if side == 'current' else None
                export_snapshot(self.workspace.repository, snapshot['commit' if side == 'current' else 'baseCommit'], folder, working)
                if side == 'original' and document == 'cv':
                    for file in snapshot['files']:
                        target = safe_path(folder, file['path'])
                        if file['originalExists']:
                            atomic_write(target, file['original'])
                        else:
                            target.unlink(missing_ok=True)
                entry = 'cover-letter.tex' if document == 'cover' else self.workspace.document_path
                atomic_write(safe_path(folder, entry), source)
                if document == 'cv':
                    for file in snapshot['files']:
                        exists = file['originalExists'] if side == 'original' else file['exists']
                        expected = file['original' if side == 'original' else 'content'] if exists else None
                        path = safe_path(folder, file['path'])
                        # A current-only file can remain as an unused asset in the
                        # exported baseline. Only captured reachable inputs matter.
                        if exists and (not path.is_file() or read_text(path) != expected):
                            raise ConflictError('Included files changed while capturing this PDF. Reload and create a new preview.')
                built = compile_document(folder, entry, engine)
                if self.workspace.snapshot(name)['projectRevision'] != snapshot['projectRevision']:
                    raise ConflictError('The CV or included files changed during compilation. Create a new preview.')
            ident = uuid.uuid4().hex
            self.results[ident] = built['pdf']
            self.previews[ident] = {'branch': name, 'side': side, 'document': document,
                'revision': hashlib.sha256(source.encode()).hexdigest(), 'filename': filename, 'commit': snapshot['commit'],
                'projectRevision': snapshot['projectRevision']}
            return {'id': ident, 'url': '/api/pdf-file?id=' + ident, 'filename': filename,
                    'engine': built['engine'], 'warnings': built['warnings'], 'revision': self.previews[ident]['revision']}

    def save(self, ident, branch, existing_revision=None):
        with self.lock, self.workspace.lock:
            preview = self.previews.get(ident)
            pdf = self.results.get(ident)
            if not preview or not pdf or not pdf.is_file():
                raise FileNotFoundError('This preview has expired. Create it again before saving the PDF.')
            if preview['branch'] != branch:
                raise ConflictError('This PDF belongs to another application. Create a preview for this application before saving.')
            self.workspace.busy(branch)
            snapshot = self.workspace.snapshot(branch)
            if not snapshot['editable']:
                raise ConflictError('Create an editable application before saving its PDF.')
            source = snapshot['cover'] if preview.get('document') == 'cover' else snapshot['original'] if preview['side']=='original' else snapshot['content']
            if hashlib.sha256(source.encode()).hexdigest()!=preview['revision'] or snapshot['commit']!=preview['commit'] or snapshot['projectRevision']!=preview['projectRevision']:
                raise ConflictError('The application changed after this PDF was created. Create a new preview before saving.')
            location = self.workspace.location(branch, create=True)
            target = safe_path(location, preview['filename'])
            current = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
            if current is not None and existing_revision != current:
                raise PDFExistsError(preview['filename'], current)
            if current is None and existing_revision is not None:
                raise ConflictError('The existing PDF changed after confirmation. Save again.')
            content = pdf.read_bytes()
            if not content.startswith(b'%PDF-'):
                raise ValueError('This preview is not a valid PDF. Create it again.')
            try:
                atomic_write_bytes(target, content)
            except OSError as error:
                self.workspace.diagnostics.error('pdf_failed', error, operation='save_pdf')
                raise
            self.workspace.diagnostics.record('pdf_saved', operation='save_pdf')
            return {'saved': True, 'branch': branch, 'filename': target.name, 'path': str(target)}
