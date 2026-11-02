// Retry attempts share a batch view; the original applications remain visible.
export function batchGroups(batches) {
  const byId = new Map(batches.map((batch) => [batch.id, batch]));
  const groups = new Map();
  for (const batch of batches) {
    if (batch.parentBatchId && !batch.startedAt) continue;
    const rootId = batch.retryRootId || batch.id;
    if (!groups.has(rootId)) {
      groups.set(rootId, { batch: byId.get(rootId) || batch, attempts: [] });
    }
    groups.get(rootId).attempts.push(batch);
  }
  return [...groups.values()]
    .map((group) => {
      group.attempts.sort(
        (a, b) => (a.startedAt || a.createdAt) - (b.startedAt || b.createdAt),
      );
      const entries = new Map();
      for (const attempt of group.attempts) {
        for (const entry of attempt.entries)
          entries.set(entry.key || entry.branch, entry);
      }
      return { ...group, entries: [...entries.values()] };
    })
    .sort((a, b) => b.batch.createdAt - a.batch.createdAt);
}

export function retryable(entry) {
  return entry.status === "failed" && !entry.pending;
}

export function batchSummary(group, statusLabel) {
  if (group.attempts.some((attempt) => attempt.status === "running"))
    return "In progress";
  const failed = group.entries.filter(retryable).length;
  const waiting = group.entries.filter(
    (entry) =>
      entry.pending || entry.status === "awaiting_requirements_approval",
  ).length;
  if (failed)
    return `${failed} failed job${failed === 1 ? "" : "s"}${waiting ? ` · ${waiting} waiting for review` : ""}`;
  if (waiting) return "Waiting for review";
  return statusLabel(group.attempts.at(-1)?.status);
}
