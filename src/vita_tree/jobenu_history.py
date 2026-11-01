"""Read-only workspace history from native Jobenu evidence, not Tree checkpoints."""

import hashlib
import json
import re
from pathlib import Path

from .fileio import atomic_write_bytes

STEPS = ("extract", "analyze", "adapt", "review", "cover", "validating")
ROUTE_FIELDS = ("provider", "model", "reasoning")
HISTORY_FIELDS = (
    "id",
    "source",
    "branch",
    "status",
    "step",
    "createdAt",
    "startedAt",
    "finishedAt",
    "elapsedSeconds",
    "reviewed",
    "stages",
    "stepConfig",
    "resumeAvailable",
    "attempt",
    "nativeBatchId",
    "nativeKey",
    "language",
    "message",
)


def pending_decision(manager, row):
    pending = row.get("pending") or {}
    if pending.get("step") not in {"adapt", "cover"} or not row.get("workspace"):
        return None
    from .workspace import safe_path
    from .jobenu import read_json

    try:
        root = safe_path(manager.ws.repository, ".vita/imports/jobenu/worktrees")
        path = Path(row["workspace"])
        relative = path.relative_to(root)
        workspace = safe_path(root, relative.as_posix())
        report = read_json(
            safe_path(workspace, ".vita/results/" + pending["step"] + ".facts.json")
        )
        if report.get("revision") != pending.get("revision"):
            return None
        if report.get("status") == "rejected":
            return "rejected"
        if (
            report.get("status") in {"approved", "applied"}
            and report.get("application_status") == "applied"
        ):
            return "applied"
    except (OSError, ValueError, TypeError):
        return None


def project(record, row, active, decision):
    """Project recorded evidence only; absence never means a step succeeded."""
    attempt = record.get("attempt")
    ident = hashlib.sha256(
        json.dumps(
            [record["id"], row.get("key"), row.get("fingerprint"), attempt]
        ).encode()
    ).hexdigest()[:32]
    native_status = row.get("status", "unknown")
    pending_step = (row.get("pending") or {}).get("step")
    waiting = native_status in {"awaiting_approval", "awaiting_requirements_approval"}
    resolved = decision == "applied"
    status = (
        ("awaiting_resume" if resolved else "awaiting_review")
        if waiting
        else {
            "complete": "succeeded",
            "failed": "failed",
            "rejected": "failed",
            "running": "running" if active else "interrupted",
            "preparing": "running" if active else "interrupted",
            "imported": "imported",
        }.get(native_status, "interrupted")
    )
    completed = set(row.get("completed_steps") or [])
    if decision == "rejected":
        status = "failed"
    if resolved:
        completed.add(pending_step)
    current = row.get("current_step")
    stages = []
    for step in STEPS:
        state = "unknown"
        if step in completed:
            state = "succeeded"
        elif step == pending_step and decision == "rejected":
            state = "failed"
        elif (
            waiting
            and not resolved
            and (
                step == pending_step
                or step == "extract"
                and native_status == "awaiting_requirements_approval"
            )
        ):
            state = "review"
        elif step == current:
            state = (
                "running"
                if status == "running"
                else "failed"
                if status == "failed"
                else "interrupted"
            )
        elif isinstance(row.get("steps"), list) and step not in row["steps"]:
            state = "unknown" if step == "validating" else "skipped"
        stages.append({"id": step, "status": state})
    routes = {
        step: {
            key: value
            for key, value in route.items()
            if key in ROUTE_FIELDS and isinstance(value, str)
        }
        for step, route in (record.get("capturedRoutes") or {}).items()
        if step in STEPS
        and isinstance(route, dict)
        and any(route.get(key) for key in ROUTE_FIELDS)
    }
    override = (record.get("plan") or {}).get("provider")
    if isinstance(override, str) and override:
        for step in STEPS[:-1]:
            if step == "extract":
                continue
            route = routes.setdefault(step, {})
            if route.get("provider") and route["provider"] != override:
                route.pop("model", None)
            route["provider"] = override
    return dict(
        id=ident,
        source="jobenu",
        branch=row["branch"],
        status=status,
        step="completed" if status == "succeeded" else status,
        createdAt=record.get("startedAt") or record.get("createdAt") or 0,
        startedAt=None,
        finishedAt=record.get("finishedAt"),
        elapsedSeconds=0,
        reviewed=True,
        stages=stages,
        stepConfig=routes,
        resumeAvailable=False,
        attempt=attempt,
        nativeBatchId=record["id"],
        nativeKey=row.get("key"),
        language=(record.get("plan") or {}).get("language"),
        message="Jobenu import · "
        + {
            "succeeded": "Recorded AI stages completed. Final checks and PDFs are separate.",
            "awaiting_resume": "Changes approved and applied. Return to Import jobs to preview resume.",
            "awaiting_review": "Review the pending proposal in Import jobs before continuing.",
        }.get(
            status,
            "Native component history. Use Import jobs for execution logs and continuation.",
        )
        + " Unrecorded steps and AI settings are shown as unknown.",
    )


def history(manager, branch=None):
    from .jobenu import read_json
    from .workspace import safe_path

    folder = safe_path(manager.ws.root, "jobenu-history")
    records = {}
    # Do not acquire the process/decision lock while Workspace.snapshot holds
    # the workspace lock: native start and review acquire those in reverse order.
    with manager.history_lock:
        for path in folder.glob("*.json"):
            if not re.fullmatch("[a-f0-9]{32}", path.stem):
                continue
            try:
                record = read_json(path)
                if record.get("id") == path.stem and record.get("source") == "jobenu":
                    if not isinstance(record.get("stages"), list) or not isinstance(
                        record.get("stepConfig"), dict
                    ):
                        continue
                    record = {
                        key: value
                        for key, value in record.items()
                        if key in HISTORY_FIELDS
                    }
                    record["stages"] = [
                        dict(id=stage["id"], status=stage["status"])
                        for stage in record["stages"]
                        if isinstance(stage, dict)
                        and stage.get("id") in STEPS
                        and stage.get("status")
                        in {
                            "unknown",
                            "review",
                            "succeeded",
                            "failed",
                            "running",
                            "interrupted",
                            "skipped",
                        }
                    ]
                    record["stepConfig"] = {
                        step: {
                            key: value
                            for key, value in route.items()
                            if key in ROUTE_FIELDS and isinstance(value, str)
                        }
                        for step, route in record["stepConfig"].items()
                        if step in STEPS and isinstance(route, dict)
                    }
                    records[path.stem] = manager.clean_report(record, {})
            except (OSError, ValueError):
                continue
        for path in manager.root.glob("*/session.json"):
            try:
                batch = manager.record(path.parent.name)
                if batch.get("status") in {
                    "planned",
                    "selecting",
                    "conflict",
                } or not batch.get("startedAt"):
                    continue
                for row in manager.entries(batch):
                    if not isinstance(row.get("branch"), str):
                        continue
                    if branch is not None and row["branch"] != branch:
                        continue
                    record = manager.clean_report(
                        project(
                            batch,
                            row,
                            batch["id"] in manager.running,
                            pending_decision(manager, row),
                        ),
                        {},
                    )
                    if records.get(record["id"]) != record:
                        try:
                            atomic_write_bytes(
                                folder / (record["id"] + ".json"),
                                json.dumps(record).encode(),
                            )
                        except OSError as error:
                            manager.ws.diagnostics.error(
                                "jobenu_history_write_failed",
                                error,
                                operation="jobenu_history",
                            )
                    records[record["id"]] = record
            except (OSError, ValueError, TypeError):
                continue
        return sorted(
            (
                record
                for record in records.values()
                if branch is None or record.get("branch") == branch
            ),
            key=lambda record: record.get("createdAt") or 0,
            reverse=True,
        )
