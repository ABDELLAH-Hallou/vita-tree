"""Prepare failed-only native resumes without replacing the original batch."""

import json


def failed_rows(record, rows, keys=None):
    eligible = {
        row.get("key"): row for row in rows
        if row.get("status") == "failed" and not row.get("pending")
    }
    if keys is None:
        keys = list(eligible)
    if (
        not isinstance(keys, list) or not keys
        or any(not isinstance(key, str) or key not in eligible for key in keys)
        or len(set(keys)) != len(keys)
    ):
        raise ValueError("Select jobs that are still failed. Jobs waiting for review cannot be retried.")
    planned = {row.get("key"): row for row in (record.get("plan") or {}).get("entries", [])}
    targets = []
    for key in keys:
        row = eligible[key]
        application_id = row.get("application_id") or planned.get(key, {}).get("application_id")
        if not application_id:
            raise ValueError("This batch lacks application identities. Use Preview resume to select the jobs again.")
        target = {**row, "application_id": application_id}
        if (any(not isinstance(value, str) or not value for value in identity(target))
                or identity(target) != identity(planned.get(key, {}))):
            raise ValueError("The application identity or branch changed. Use Preview resume before retrying.")
        targets.append(target)
    return targets


def identity(row):
    return tuple(row.get(field) for field in ("key", "fingerprint", "branch", "application_id"))


def verify_plan(original, retried, targets):
    for field in ("base_commit", "routing_sha256", "preferences_sha256"):
        if not original.get(field) or original[field] != retried.get(field):
            raise ValueError(
                "The starting CV or captured settings changed, or their metadata is missing. "
                "Use Preview resume to review the current configuration. No retry was started."
            )
    if (
        sorted(identity(row) for row in targets)
        != sorted(identity(row) for row in retried.get("entries", []))
    ):
        raise ValueError("The application identities or branches changed. Preview resume before retrying.")


def preview(manager, ident, keys=None):
    from .jobenu import read_json

    with manager.lock:
        if manager.ws._closed or manager.running:
            raise ValueError("Wait for the running batch, or restart Vita Tree, before retrying.")
        original = manager.record(ident)
        targets = failed_rows(original, manager.entries(original), keys)
        try:
            content = json.dumps(read_json(manager.folder(ident) / "original.json"), ensure_ascii=False)
        except (OSError, ValueError):
            raise ValueError("The retained export is unavailable. Import the original JSON again.") from None
        options = original.get("options")
        if not isinstance(options, dict):
            raise ValueError("This batch lacks saved options. Use Preview resume first.")
        # A child keeps the original selection, outcome and logs available.
        child = manager.upload(
            original["filename"], content, parent_batch=original,
            retry_keys=[row["key"] for row in targets],
        )
        child_id = child["id"]
        try:
            options = {
                **options, "id": child_id,
                "ids": [row["application_id"] for row in targets],
                "rerun": False, "newRevision": False,
            }
            result = manager.preview(
                child_id, options,
                captured_routes=original.get("capturedRoutes", {}),
                runtime=manager.environments.get(ident),
            )
            if result["status"] != "planned":
                raise ValueError("Retry preview found a conflict. Open Preview resume to inspect it.")
            verify_plan(original.get("plan") or {}, result["plan"], targets)
            return result
        except Exception:
            manager.discard(child_id)
            raise


def check_start(manager, record):
    parent_id = record.get("parentBatchId")
    if not parent_id:
        return
    try:
        parent = manager.record(parent_id)
    except OSError:
        raise ValueError("The original batch was removed. Preview this import again.") from None
    targets = failed_rows(parent, manager.entries(parent), record.get("retryKeys"))
    verify_plan(parent.get("plan") or {}, record.get("plan") or {}, targets)
