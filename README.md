# Vita Tree

Browse, edit, and adapt LaTeX CVs across Git branches. Compare versions side by side, keep a job description with each branch, and preview the compiled PDFs.

## Install and run

Requires **Python 3.10+**, **Git**, and a Git repository containing a LaTeX CV.
Install the CLI in an isolated environment with pipx:

```sh
pipx install "vita-tree[ai]"
vt run /path/to/your/cv-repository
```

Or use uv:

```sh
uv tool install "vita-tree[ai]"
vt run /path/to/your/cv-repository
```

`vita-tree` is also available as an alias for `vt`; `python -m vita_tree` works
inside the environment where the package is installed. Use `pipx upgrade vita-tree` or `uv tool upgrade vita-tree` to update a published installation.

The optional `[ai]` extra installs the compatible VITA CLI and enables provider
and reasoning integration automatically. Install plain `vita-tree` if you only
need browsing, editing, and PDF previews. AI calls still require your VITA
configuration and provider credentials or Codex login. See
[VITA](https://github.com/ABDELLAH-Hallou/vita-cv) for CV initialization and provider
setup. VITA can also be used from a local checkout with `--vita-source`.

**PDF previews:** install MiKTeX (Windows) or TeX Live (Linux/macOS), including your
template's packages and fonts, and put its executables on PATH. Git and TeX are
system requirements and are not installed by pip. Browser assets, PDF.js, fonts,
and character maps are bundled; no Node installation or CDN is needed at runtime.

To run from source:

```sh
git clone https://github.com/ABDELLAH-Hallou/vita-tree.git
cd vita-tree
python -m pip install -e ".[ai]"
vt run /path/to/your/cv-repository
```

On Windows use a path such as `vt run "C:\path\to\cv-repository"`.

```text
vt run [REPOSITORY] [--port 8765] [--file main.tex] [--no-browser] [--vita-source PATH]
```

The server accepts localhost connections only. It can modify the chosen repository, so do not expose it through a network proxy. Compile only trusted local LaTeX: disabling shell escape is not an operating-system sandbox.

## Workflow

The LaTeX tab includes syntax colors, line numbers, bracket matching, undo/redo,
and search (Ctrl/Cmd+F). Live syntax checks underline parser errors; click the
status below the editor for details. Checks report the first syntax error and
do not validate custom macro expansion or installed packages; compile the PDF
for full validation. Unsaved and temporarily invalid source can still be saved.
The editor is bundled locally and follows the selected light/dark theme.

1. Open a branch. Existing checked-out branches display working files, including uncommitted `main.tex`, `job.md`, and `.vita/results/*.md`. Other branches display committed files.
2. Choose **Branch from this**, name the branch, and paste the job description. Vita Tree creates a Git linked worktree below the repository's Git common directory at `vita-tree/worktrees/`. The original checkout is not switched. The viewed main document and the new `job.md` are written to the new worktree.
3. In **Structure**, select/copy text normally, or double-click text in the new version to edit it. The parser maps text to its exact source range and escapes LaTeX special characters. **LaTeX** provides the full editable source for other changes. Save writes the branch worktree's real file.
4. In **Job & AI**, save `job.md`, select a provider, model, reasoning level, and language, and run **Analyze & adapt**. The app runs `vita analyze --auto`, then `vita adapt --auto`, in a separate snapshot. It checks the reports and a changed, parseable `main.tex` before applying output. The exact pre-run CV becomes the original comparison. Failed and conflicting results remain in the run folder shown in the error.
5. Review `.vita/results/analyze.md`, `.vita/results/adapt.md`, the source diff, and both PDFs. The PDF view uses the actual TeX output with PDF.js canvas rendering and its text layer. Choose a different engine if your template requires it.
6. Use **Commit & push** to review the destination, commit message, and included files, then publish only the selected branch. A failed push leaves the commit safely in the worktree and offers a push-only retry.

**Save changes** remains local and uncommitted. **Commit & push** includes only the displayed main document, `job.md`, and reviewed VITA Markdown reports; unrelated working-tree changes are reported and excluded. It never force-pushes or publishes other branches. Worktrees containing local changes persist across server restarts; leaving a clean worktree releases its branch for CLI checkout.

For existing branches without a recorded baseline, Original means that branch's committed CV. New branches retain the viewed base CV; AI runs retain the pre-run CV. Reload imports changes made by a terminal/editor. Saving with a stale revision returns a conflict and preserves the user's editor text.

VITA's local `config.json`, `extensions.json`, and `cv.yaml` are supplied to isolated AI runs. API-key/token values from `.vita/.env` are passed in child-process memory. Existing reports are branch-local. The UI does not expose credentials or raw provider logs.

Provider/model dropdowns scan `.vita/extensions.json` on every local and remote branch ref and in linked working trees. Duplicate choices are combined; hovering over Model lists their sources. Reload rescans the repository. Choosing a model from another branch overrides only the isolated run, leaving your branch configuration intact. These are discovered configurations, not a guarantee that historical model names remain available to your account.

**Background AI runs:** use one `vt run` server and port for all branches. Every Analyze & adapt action starts an independent background process immediately, with its own provider, model, reasoning, language, and isolated files. Codex runs use separate CLI invocations; API providers make independent requests through VITA. There is no Vita Tree queue or concurrency cap. Each run analyzes then adapts sequentially; different branches run at the same time. Only the running branch stays locked for edits and publication. Provider rate limits and machine resources still apply.

Leaving a branch (back to the list, opening another branch, or closing the page) releases its clean, idle Vita Tree worktree so the branch can be checked out from the CLI. No force removal is used. Running operations, uncommitted changes, untracked files, and ignored files keep the worktree intact; the UI explains when local files prevent release. Commit or move those files, then open and leave the branch again. Worktrees created outside Vita Tree and the original repository are never removed.

Open **AI runs** from any screen for progress, provider/model settings, timing, and completion or failure messages. Branch badges and persistent in-app notifications show results waiting for review. Selecting a result opens its branch's Job & AI view with that run's retained reports and source files, including its original CV. Reviewing a result clears only that run's notification. The opportunity label is the branch name; job description text and provider output are not included in the global status list.

Run history and review state survive browser refreshes and server restarts. A server restart marks unfinished work as interrupted; it does not automatically resume or resend AI requests. Start a new run after reviewing the branch. Keep one Vita Tree server per CV repository. No desktop-notification permission is needed.

With the `[ai]` extra or `--vita-source`, the child-process adapter makes environment credentials available to VITA and forwards Codex reasoning as an explicit `-c model_reasoning_effort` override for both steps. Available levels come from the selected model's entry in `$CODEX_HOME/models_cache.json` (default `~/.codex`). Models absent from that catalog and non-Codex providers offer **Provider default** only; unsupported settings are rejected by the server. No parent VITA source files or global Codex settings are changed.

The **Appearance** selector in the header offers Light, Dark, and System. Your preference is saved in this browser; System follows OS appearance changes. Reading pages and compiled PDFs remain white in dark mode.

For a pipx editable installation, source changes take effect when you restart `vt`; no reinstall is needed. To reinstall its environment explicitly, run `pipx reinstall vita-tree`, then restart the command above.

## What is supported and what is limited

| Capability | Status |
| --- | --- |
| Centered, responsive branch list and original/new comparison | Implemented |
| Actual LaTeX syntax parsing with positions | `pylatexenc` AST, not regex stripping |
| Common `resume.cls` content: names, addresses, rSection/rSubsection, formatting, bullets, tabularx | Structured reading view supported |
| Text selection and mapped editing | HTML reading view and PDF text layer; edits made in Structure/LaTeX update the source |
| Exact fonts, spacing, line breaks, page breaks | Compiled PDF is authoritative |
| Arbitrary macro expansion / exact HTML reproduction of every LaTeX package | Not supported; use PDF and source editing |
| Editing directly inside the compiled PDF | Not supported; PDF is read-only, then recompiled after source edits |
| `\\input` / `\\include`, custom classes, images | Included in compilation when present in the repository snapshot; included files are not visually editable in Structure |
| Multi-file uncommitted changes when creating a branch | Only the displayed main document is copied; other files come from the base commit |
| Bibliography, makeindex, minted/shell-escape builds | Not orchestrated; current compiler runs the selected TeX engine twice |
| Guaranteed perfect PDF reading order for arbitrary templates/fonts | Not possible; depends on the PDF's text encoding and layout |
| Successful AI generation for every provider | Depends on VITA credentials/provider availability; failed runs do not replace the CV |

Structure preserves unsupported source and explicitly reports unknown commands/environments. It is a reading/editing aid, not a TeX engine. Source edits can temporarily be invalid; the UI reports parse/compile failures instead of pretending a stale PDF is current. AI results are syntax-checked but still require PDF compilation and factual review.

PDF previews and AI snapshots are stored under the repository Git common directory's `vita-tree/pdf/` and `vita-tree/runs/`. AI input text is retained in `vita-tree/run-inputs/`, and run status and review state in `vita-tree/job-history/`. These can accumulate; keep the server stopped before manually cleaning old cache folders. Do not delete `worktrees/` directly; use Git's worktree commands.

## Development and verification

```powershell
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
python -m playwright install chromium
python tests/browser_check.py --browser chromium
python tests/browser_jobs.py --browser chromium
```

Browser tests cover editing, branch creation, provider settings, themes, conflicts,
and real PDF compilation and text selection. They use synthetic CVs and a fake AI
provider. Screenshots and PDFs are saved in ignored `.test-artifacts/`.

PDF.js is pinned in `package-lock.json`; browser assets and its Apache license are vendored into the Python package. Node is only needed to refresh these assets:

```powershell
npm ci
npm run vendor
```

Use Node 22.13+ or 24+ when updating PDF.js. The application itself runs on Python 3.10+.

## Releases

Use `feat:` and `fix:` commit messages. Release Please opens a PR updating the
version and changelog; merging it creates the release tag. Code, browser/PDF,
package installation, and privacy checks run before TestPyPI and PyPI uploads.
Publishing uses `PYPI_API_TOKEN` in the `pypi` environment,
`TEST_PYPI_API_TOKEN` in `testpypi`, and the repository's `RELEASE_PLEASE_TOKEN`.

## Author

Created and maintained by [Abdellah HALLOU](https://github.com/ABDELLAH-Hallou),
the project's main contributor. Contact: [abdeallahhallou33@gmail.com](mailto:abdeallahhallou33@gmail.com).

Vita Tree is MIT licensed. Bundled PDF.js components retain their original licenses;
see [third-party notices](https://github.com/ABDELLAH-Hallou/vita-tree/blob/main/THIRD_PARTY_NOTICES.md).
