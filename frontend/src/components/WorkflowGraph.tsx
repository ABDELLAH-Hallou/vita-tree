import { useRef } from "react";
import type { GraphRun, Route, Stage, StageStatus, StepId } from "../model";
export interface WorkflowGraphProps {
  stages: Stage[];
  run?: GraphRun;
  selected?: StepId;
  select: (stage: Stage) => void;
  config: Partial<Record<StepId, Route>>;
  statusNames: Record<string, string>;
  disabled?: boolean;
}

const stepSymbols: Partial<Record<StageStatus, string>> = {
  succeeded: "m5 12 4 4L19 6",
  previous: "M12 7v5l3 2m6-2a9 9 0 1 1-9-9 9 9 0 0 1 9 9",
  running: "M12 3a9 9 0 1 1-9 9",
  review: "M8 10a4 4 0 1 0 8 0 4 4 0 0 0-8 0ZM4 21a8 8 0 0 1 16 0",
  failed: "M12 5v9m0 4v.1",
  interrupted: "M9 6v12m6-12v12",
  skipped: "M6 12h12",
  unavailable: "M6 12h12",
  blocked: "M6 12h12",
};

export function formatWorkflowElapsed(seconds: number, clock = false) {
  const elapsed = Math.max(0, Math.floor(seconds));
  if (!clock) return `${elapsed}s`;
  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  return `${minutes}:${String(elapsed % 60).padStart(2, "0")}`;
}

function WorkflowProgress({
  stages,
  run,
  statusNames,
  disabled,
  focusStep,
}: Pick<WorkflowGraphProps, "stages" | "run" | "statusNames" | "disabled"> & {
  focusStep: (step: StepId) => void;
}) {
  const included = stages.filter(
    ({ status }) => !["skipped", "unavailable", "previous"].includes(status),
  );
  const recorded =
    included.length > 0 && !included.some(({ status }) => status === "unknown");
  const done = included.filter(({ status }) => status === "succeeded").length;
  const live = run?.status === "running" && !run.finishedAt;
  const attention =
    included.find(({ status }) => status === "review") ??
    included.find(({ status }) => status === "running") ??
    included.find(
      ({ status }) => status === "failed" || status === "interrupted",
    );

  return (
    <div className="workflow-progress">
      <div className="workflow-progress-label">
        <div className="workflow-progress-current">
          <strong>
            {recorded
              ? `${done} of ${included.length} ${included.length === 1 ? "step" : "steps"} done`
              : "Step progress wasn’t recorded"}
          </strong>
          {attention && (
            <button
              type="button"
              data-status={attention.status}
              disabled={disabled}
              title="Show this step in the workflow"
              onClick={() => focusStep(attention.id)}
            >
              {attention.title} ·{" "}
              {statusNames[attention.status] || attention.status}
            </button>
          )}
        </div>
        {run?.startedAt && (live || run.finishedAt) && (
          <span className="workflow-elapsed">
            <span
              className="dag-time"
              data-started-at={live ? run.startedAt : undefined}
              data-clock=""
            >
              {formatWorkflowElapsed(
                (run.finishedAt || Date.now() / 1000) - run.startedAt,
                true,
              )}
            </span>{" "}
            elapsed
          </span>
        )}
      </div>
      {recorded && (
        <progress aria-label="Steps done" value={done} max={included.length} />
      )}
    </div>
  );
}

function ApprovalGate({
  task,
  select,
  disabled,
}: {
  task: Stage;
  select: WorkflowGraphProps["select"];
  disabled: boolean;
}) {
  return (
    <button
      type="button"
      className="dag-gate"
      disabled={disabled}
      aria-haspopup="dialog"
      onClick={() => select(task)}
    >
      <svg className="dag-symbol" viewBox="0 0 24 24" aria-hidden="true">
        <path d={stepSymbols.review} />
      </svg>
      <span>
        <strong>
          {task.id === "extract"
            ? "Approve requirements"
            : task.id === "cover"
              ? "Approve cover letter"
              : "Approve CV changes"}
        </strong>
        <span>Needs you</span>
      </span>
    </button>
  );
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
  const viewport = useRef<HTMLDivElement>(null);
  const statuses = Object.fromEntries(
    stages.map(({ id, status }) => [id, status]),
  );
  const showRevision = !!statuses.adapt && !!statuses.review;
  return (
    <>
      {run && (
        <WorkflowProgress
          stages={stages}
          run={run}
          statusNames={statusNames}
          disabled={disabled}
          focusStep={(step) =>
            viewport.current
              ?.querySelector<HTMLButtonElement>(`[data-step="${step}"]`)
              ?.focus()
          }
        />
      )}
      <div className="dag" ref={viewport}>
        <div className="dag-map">
          {showRevision && (
            <div className="dag-return">
              <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path
                  d="M84 34C84 1 16 1 16 76"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
              <span>Revise CV in a new preparation</span>
            </div>
          )}
          {(["extract", "analyze"] as const).map(
            (id) =>
              statuses[id] && (
                <span
                  key={id}
                  className="dag-edge"
                  data-from={id}
                  data-status={statuses[id]}
                  aria-hidden="true"
                />
              ),
          )}
          {statuses.review && statuses.cover && (
            <>
              <svg
                className="dag-split"
                data-status={statuses.adapt}
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path
                  d="M0 50C58 50 42 25 100 25M0 50C58 50 42 75 100 75"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
              <svg
                className="dag-join"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <path
                  d="M0 25C58 25 42 50 100 50M0 75C58 75 42 50 100 50"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            </>
          )}
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
            const routing = run?.outcomes?.[task.id]?.backend?.routing;
            const effective = routing?.effective;
            const usedBackup =
              !!routing?.chain?.length &&
              routing.chain.length > 1 &&
              ((!!effective?.model &&
                effective.model !== routing.chain[0]?.model) ||
                (!!effective?.provider &&
                  effective.provider !== routing.chain[0]?.provider));
            const title = task.previousRun
              ? "This step completed in an earlier preparation. Its results were not loaded or verified for this preparation. Use Retry on that earlier preparation to check checkpoint reuse."
              : task.id === "validating"
                ? undefined
                : run
                  ? "View the AI settings captured for this step"
                  : "Configure the AI for this step";
            return (
              <div key={task.id} className="dag-stage" data-stage={task.id}>
                <button
                  type="button"
                  className="dag-node"
                  disabled={disabled}
                  data-step={task.id}
                  data-status={task.status}
                  aria-pressed={selected === task.id}
                  aria-haspopup={
                    task.id === "validating" ? undefined : "dialog"
                  }
                  aria-label={`${task.title}: ${label}. ${task.detail}`}
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
                        stepSymbols[task.status] ||
                        "M21 12a9 9 0 1 1-9-9 9 9 0 0 1 9 9"
                      }
                    />
                  </svg>
                  <span className="dag-state">
                    <span className="dag-index">Step {index + 1}</span>
                    <span className="dag-status">{label}</span>
                  </span>
                  <strong>{task.title}</strong>
                  {run?.requirementsRevision && task.id !== "validating" && (
                    <span
                      className="dag-requirements"
                      title={run.requirementsRevision}
                    >
                      Requirements {run.requirementsRevision.slice(0, 12)}
                    </span>
                  )}
                  <span className="dag-meta">
                    {route ? (
                      <span
                        className="dag-model"
                        title={
                          effective?.provider
                            ? `Used ${effective.provider} / ${effective.model || "model unreported"}${usedBackup ? " (backup)" : ""}. Requested ${route.provider} / ${route.model}`
                            : [
                                route.provider,
                                route.model,
                                route.reasoning || "Automatic reasoning",
                              ]
                                .filter(Boolean)
                                .join(" · ")
                        }
                      >
                        {(effective?.provider
                          ? effective.model ||
                            `${effective.provider} · model unreported`
                          : null) ||
                          route.model ||
                          `${route.provider} default`}
                        {usedBackup ? " · Backup" : ""}
                      </span>
                    ) : task.id === "validating" ? (
                      <span className="dag-local">No AI</span>
                    ) : null}
                    {(task.previousRun || task.startedAt) && (
                      <span
                        className="dag-time"
                        data-clock={task.status === "running" ? "" : undefined}
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
                            ? formatWorkflowElapsed(
                                (task.finishedAt || Date.now() / 1000) -
                                  task.startedAt,
                                task.status === "running",
                              )
                            : ""}
                      </span>
                    )}
                  </span>
                </button>
                {task.pendingReview && (
                  <ApprovalGate
                    task={task}
                    select={select}
                    disabled={disabled}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
