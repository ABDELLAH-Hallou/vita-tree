# Changelog

## [1.4.1](https://github.com/ABDELLAH-Hallou/vita-tree/compare/v1.4.0...v1.4.1) (2026-10-17)


### Bug Fixes

* simplify header and use an icon theme toggle ([bc5417f](https://github.com/ABDELLAH-Hallou/vita-tree/commit/bc5417febd17e39d1f0163474beb4965cc07b4fb))
* simplify header and use an icon theme toggle ([7817058](https://github.com/ABDELLAH-Hallou/vita-tree/commit/78170589550033c46d048ac1aa8172899e3e8444))

## [1.4.0](https://github.com/ABDELLAH-Hallou/vita-tree/compare/v1.3.0...v1.4.0) (2026-10-17)


### Features

* add workflow graph and independent AI step controls ([5a0f307](https://github.com/ABDELLAH-Hallou/vita-tree/commit/5a0f307aa54db7965bd30713224ef41ae755ee5d))
* add workflow graph and independent AI step controls ([d566dca](https://github.com/ABDELLAH-Hallou/vita-tree/commit/d566dca0ffcde5f5965945d157e03b43b0e7d1e6))

## [1.3.0](https://github.com/ABDELLAH-Hallou/vita-tree/compare/v1.2.0...v1.3.0) (2026-10-14)


### Features

* run independent AI sessions and release clean worktrees ([8e506ab](https://github.com/ABDELLAH-Hallou/vita-tree/commit/8e506aba41de429ac031a23d4a1db99381f3d7f4))
* run independent AI sessions and release clean worktrees ([179221b](https://github.com/ABDELLAH-Hallou/vita-tree/commit/179221bcf2950fea0457090355c884a1fe656b48))

## [1.2.0](https://github.com/ABDELLAH-Hallou/vita-tree/compare/v1.1.0...v1.2.0) (2026-10-12)


### Features

* **commit:** add a button to commit and push ([90c68fe](https://github.com/ABDELLAH-Hallou/vita-tree/commit/90c68fec27d4bbbbac6bd53e2339f22167be2145))
* **commit:** add a button to commit and push ([30fd515](https://github.com/ABDELLAH-Hallou/vita-tree/commit/30fd5159761ce26548b2f8d1a639532240fa7853))

## [1.1.0](https://github.com/ABDELLAH-Hallou/vita-tree/compare/v1.0.0...v1.1.0) (2026-10-11)


### Features

* add LaTeX syntax highlighting and linting ([4b702dc](https://github.com/ABDELLAH-Hallou/vita-tree/commit/4b702dce3f77b79016260dd5859c4dce390a6f43))
* add LaTeX syntax highlighting and linting ([5fb51a8](https://github.com/ABDELLAH-Hallou/vita-tree/commit/5fb51a8bee46e5fab6d681ed6271253b0c2a3370))


### Bug Fixes

* recognize GitHub merge service email in privacy checks ([613b3df](https://github.com/ABDELLAH-Hallou/vita-tree/commit/613b3dfa843a4616d5894e3c8e674c82386a4594))
* restore project author attribution ([c364d68](https://github.com/ABDELLAH-Hallou/vita-tree/commit/c364d68ef3007b92b8a1efbd1925f4cbae276353))

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
