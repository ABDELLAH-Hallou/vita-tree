import type { GraphRun, Route, Stage, StepId } from "../model";
export interface WorkflowGraphProps {
  stages: Stage[];
  run?: GraphRun;
  selected?: StepId;
  select: (stage: Stage) => void;
  config: Partial<Record<StepId, Route>>;
  statusNames: Record<string, string>;
  disabled?: boolean;
}
export function WorkflowGraph({
  stages,
  run,
  selected,
  select,
  config,
  statusNames,
  disabled = false,
}: WorkflowGraphProps) {
  return (
    <>
      {stages.map((task, index) => {
        let label =
          (statusNames[task.status] || task.status) +
          (task.reusedFrom ? " · reused" : "");
        if (run?.factualReview?.step === task.id)
          label =
            (
              {
                pending: "Needs factual review",
                resolved: "Factual decisions saved",
                unavailable: "Review unavailable",
              } as Record<string, string>
            )[run.factualReview.state] || "Review unavailable";
        if (task.id === "extract" && run?.requirementsApprovalNeeded)
          label = "Needs requirements review";
        if (
          ["analyze", "adapt", "review", "cover"].includes(task.id) &&
          task.status === "succeeded" &&
          run?.requirementsStatus &&
          run.requirementsStatus !== "current"
        )
          label += " · requirements changed";
        const route = config[task.id];
        const title = task.previousRun
          ? "This step completed in an earlier preparation. Its results were not loaded or verified for this preparation. Use Retry on that earlier preparation to check checkpoint reuse."
          : task.id === "validating"
            ? undefined
            : run
              ? "View the AI settings captured for this step"
              : "Configure the AI for this step";
        return (
          <span key={task.id} className="workflow-stage-group">
            {index > 0 && (
              <span
                className="dag-edge"
                aria-hidden="true"
                data-status={stages[index - 1].status}
              >
                →
              </span>
            )}
            <button
              type="button"
              className="dag-node"
              disabled={disabled}
              data-step={task.id}
              data-status={task.status}
              aria-pressed={selected === task.id}
              aria-haspopup={task.id === "validating" ? undefined : "dialog"}
              aria-label={`${task.title}: ${statusNames[task.status] || task.status}. ${task.detail}`}
              title={title}
              onClick={() => select(task)}
              onFocus={(event) => {
                const target = event.currentTarget;
                requestAnimationFrame(() => {
                  if (document.activeElement === target)
                    target.scrollIntoView({
                      block: "nearest",
                      inline: "nearest",
                    });
                });
              }}
            >
              <svg
                className="dag-symbol"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  d={
                    ["succeeded", "previous"].includes(task.status)
                      ? "m5 12 4 4L19 6"
                      : ["failed", "interrupted"].includes(task.status)
                        ? "M12 5v9m0 4v.1"
                        : ["skipped", "unavailable", "blocked"].includes(
                              task.status,
                            )
                          ? "M6 12h12"
                          : "M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9"
                  }
                />
              </svg>
              <strong>{task.title}</strong>
              <span className="dag-status">{label}</span>
              <span
                className="dag-time"
                data-started-at={
                  task.startedAt &&
                  !task.finishedAt &&
                  task.status === "running"
                    ? task.startedAt
                    : undefined
                }
              >
                {task.previousRun
                  ? "Historical result · not loaded"
                  : task.startedAt
                    ? `${Math.max(0, Math.floor((task.finishedAt || Date.now() / 1000) - task.startedAt))}s`
                    : task.output}
              </span>
              {run?.requirementsRevision && task.id !== "validating" && (
                <span
                  className="dag-requirements"
                  title={run.requirementsRevision}
                >
                  Requirements {run.requirementsRevision.slice(0, 12)}
                </span>
              )}
              {route && (
                <span
                  className="dag-model"
                  title={`${route.provider} · ${route.reasoning || "Automatic reasoning"}`}
                >
                  {route.model || `${route.provider} default`}
                </span>
              )}
            </button>
          </span>
        );
      })}
    </>
  );
}
