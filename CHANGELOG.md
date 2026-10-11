# Changelog

## 1.0.0 (2026-10-11)

First public package release.

- Browse and search local and remote CV branches in a centered, responsive UI.
- Compare the original CV and edited version side by side, with a source diff.
- Read LaTeX as structured, selectable text. Edit supported text in place or use
  the source editor; saves update the branch's `main.tex` and detect conflicts.
- Create branches in linked Git worktrees and save job descriptions to `job.md`.
- Run VITA analyze and adapt commands, review their reports, and compare the
  generated CV with the version captured before the run.
- Select providers and models discovered across branches, with supported Codex
  reasoning levels.
- Compile and compare real PDFs using the bundled offline PDF.js viewer, with
  selectable text, zoom, and page navigation.
- Choose light, dark, or system appearance.
- Install with pipx or uv; add `vita-tree[ai]` for VITA integration.
- Automate subsequent version updates and release notes with Release Please.
  Releases pass code, browser/PDF, package installation, and privacy checks
  before publishing through TestPyPI to PyPI.

The structured view supports common CV templates; arbitrary LaTeX macros and
exact page layout require the compiled PDF. PDF previews are read-only. AI
commands require configured providers; Git and a TeX installation are separate
system dependencies.
