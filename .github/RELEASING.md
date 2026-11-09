# Maintaining Vita Tree

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

For reproducible multi-application stress tests, declared performance budgets,
resource measurements and recovery checks, see [workflow load profiles](../docs/workflow-load.md).

Browser/accessibility targets, repeatable keyboard checks and current coverage
limits are in [accessibility verification](../docs/accessibility.md), with a
[representative-user study protocol](../docs/usability-study.md).

PDF.js is pinned in `package-lock.json`; browser assets and its Apache license are vendored into the Python package. Node is only needed to refresh these assets:

```powershell
npm ci
npm run vendor
```

Use Node 22.13+ or 24+ when updating PDF.js. The application itself runs on Python 3.10+.

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
