import assert from "node:assert/strict";
import test from "node:test";
import {
  batchGroups,
  batchSummary,
  isRunningGroup,
  retryable,
} from "../src/compat/jobenu-history.js";

test("abandoned empty previews are not execution history; real failures remain visible", () => {
  const draft = {
    id: "preview",
    createdAt: 1,
    status: "selecting",
    entries: [],
  };
  const failed = {
    id: "failed",
    createdAt: 2,
    startedAt: 3,
    status: "failed",
    entries: [],
  };
  assert.deepEqual(
    batchGroups([draft, failed]).map((group) => group.batch.id),
    ["failed"],
  );
});

test("retry attempts update their rows without losing other applications or original outcomes", () => {
  const original = {
    id: "root",
    createdAt: 1,
    startedAt: 2,
    status: "failed",
    entries: [
      { key: "one", status: "failed" },
      { key: "two", status: "awaiting_approval", pending: { step: "adapt" } },
      { key: "three", status: "complete" },
    ],
  };
  const retry = {
    id: "retry",
    parentBatchId: "root",
    retryRootId: "root",
    createdAt: 3,
    startedAt: 4,
    status: "complete",
    entries: [{ key: "one", status: "complete" }],
  };
  const prepared = {
    id: "unused",
    parentBatchId: "root",
    retryRootId: "root",
    createdAt: 5,
    status: "planned",
    entries: [{ key: "one", status: "failed" }],
  };
  const groups = batchGroups([prepared, retry, original]);
  assert.equal(groups.length, 1);
  assert.deepEqual(
    groups[0].entries.map((row) => row.status),
    ["complete", "awaiting_approval", "complete"],
  );
  assert.equal(groups[0].attempts.length, 2);
  assert.equal(original.entries[0].status, "failed");
  assert.equal(
    batchSummary(groups[0], (value) => value),
    "Waiting for review",
  );
});

test("only actual failures offer retry; active attempts win over old failure summaries", () => {
  assert.equal(retryable({ status: "failed" }), true);
  for (const entry of [
    { status: "failed", pending: { step: "adapt" } },
    { status: "awaiting_approval" },
    { status: "complete" },
    { status: "running" },
  ])
    assert.equal(retryable(entry), false);
  const group = {
    entries: [{ key: "one", status: "failed" }],
    attempts: [{ status: "running" }],
  };
  assert.equal(
    batchSummary(group, (value) => value),
    "In progress",
  );
  group.attempts[0].status = "failed";
  assert.equal(
    batchSummary(group, (value) => value),
    "1 failed job",
  );
});

test("a running retry blocks its group without blocking unrelated batches", () => {
  const original = { id: "root", createdAt: 1, startedAt: 2, status: "failed", entries: [] };
  const retry = { id: "retry", parentBatchId: "root", retryRootId: "root",
    createdAt: 3, startedAt: 4, status: "running", entries: [] };
  const unrelated = { id: "other", createdAt: 5, startedAt: 6, status: "failed", entries: [] };
  const groups = batchGroups([original, retry, unrelated]);
  assert.equal(isRunningGroup(groups.find(group => group.batch.id === "root")), true);
  assert.equal(isRunningGroup(groups.find(group => group.batch.id === "other")), false);
  assert.equal(original.status, "failed");
});
