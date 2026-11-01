# Frontend development

Vita Tree serves a compiled React application from the existing local Python
server. `vt run` and the PyPI installation continue to work without Node,
internet access, or a second server.

Use Node 24 LTS and install development dependencies with `npm ci --ignore-scripts`.
Run `npm run typecheck`, `npm run test:frontend`, and `npm run build` before
committing frontend changes. The compiled assets are versioned so a Python-only
installation can serve them immediately.

For development, install this checkout with `python -m pip install -e '.[test]'`,
start `vt run PATH_TO_A_SYNTHETIC_CV_PROJECT`, then run `npm run dev` in a second
terminal. This rebuilds on source changes; refresh the same Vita Tree page.
Development deliberately uses the Python origin and its session/CSRF checks.
There is no cross-origin Vite API proxy. Stop the watcher and run `npm run build`
before committing.

## Source ownership

- `frontend/src/components`: React shell, application list, workflow graph,
  responsive navigation and Radix keyboard quick actions.
- `frontend/src/api/client.ts`: TanStack Query request boundary. Branch URLs have
  separate cache keys. Reads return isolated objects; user mutations never retry
  automatically. Editor lint requests preserve cancellation.
- `frontend/src/styles`: shared light/dark tokens and CSS Modules for the frame.
- `frontend/src/compat`: existing feature controllers and their layout styles.
  These remain JavaScript during the view migration. They preserve the tested
  source-map, PDF.js, CodeMirror, approval, checkpoint, import and publication
  lifecycles. React does not reconcile editor/PDF-owned DOM.
- `src/vita_tree/static`: generated production modules, CSS, manifest and offline
  vendors. Edit frontend sources, then rebuild these outputs.

The build manifest records normalized source hashes. Python tests reject stale
assets, missing packaged chunks and imports that cannot resolve offline. The
wheel contains all runtime chunks and notices; the sdist also includes frontend
sources and the lockfile.

## Feature boundaries to preserve

Application creation and worktree release, bulk reviewed marking, include-aware
Structure/source editing, dirty/conflicting draft checks, local save versus Git
sync, restricted compilation, PDF text selection/export, stage settings and
connection inheritance, requirements/factual approvals, retries and captured
configuration, history, execution support and Jobenu import continue through the
same backend APIs. No provider, compiler, approval or publication contract changes
are part of the frontend migration.

Run `python tests/browser_migration.py` for the new navigation, dirty-cancel,
responsive and theme checks. Existing `tests/browser_*.py` scripts exercise the
feature flows; CI also checks Chromium, Firefox and WebKit accessibility scenarios.
These automated checks do not establish screen-reader or human-study coverage.
