"""Compile repository snapshots with the real TeX engine, without shell escape."""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import threading
import time
import uuid
import zipfile

from .server import run_git
from .workspace import safe_path, atomic_write, ConflictError, read_text
from .fileio import atomic_write_bytes
from .exports import cv_filename


def export_snapshot(repository: Path, commit: str, target: Path, working: Path | None = None):
    target.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(["git", "archive", "--format=zip", commit], cwd=repository,
                             capture_output=True, check=True, timeout=30).stdout
    total = 0
    with zipfile.ZipFile(io.BytesIO(archive)) as files:
        for entry in files.infolist():
            if entry.is_dir() or PurePosixPath(entry.filename).parts[0] in {".git", ".vita"}:
                continue
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symlink assets are not supported in previews")
            total += entry.file_size
            if total > 100_000_000:
                raise ValueError("Repository snapshot exceeds 100 MB")
            path = safe_path(target, entry.filename)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(files.read(entry))
    if working:
        names = run_git(working, "ls-files", "-z", "--cached", "--others", "--exclude-standard", strip=False)
        for name in set(names.split("\0")) - {""}:
            if PurePosixPath(name).parts[0] in {".git", ".vita"}:
                continue
            origin = safe_path(working, name)
            dest = safe_path(target, name)
            if origin.is_file():
                total += origin.stat().st_size
                if total > 200_000_000:
                    raise ValueError("Working snapshot exceeds 200 MB")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(origin, dest)
            elif dest.is_file():
                dest.unlink()


class PDFExistsError(ConflictError):
    def __init__(self, filename, revision):
        super().__init__('A PDF with this name already exists in the worktree. Confirm replacement to continue.')
        self.filename, self.revision = filename, revision


class PDFCompiler:
    def __init__(self, workspace):
        self.workspace = workspace
        self.lock = threading.Lock()
        self.results: dict[str, Path] = {}
        self.previews = {}

    def compile(self, name: str, side: str, engine: str):
        # Keep its worktree available if the user navigates away during export.
        with self.workspace.lock:
            self.workspace._previewing[name] = self.workspace._previewing.get(name, 0) + 1
        started = time.monotonic()
        try:
            result = self._compile(name, side, engine)
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

    def _compile(self, name: str, side: str, engine: str):
        if side not in {"original", "current"}:
            raise ValueError("Invalid preview side")
        if engine not in {"auto", "pdflatex", "xelatex", "lualatex"}:
            raise ValueError("Invalid TeX engine")
        with self.lock:
            snapshot = self.workspace.snapshot(name)
            source = snapshot["original" if side == "original" else "content"]
            if engine == "auto":
                engine = "xelatex" if any(x in source for x in ("fontspec", "polyglossia", "unicode-math")) else "pdflatex"
            executable = shutil.which(engine)
            if not executable:
                raise ValueError(f"{engine} not found. Install MiKTeX or TeX Live, or choose an installed engine.")
            ident = uuid.uuid4().hex
            folder = self.workspace.root / "pdf" / ident
            working = self.workspace.location(name) if side == "current" else None
            export_snapshot(self.workspace.repository, snapshot["commit" if side == "current" else "baseCommit"], folder, working)
            entry = safe_path(folder, self.workspace.document_path)
            atomic_write(entry, source)
            output = folder / "__vt_output"
            output.mkdir()
            version = subprocess.run([executable, "--version"], capture_output=True, timeout=10).stdout.decode(errors="replace")
            flags = ["-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-no-shell-escape"]
            if "MiKTeX" in version:
                flags += ["--disable-installer", "--disable-write18", "--dont-parse-first-line"]
            else:
                flags += ["-no-parse-first-line"]
            env = os.environ.copy()
            env.update(openin_any="p", openout_any="p", TEXMFOUTPUT=str(output))
            command = [executable, *flags, "-output-directory=" + str(output), "./" + self.workspace.document_path]
            log = ""
            try:
                for _ in range(2):
                    process = subprocess.run(command, cwd=folder, env=env, stdin=subprocess.DEVNULL,
                                             capture_output=True, timeout=90)
                    log = process.stdout.decode("utf-8", errors="replace") + process.stderr.decode("utf-8", errors="replace")
                    if process.returncode:
                        raise ValueError("PDF compilation failed.\n" + log[-6000:])
            except subprocess.TimeoutExpired as error:
                raise ValueError("PDF compilation timed out after 90 seconds. Check your LaTeX source and installed packages.") from error
            pdf = output / (entry.stem + ".pdf")
            if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
                raise ValueError("The TeX engine did not produce a PDF")
            self.results[ident] = pdf
            self.previews[ident] = {'branch': name, 'side': side, 'revision': hashlib.sha256(source.encode()).hexdigest(),
                                    'filename': cv_filename(source, side), 'commit': snapshot['commit']}
            warnings = [line.strip() for line in log.splitlines() if any(x in line for x in ("Overfull", "Missing character", "LaTeX Warning"))]
            return {"id": ident, "url": "/api/pdf-file?id=" + ident, "filename": self.previews[ident]['filename'], "engine": engine,
                    "warnings": warnings, "revision": hashlib.sha256(source.encode()).hexdigest()}

    def save(self, ident, branch, existing_revision=None):
        with self.lock, self.workspace.lock:
            preview = self.previews.get(ident)
            pdf = self.results.get(ident)
            if not preview or not pdf or not pdf.is_file():
                raise FileNotFoundError('Preview expired. Compile again before saving the PDF.')
            if preview['branch'] != branch:
                raise ConflictError('This PDF belongs to another branch. Compile this branch before saving.')
            self.workspace.busy(branch)
            snapshot = self.workspace.snapshot(branch)
            if not snapshot['editable']:
                raise ConflictError('Create a local branch before saving a PDF into a worktree.')
            source = snapshot['original'] if preview['side']=='original' else snapshot['content']
            if hashlib.sha256(source.encode()).hexdigest()!=preview['revision'] or snapshot['commit']!=preview['commit']:
                raise ConflictError('The branch changed after PDF compilation. Compile again before saving.')
            location = self.workspace.location(branch, create=True)
            target = safe_path(location, preview['filename'])
            current = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
            if current is not None and existing_revision != current:
                raise PDFExistsError(preview['filename'], current)
            if current is None and existing_revision is not None:
                raise ConflictError('The existing PDF changed after confirmation. Save again.')
            content = pdf.read_bytes()
            if not content.startswith(b'%PDF-'):
                raise ValueError('The retained preview is not a PDF. Compile again.')
            try:
                atomic_write_bytes(target, content)
            except OSError as error:
                self.workspace.diagnostics.error('pdf_failed', error, operation='save_pdf')
                raise
            self.workspace.diagnostics.record('pdf_saved', operation='save_pdf')
            return {'saved': True, 'branch': branch, 'filename': target.name, 'path': str(target)}
