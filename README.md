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

## Check your input and setup

Open a complete **UTF-8 LaTeX project in Git**. AI preparation uses `main.tex` at the
collection root, with its local classes, styles, images, fonts and includes.
Required project assets must be tracked or non-ignored files. Tree does not
import PDF, DOCX or scanned CVs. `vt run --file other.tex` remains available for
direct viewing and PDF previews; preparation currently requires `main.tex`.

Use **Check input & setup** from the application list, including when an entry is
missing, or **Check setup** inside an application. Save editor drafts first.
Checks validate supported JSON settings/entry fields and compile an isolated
copy with the restricted local compiler. Missing engines, packages/classes,
inputs and fonts have separate next actions. Install dependencies yourself with
your TeX distribution manager; Tree never enables an installer or shell escape.
Other Vita CV configuration/profile semantics remain the backend's responsibility.

Choose Automatic, PDFLaTeX, XeLaTeX or LuaLaTeX in setup checks. Automatic uses
XeLaTeX for `fontspec`, `polyglossia` or `unicode-math` declared in the entry;
otherwise it uses PDFLaTeX. Select explicitly if an included class requires
another engine. The choice applies to new preparations and cover-letter PDFs;
retries retain the original run's engine. Checks run again against the captured
project before any CV-dependent AI step. CV, job and asset changes during that
check cause a conflict; a preparation keeps its submitted AI settings. Manual
checks also invalidate their result if project settings change during the check.
Job-requirement extraction remains independent of CV compilation.

Structure is an approximate reading view, not a TeX validator. A project can
compile correctly even when Structure cannot display it. A passed preflight
covers dependencies used by that captured compilation; future AI output may
introduce new requirements. Only compile templates and installations you trust;
restricted compilation is not an OS sandbox. Temporary check copies are removed
on completion; manual check results are browser-local, while a run's summary is
retained with its history. No check calls a provider or changes project files.

## Applications and saving

Choose **New application**, give it a natural name such as “Acme — ML Engineer”, and choose a starting CV. Vita Tree keeps the internal Git identifier separate from the displayed name. Existing names remain available without automatic reclassification as templates.

**Save draft** writes edits on this computer. **Save** records a version and syncs only the selected application to its connected destination after you review the changes and enter a change note. A failed sync preserves the local version and offers **Retry sync**. The status distinguishes unsaved edits, saved drafts, and versions waiting to sync; “Saved and synced” is shown only after a successful sync in the current session.

File paths, source filenames, PDF engine choices, and raw support events are available in expandable details. The source editor and advanced tooling remain available. Browser URLs, CLI commands, API fields, Git operations, and existing repository files retain their technical names for compatibility.

## Workflow

The LaTeX tab includes syntax colors, line numbers, bracket matching, undo/redo,
and search (Ctrl/Cmd+F). Live syntax checks underline parser errors; click the
status below the editor for details. Checks report the first syntax error and
do not validate custom macro expansion or installed packages; compile the PDF
for full validation. Unsaved and temporarily invalid source can still be saved.
The editor is bundled locally and follows the selected light/dark theme.

1. Open a branch. Existing checked-out branches display working files, including uncommitted `main.tex`, `job.md`, and `.vita/results/*.md`. Other branches display committed files.
2. Choose **Branch from this**, name the branch, and paste the job description. Vita Tree creates a Git linked worktree below the repository's Git common directory at `vita-tree/worktrees/`. The original checkout is not switched. The viewed main document, supported local include drafts and the new `job.md` are written to the new worktree.
3. In **Structure**, select/copy text normally, or double-click text in the new version to edit it. The parser maps text to its exact source range and escapes LaTeX special characters. **Source · Advanced** provides the full editable source for other changes. Save writes the branch worktree's real file.
4. In **Job & AI**, save the job description and select a provider, model, reasoning level, and language. Use **Prepare application** for every available AI step, **Start selected steps** for any checked subset, or select a graph node and choose **Run … only**. Each enabled step runs in order in an isolated snapshot. Different branches still run concurrently, without a queue.
5. Follow the **Application workflow** graph: extract → analyze → adapt → AI review → cover letter → validate. Select a task for its status, duration, output, and independent run action, or choose an earlier run. Actions always use the current saved branch files, even when inspecting an older run. Skipped tasks make no AI calls; failed tasks block downstream work. Input preflight checks compilation before CV-dependent AI steps. Final checks validate source and protect against conflicts; Structure limitations defer to restricted compilation. Review the Markdown reports, changes, and compiled PDFs before committing.
6. Use **Save** to review the destination, commit message, and included files, then publish only the selected branch. A failed push leaves the commit safely in the worktree and offers a push-only retry.

**Save draft** remains local and uncommitted. **Save** reviews the main document, its supported reachable local includes, `job.md`, the generated `cover-letter.tex`, and VITA Markdown/JSON/TOON reports; unrelated working-tree changes are reported and excluded. It never force-pushes or publishes other branches. Worktrees containing local changes persist across server restarts; leaving a clean worktree releases its branch for CLI checkout.

### CVs with included files

Use **CV file** in Edit CV, Source or Changes to open a local `\input{sections/experience}` or `\include{education}` file. Paths resolve from the project root, including paths inside nested files, as in Vita CV. Each file has its own Before/Current comparison, syntax editor and Structure source map. Structure edits show the originating path and character range; saving writes that file, without flattening the CV into `main.tex`. Changing files asks before discarding unsaved edits.

Navigation supports literal braced `.tex` inputs (the extension may be omitted), up to 64 files, 16 nesting levels, 256 references, 2 MB per file and 8 MB total. Files must be tracked or nonignored regular UTF-8 project files, with names matching their Git paths and case exactly. Missing files, cycles, limits, ignored/excluded files, traversal and symlink/junction paths produce diagnostics. Correct the include command in Source or restore the file externally, then Reload. Files present only in Before are view-only.

Structure displays one file at a time, not a merged typeset document. Macro expansion (including inputs inside command/environment definitions), conditional execution, `\includeonly`, unbraced/computed paths and import/subfiles package resolution are not evaluated. Commands that depend on surrounding files can render approximately or lack editable text; use Source for exact edits and PDF for the assembled layout. Unsupported navigation does not rewrite includes or change Vita CV's context resolver or restricted PDF compiler.

Included-file edits participate in save-conflict checks, new-application draft capture, commit review, checkpoint dependency hashes and PDF freshness checks. If another editor changes an include, Reload before saving or exporting a new PDF. These are optimistic revision checks, not cross-process filesystem locks; the local application is not an OS sandbox against another program racing file operations.

Applications created before include-draft capture use their base commit for Before's included files. Earlier uncommitted include versions cannot be reconstructed.

For existing branches without a recorded baseline, Original means that branch's committed CV. New branches retain the viewed base CV; AI runs retain the pre-run CV. Reload imports changes made by a terminal/editor. Saving with a stale revision returns a conflict and preserves the user's editor text.

VITA's local `config.json`, `extensions.json`, `cv.yaml`, and task Markdown files under `.vita/skills/<step>/` are supplied to isolated AI runs. API-key/token values from `.vita/.env` are passed in child-process memory. Existing reports are branch-local. The UI does not expose credentials or raw provider logs.

**Shared AI setup:** choose any of Vita CV's supported providers, then select a suggested model or type any model ID your account can access. Suggestions come from `.vita/extensions.json` across repository refs and working trees, the local Codex catalog, and saved AI setups. Empty model IDs use the provider/Vita CV default. Model suggestions do not prove account access.

Use **Add API key…** to create a named connection and reuse it across steps, or choose existing local credentials from the environment or `.vita/.env`. Codex uses your local CLI login. Keys added in the UI stay only in server memory and must be added again after a server restart; expired connections are shown with instructions to reconnect. They are never returned in API responses or saved in browser storage, Git, settings, or run history.

Click any AI step in the workflow graph to open its settings popup. Choose **Customize this step**, edit the provider, model, reasoning, or connection, and select **Apply to step** to save the setup locally and update that component. **Use shared setup** restores inheritance. Cancel or Escape discards pending popup edits. Past and running preparations show their recorded setup as read only; **Configure next run** opens the current draft when available.

The same controls remain under **Advanced · customize individual steps**. New custom setups start with a copy of the shared setup; turn customization off to inherit future shared changes again. **Use shared setup for every step** clears all overrides. **Save AI setup** saves non-secret choices locally for the current application. New runs use the visible settings even before saving. Workflow nodes and their inspectors show the effective model, including the captured configuration for historical runs. See [AI setup design and behavior](docs/ai-workflow-configuration.md) for the research and execution contract.

**Background AI runs:** use one `vt run` server and port for all branches. Every workflow action starts an independent background process immediately, with its own provider, model, reasoning, language, and isolated files. Codex runs use separate CLI invocations; API providers make independent requests through VITA. There is no Vita Tree queue or concurrency cap. Each run executes its enabled tasks sequentially; different branches run at the same time. Only the running branch stays locked for edits and publication. Provider rate limits and machine resources still apply.

Leaving a branch (back to the list, opening another branch, or closing the page) releases its clean, idle Vita Tree worktree so the branch can be checked out from the CLI. No force removal is used. Running operations, uncommitted changes, untracked files, and ignored files keep the worktree intact; the UI explains when local files prevent release. Commit or move those files, then open and leave the branch again. Worktrees created outside Vita Tree and the original repository are never removed.

Use the sidebar **Running**, **Needs review**, and **Needs attention** filters to find active work and results. Open a branch for its workflow progress and run history. The sidebar counts and branch badges show results waiting for review. In **Needs review**, open a branch to inspect its pending result in **Job & AI**, including retained reports and source files. Click **Mark as reviewed** beside **Preparation history** when finished. This clears only the selected run; a branch leaves **Needs review** once all its completed runs are marked. Opening results alone does not dismiss them, and reviewed state survives refresh and server restarts. Use the run selector and **View results** to revisit earlier runs. The opportunity label is the branch name; job description text and provider output are not included in the global status list.

From **All applications**, select branches with unreviewed runs, then choose **Mark selected as reviewed**. Select visible respects the current search and filter. The action acknowledges the selected branches' finished runs, including failures; it does not change CV files. Active runs cannot be acknowledged. If a history write fails, successful acknowledgements are kept and failed runs remain selected for retry.

Run history and review state survive browser refreshes and server restarts. A server restart marks unfinished work as interrupted; it does not automatically resume or resend AI requests. Start a new run after reviewing the branch. Keep one Vita Tree server per CV repository. No desktop-notification permission is needed.

With the `[ai]` extra or `--vita-source`, the child-process adapter supplies each step's credentials and forwards its Codex reasoning as an explicit `-c model_reasoning_effort` override. Known Codex models use the levels in `$CODEX_HOME/models_cache.json` (default `~/.codex`). Custom Codex model IDs expose explicit levels; the provider validates their actual support when called. Other Vita CV providers currently use **Automatic** reasoning. No parent VITA source files or global Codex settings are changed.

Extraction and structured evaluation reports require Vita CV 2.5+. The UI detects task prompts in the connected installation and disables unavailable options; older integrations can still run Analyze and Adapt together or independently. Each enabled step uses the shared AI setup or its explicit custom setup, overriding environment stage routing only in that run. Analyze, Adapt, and available AI review are selected initially; every AI step can be unchecked. **Prepare application** includes all supported AI steps regardless of checkbox selection. Validation runs automatically before applying outputs and can also run alone, without a job description or AI provider. Single steps never launch other AI steps. Analyze, Review, Extract, and Cover leave the CV and comparison baseline untouched. Review uses an existing matching structured analysis for score deltas, or evaluates the CV on its own when none exists. Matching extraction and analysis are captured at launch; analysis Markdown without job provenance is not reused. Running Analyze again clears the previous score delta; unrelated reports remain available. The current UI requires `tex_entry=main.tex` and, for cover generation, `cover_tex_entry=cover-letter.tex`. Cover letter generates `cover-letter.tex` and compiles a PDF before succeeding. Use **Open generated cover-letter PDF** in the run results to view that exact run, or select **Cover letter** in the PDF tab to compile the branch’s saved source. PDF compilation failures fail the cover step and preserve existing branch files; the attempted source remains in the run results.

Vita CV 2.5 writes `analysis.md`/`analysis.json`, `review.md`/`review.json`, and comparable `delta.md`/`delta.json` reports. Vita Tree retains these along with `job.json` and `job.toon`. Reports render as readable Markdown with tables; raw HTML is treated as text. Historical runs without recorded task progress display **Not recorded**, never inferred success.

The theme icon in the header switches between Light and Dark. Your preference is saved in this browser. Reading pages and compiled PDFs remain white in dark mode.

For a pipx editable installation, source changes take effect when you restart `vt`; no reinstall is needed. To reinstall its environment explicitly, run `pipx reinstall vita-tree`, then restart the command above.

## Review and continue

The workflow's **Your next step** action opens the required review or starts preparation. **Approve & continue** saves your decisions and resumes with the captured AI setup; you do not need to retry manually. Your CV is updated after the remaining steps and final checks succeed. A conflict preserves your edits and the reviewed draft.

Review sheets keep Close and approval controls visible while you scroll. Factual changes show highlighted original/proposed LaTeX; **Accept all** or **Keep all originals** selects decisions in bulk, with individual edits still available. Confirm the meaning before approving. The full proposed-source preview includes syntax diagnostics; compilation remains authoritative.

**Review mode** defaults to **Review before continuing**. Select **Automatic · accept AI proposals** before starting a run to accept extracted requirements and proposed factual changes without pausing. Automatic decisions retain separate provenance and attempt history. Provider errors, compilation failures, and conflicts still stop the run. Restarted work is not silently resumed, and neither mode commits or pushes automatically.

Unselected graph steps can show **Done earlier** when execution history exists. This label preserves history; it does not claim the old result matches changed inputs or will be reused. Checkpoint reuse still requires matching inputs and configuration.

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
| `\\input` / `\\include` | File navigation and mapped editing for supported literal local `.tex` inputs; PDF assembles the project |
| Custom classes, images, dynamic/import-package includes | Preserved for restricted compilation; no class/image editor or arbitrary TeX expansion in Structure |
| Multi-file uncommitted changes when creating a branch | Main document and supported reachable include drafts are copied; other assets come from the base commit |
| Bibliography, makeindex, minted/shell-escape builds | Not orchestrated; current compiler runs the selected TeX engine twice |
| Guaranteed perfect PDF reading order for arbitrary templates/fonts | Not possible; depends on the PDF's text encoding and layout |
| Guided input and dependency preflight | Saved-project JSON/entry checks and restricted compilation before CV-dependent AI calls; no automatic installs or import conversion |
| Successful AI generation for every provider | Depends on VITA credentials/provider availability; provider, validation, and conflict failures preserve the CV; inspect files after disk-write failures |

Custom command and environment definitions keep their original source ranges. Their bodies are read as token lists rather than executed: an environment may open in one definition argument and close in another. Structure shows supported body text with an approximate-layout notice; use PDF preview for the actual expanded layout.

Structure preserves unsupported source and explicitly reports unknown commands/environments. It is a reading/editing aid, not a TeX engine. Source edits can temporarily be invalid; the UI reports parse/compile failures instead of pretending a stale PDF is current. Input preflight compiles the captured project. Generated CVs receive structure checks, with restricted compilation when Structure cannot validate them; cover letters are compiled. Always review the final PDF and factual changes.

PDF previews and AI snapshots are stored under the repository Git common directory's `vita-tree/pdf/` and `vita-tree/runs/`. AI input text is retained in `vita-tree/run-inputs/`, cover-letter PDFs in `vita-tree/run-pdfs/`, and run status and review state in `vita-tree/job-history/`. These can accumulate; keep the server stopped before manually cleaning old cache folders. Do not delete `worktrees/` directly; use Git's worktree commands.

Vita Tree reserves its listening port before opening workspace history. A second server on the same address and port is rejected; stop the existing server or choose a different `--port`. On Windows, the port is reserved exclusively so an older server cannot silently receive requests intended for a new one.

## Resume a failed preparation

Choose a failed or interrupted preparation in its history, then select **Retry preparation**. Review the verified steps to reuse and the steps to run again before choosing **Start new attempt**. Save pending CV and job description edits first. Each attempt retains its parent, original preparation, step outcomes, and backend format-attempt history; selecting an earlier attempt opens its own results.

Checkpoints are immutable copies of successful step outputs, including the adapted CV and a validated cover-letter PDF. Reuse requires matching captured CV/JD, include-file hashes, approved requirement revisions, dependency artifacts, effective per-step service/model/reasoning/connection, project settings, skills, credentials fingerprints, and backend implementation. The first missing, changed, expired, or unverifiable checkpoint invalidates that step and all later selected steps. Final checks always run. Changing only Cover's setup can reuse preceding steps; changing the CV or job description starts the selected workflow again. A Cover retry after Adapt uses the verified isolated adapted source, never an unrelated draft.

Vita CV 2.6.1+ supplies versioned structured outcomes for Extract, Analyze, and Review. The child adapter consumes these and the boolean command API used by Vita CV's CLI for Adapt/Cover; Tree then verifies expected files, source preservation, LaTeX structure, and cover compilation before checkpointing. Provider stdout is never parsed as a success contract or exposed in run history. CLI integrations without this contract may execute normally but their outputs are not verified resume checkpoints. Existing report context does not count as a completed step. The `[ai]` extra requires the compatible Vita CV version. Session API connections must be re-added after restart; matching credentials can still reuse checkpoints, while a changed key invalidates them.

Retries run in new isolated folders. Failed or interrupted work does not publish over application drafts. Publication checks source, job, report, include-file and criteria conflicts, and journals multi-file writes for rollback and restart recovery. External edits encountered during recovery are preserved. If rollback cannot complete, editing and retrying that application remain blocked until folder access is repaired and Vita Tree is restarted. AI setup and skill edits made after launch apply to the next attempt; an active attempt keeps its submitted setup.

Vita CV 2.8.0+ also pauses Tailor CV and Cover letter for source-linked factual review. Choose accept, reject, or edit for every change, save the reviewed preparation draft, then retry to continue from matching checkpoints. Rejected wording is excluded from downstream work. [Factual review and provenance](docs/FACTUAL_REVIEW.md) explains conflicts, atomic publication, keyboard controls and retention.

Extract also creates a canonical job definition for review. Correct requirements and source references, keep employment conditions separate, then approve an immutable revision before continuing. Applications with the same job description share the approval; run history records the exact revision used. [Requirements review](docs/REQUIREMENTS.md) explains approval, corrections and downstream invalidation.

Verified checkpoints live in the Git common directory under `vita-tree/checkpoints/`. Cleanup runs on startup, launch, and completion, and is also available under **Activity & support → Retained retry results**. Retention is at most 7 days, 20 terminal preparations, and 256 MB total, with a 32 MB limit per checkpoint. Active attempts and their immediate resume parents are protected from eviction; checkpoint writes stop when the byte budget is full. An expired checkpoint causes a fresh rerun, never a guessed success. Cleanup deletes only checkpoint copies; application folders, drafts, preparation/review history, `runs/`, `run-inputs/`, and `run-pdfs/` remain. The existing result caches require separate cleanup with the server stopped.

## Activity, errors, and logs

Open **Activity & support** for preparation history, request metrics, and recent events. Select a preparation or use **Execution details** in its workflow to inspect phases, attempts, requested/effective AI routing, capture availability, and safe provider errors. **Retry preparation** preserves captured routing and language by default. Explicitly choose **Use the current application setup** to change them and review the verified checkpoint plan before starting another attempt.

AI failures, explicit generation checks, and captured-setup retries are described in [AI troubleshooting](docs/PROVIDER_FAILURES.md).

Execution traces live in the application project's .vita/logs/traces/ directory, independently of disposable workspaces and checkpoint cleanup. Older backends show limited diagnostics. See [Execution inspector](docs/EXECUTION_INSPECTOR.md) for trace locations, alternative destinations, capture policies, retention, compatibility, and inspectable support exports. Errors also include request references that can be found in the existing event search.

`vt run` prints the log filename and metrics URL at startup. Rotating JSON logs live outside the repository, under `%LOCALAPPDATA%\vita-tree\logs\<repository-id>` on Windows or `$XDG_STATE_HOME/vita-tree/logs/<repository-id>` on other platforms (default `~/.local/state`). Each server session keeps up to six 1 MB files. Logs exclude CV/job contents, prompts, credentials, request payloads, and raw provider output. If file logging cannot write, the UI retains the latest 200 events in memory and reports the logging failure.

```powershell
vt run . --log-level debug --log-dir C:\path\to\private-logs
```

Prometheus metrics are available at `http://127.0.0.1:8765/metrics` on the same server port. They include HTTP counts/durations, active runs, workflow outcomes, and step counts/durations. Request/workflow counters reset on restart; saved run history remains available.

**Permission denied when marking reviewed:** the run is acknowledged only after history is saved. Temporary file locks are retried. Permanent write denials still require write access to `.git/vita-tree`; if the server was launched inside a restricted agent terminal, stop it and restart `vt run` from a normal terminal as your own user. No administrator mode or automatic permission changes are required by Vita Tree.

A Git `cannot lock ref ... Permission denied` error means the server cannot write the repository's Git metadata. Stop Vita Tree and start `vt run` from a normal terminal outside a restricted sandbox. If it persists, check write permission for the repository and its `.git` folder. Removing a lock file does not resolve a permission denial.

## Save a PDF into its worktree

Compile the PDF, then click **Save PDF to application folder** above the preview. Cover letters save as `cover-letter-Jordan_Lee.pdf`, separately from the CV, and use the same stale-source and overwrite checks. A CV headed “Jordan Lee” saves as `cv-Jordan_Lee.pdf` in the selected branch's existing worktree. The original preview uses `cv-Jordan_Lee-original.pdf`; documents without a recognizable name use `cv.pdf`. The UI shows the saved path. Existing files require confirmation, and a changed branch must be compiled again before saving.

These PDFs are local artifacts; saving does not stage, commit, or push them. Repository ignore rules still apply. **Open PDF** uses the browser viewer, whose own download button follows the browser's save-location settings.

## Development and verification

```powershell
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
python -m playwright install chromium
python tests/browser_check.py --browser chromium
python tests/browser_jobs.py --browser chromium
python tests/browser_workflow.py --browser chromium
python tests/browser_ai_settings.py --browser chromium
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

## Security

Read the [security boundaries and threat model](SECURITY.md) before opening unfamiliar templates or repository configurations. The [scoped security review](docs/SECURITY_REVIEW.md) records synthetic tests, fixes, and remaining limits.

## Releases

Use `feat:` and `fix:` commit messages. Releases have two separate PRs:

1. **Release to TestPyPI:** Release Please updates the version and changelog.
   Merging this PR creates the tag/GitHub release and runs code, browser/PDF,
   installation, and privacy checks before uploading to TestPyPI only.
2. **Publish to PyPI:** after verifying the TestPyPI downloads, automation opens
   a separate promotion PR with installation commands, the source commit, workflow
   run, and SHA-256 hashes. Test that candidate, then merge this PR to publish it
   to PyPI. Leaving it open keeps the candidate off PyPI.

Promotion downloads the exact wheel and source archive from TestPyPI and verifies
their hashes again; it does not rebuild from a potentially newer main branch.
If a candidate needs fixes, close its promotion PR and release a new version.
Published candidate files and version numbers cannot be replaced. If production
publishing fails, rerun the failed workflow or run **Promote approved release to
PyPI** on `main` with the already-merged promotion PR number.

Publishing uses `PYPI_API_TOKEN` in the `pypi` environment,
`TEST_PYPI_API_TOKEN` in `testpypi`, and the repository's `RELEASE_PLEASE_TOKEN`.
The release automation token needs permission to create branches and PRs. No new
secrets or environments are required for the two-stage process.

## Author

Created and maintained by [Abdellah HALLOU](https://github.com/ABDELLAH-Hallou),
the project's main contributor. Contact: [abdeallahhallou33@gmail.com](mailto:abdeallahhallou33@gmail.com).

Vita Tree is MIT licensed. Bundled PDF.js components retain their original licenses;
see [third-party notices](https://github.com/ABDELLAH-Hallou/vita-tree/blob/main/THIRD_PARTY_NOTICES.md).
