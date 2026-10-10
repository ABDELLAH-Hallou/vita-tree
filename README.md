# Vita Tree

A local CV workspace for Git branches: a centered branch list, source-mapped LaTeX reading view, side-by-side comparison, editing, job context, VITA AI results, and real PDF previews.

## Install and run

```powershell
python -m pip install -e .
vt run C:\path\to\cv-repository --vita-source C:\path\to\vita-cv
```

`--vita-source` uses that local VITA checkout with Vita Tree's Python interpreter. Alternatively install `vita-cv` so `vita` is on PATH. VITA provider authentication/configuration is still required. PDF compilation requires MiKTeX or TeX Live and your template's packages/fonts. The interface and bundled PDF.js viewer work without a CDN.

```text
vt run [REPOSITORY] [--port 8765] [--file main.tex] [--no-browser] [--vita-source PATH]
```

The server accepts localhost connections only. It can modify the chosen repository, so do not expose it through a network proxy. Compile only trusted local LaTeX: disabling shell escape is not an operating-system sandbox.

## Workflow

1. Open a branch. Existing checked-out branches display working files, including uncommitted `main.tex`, `job.md`, and `.vita/results/*.md`. Other branches display committed files.
2. Choose **Branch from this**, name the branch, and paste the job description. Vita Tree creates a Git linked worktree below the repository's Git common directory at `vita-tree/worktrees/`. The original checkout is not switched. The viewed main document and the new `job.md` are written to the new worktree.
3. In **Structure**, select/copy text normally, or double-click text in the new version to edit it. The parser maps text to its exact source range and escapes LaTeX special characters. **LaTeX** provides the full editable source for other changes. Save writes the branch worktree's real file.
4. In **Job & AI**, save `job.md`, select a provider, model, reasoning level, and language, and run **Analyze & adapt**. The app runs `vita analyze --auto`, then `vita adapt --auto`, in a separate snapshot. It checks the reports and a changed, parseable `main.tex` before applying output. The exact pre-run CV becomes the original comparison. Failed and conflicting results remain in the run folder shown in the error.
5. Review `.vita/results/analyze.md`, `.vita/results/adapt.md`, the source diff, and both PDFs. The PDF view uses the actual TeX output with PDF.js canvas rendering and its text layer. Choose a different engine if your template requires it.

**Saves are local and uncommitted.** No commit, push, or VITA company-registry update happens automatically. The workspace footer gives the directory to use with Git/VITA. Commit the CV and job description from that directory when ready. Linked worktrees persist across server restarts; Git will refuse to check out their branch elsewhere until you remove the worktree with Git after preserving your edits.

For existing branches without a recorded baseline, Original means that branch's committed CV. New branches retain the viewed base CV; AI runs retain the pre-run CV. Reload imports changes made by a terminal/editor. Saving with a stale revision returns a conflict and preserves the user's editor text.

VITA's local `config.json`, `extensions.json`, and `cv.yaml` are supplied to isolated AI runs. API-key/token values from `.vita/.env` are passed in child-process memory. Existing reports are branch-local. The UI does not expose credentials or raw provider logs.

Provider/model dropdowns scan `.vita/extensions.json` on every local and remote branch ref and in linked working trees. Duplicate choices are combined; hovering over Model lists their sources. Reload rescans the repository. Choosing a model from another branch overrides only the isolated run, leaving your branch configuration intact. These are discovered configurations, not a guarantee that historical model names remain available to your account.

With `--vita-source`, the child-process adapter makes environment credentials available to VITA and forwards Codex reasoning as an explicit `-c model_reasoning_effort` override for both steps. Available levels come from the selected model's entry in `$CODEX_HOME/models_cache.json` (default `~/.codex`). Models absent from that catalog and non-Codex providers offer **Provider default** only; unsupported settings are rejected by the server. No parent VITA source files or global Codex settings are changed.

The **Appearance** selector in the header offers Light, Dark, and System. Your preference is saved in this browser; System follows OS appearance changes. Reading pages and compiled PDFs remain white in dark mode.

For a pipx editable installation, source changes take effect when you restart `vt`; no reinstall is needed. To reinstall its environment explicitly, run `pipx reinstall vita-tree`, then restart the command above.

## What is supported and what is limited

| Capability | Status |
| --- | --- |
| Centered, responsive branch list and original/new comparison | Implemented |
| Actual LaTeX syntax parsing with positions | `pylatexenc` AST, not regex stripping |
| sample CV `resume.cls` content: names, addresses, rSection/rSubsection, formatting, bullets, tabularx | Structured reading view supported |
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

PDF previews and AI snapshots are stored under the repository Git common directory's `vita-tree/pdf/` and `vita-tree/runs/`. These can accumulate; keep the server stopped before manually cleaning old cache folders. Do not delete `worktrees/` directly; use Git's worktree commands.

## Research behind the implementation

- [pylatexenc's parser and source-position API](https://pylatexenc.readthedocs.io/en/v2.10/latexwalker/) explains its AST and explicitly distinguishes parsing from a full TeX engine.
- [PDF.js rendering examples](https://mozilla.github.io/pdf.js/examples/) describe page viewports, canvas rendering, and high-DPI scaling. The packaged PDF.js text-layer implementation supplies selection at the same viewport scale.
- [Git worktree documentation](https://git-scm.com/docs/git-worktree) describes isolated linked checkouts and branch checkout constraints.
- [MiKTeX engine options](https://docs.miktex.org/manual/miktex-xetex.html) document disabled shell commands, disabled automatic package installation, and noninteractive compilation options.
- Local `vita-cv/vita/commands/ai_step.py` and `vita/helpers/context_builder.py` define the actual `analyze`/`adapt` artifact contract. The adapter checks outputs because that CLI can report failure while exiting with code zero.
- [Official Codex configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) documents model-dependent reasoning levels and explicit model/reasoning overrides. The local model catalog determines the offered choices.

## Development and verification

```powershell
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
python tests/browser_check.py --sample-cv C:\path\to\cv-repository
```

The browser smoke test uses installed Google Chrome through Playwright and an isolated Git fixture. It tests provider/model choices across branches, reasoning delivered to both controlled CLI steps, theme persistence and system changes, branch creation, real file saves, mapped edits, source edits, reports, conflicts, desktop/mobile layout, actual TeX compilation, and PDF text selection in both themes. `--sample-cv` additionally compiles copies of sample CV's main.tex and resume.cls and checks its pages. It does not change sample CV or call a paid AI provider. Screenshots and PDFs go in ignored `.test-artifacts/`.

PDF.js is pinned in `package-lock.json`; browser assets and its Apache license are vendored into the Python package. Node is only needed to refresh these assets:

```powershell
npm ci
npm run vendor
```

Use Node 22.13+ or 24+ when updating PDF.js. The application itself runs on Python 3.10+.
