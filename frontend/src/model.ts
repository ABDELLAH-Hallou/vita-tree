export type StepId =
  "extract" | "analyze" | "adapt" | "review" | "cover" | "validating";
export type StageStatus =
  | "pending"
  | "running"
  | "succeeded"
  | "failed"
  | "blocked"
  | "interrupted"
  | "skipped"
  | "unavailable"
  | "unknown"
  | "review"
  | "previous";
export interface Stage {
  id: StepId;
  status: StageStatus;
  title: string;
  detail: string;
  output: string;
  startedAt?: number;
  finishedAt?: number;
  reusedFrom?: string;
  previousRun?: string;
}
export interface Route {
  provider?: string;
  model?: string;
  reasoning?: string;
  connection?: string;
}
export interface GraphRun {
  id: string;
  source?: "jobenu";
  requirementsRevision?: string;
  requirementsStatus?: string;
  requirementsApprovalNeeded?: boolean;
  factualReview?: { state: string; step: string };
}
export interface Branch {
  name: string;
  displayName?: string;
  local: boolean;
  subject: string;
  author: string;
  modifiedAt: string;
  timestamp: number;
}
export interface ApplicationRow {
  branch: Branch;
  selected: boolean;
  selectable: boolean;
  status?: string;
  label?: string;
  failure?: string;
}
