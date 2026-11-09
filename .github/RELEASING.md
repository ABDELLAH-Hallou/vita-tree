# Maintainer Release Runbook

This document describes the two-stage release procedure for Vita Tree to TestPyPI and PyPI.
It is intended for repository maintainers.

---

## Commit Conventions

All commits intended for release must follow the Conventional Commits specification:
- `feat:` for new user-facing features (triggers a minor version bump in Release Please).
- `fix:` for bug fixes and security corrections (triggers a patch version bump).
- `chore:`, `docs:`, `test:` for changes that do not increment the release version.

---

## Two-Stage Release Procedure

Releases use a two-stage pull request workflow to ensure that production PyPI packages are byte-identical to tested TestPyPI candidates:

### Stage 1: Release to TestPyPI

1. **Automated PR:** Release Please maintains a release PR updating the version in `src/vita_tree/__init__.py` and the changelog in `CHANGELOG.md`.
2. **Review & Merge:** Merging this PR creates the version tag and initiates `.github/workflows/release.yml`.
3. **Automated Verification:** The workflow runs code quality, browser/PDF integration, clean package builds, and credential/privacy scans (`scripts/check_privacy.py`, `scripts/check_package.py`).
4. **Upload to TestPyPI:** Upon passing all checks, the built wheel and sdist are uploaded to TestPyPI only.

### Stage 2: Publish to PyPI

1. **Promotion PR:** Release automation opens a separate promotion PR containing the verified SHA-256 hashes, TestPyPI download links, and install validation commands.
2. **Candidate Verification:** Maintainers test the TestPyPI candidate in clean virtual environments across supported platforms.
3. **Approval & Publish:** Merging the promotion PR triggers `.github/workflows/publish-pypi.yml`, which downloads the exact wheel and source archive from TestPyPI, verifies their SHA-256 digests, and publishes them to PyPI.
4. **Rejection:** If a candidate has issues, close its promotion PR without merging and push a fix commit to start a new release cycle. Published candidate files and version numbers cannot be replaced.

---

## Recovery and Manual Promotion

If production publishing fails after the promotion PR is merged:
1. Rerun the failed workflow run in GitHub Actions.
2. Or manually trigger **Promote approved release to PyPI** (`publish-pypi.yml`) on `main`, supplying the merged promotion PR number.

---

## Required Secrets and Environments

- `PYPI_API_TOKEN` in the `pypi` environment (scoped to upload to PyPI).
- `TEST_PYPI_API_TOKEN` in the `testpypi` environment (scoped to upload to TestPyPI).
- `RELEASE_PLEASE_TOKEN` repository secret (needs contents and pull-requests permissions).
