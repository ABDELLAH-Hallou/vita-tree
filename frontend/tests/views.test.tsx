import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import { ApplicationList } from "../src/components/ApplicationList";
import { WorkflowGraph } from "../src/components/WorkflowGraph";

test("a withheld effective model is not replaced with the old primary model", () => {
  const html = renderToStaticMarkup(
    <WorkflowGraph
      stages={[
        {
          id: "analyze",
          title: "Check CV match",
          detail: "Compare",
          output: "Analysis",
          status: "succeeded",
        },
      ]}
      run={{
        id: "run",
        outcomes: {
          analyze: {
            backend: {
              routing: {
                effective: { provider: "gemini" },
                chain: [
                  { provider: "openai", model: "old-primary" },
                  { provider: "gemini" },
                ],
              },
            },
          },
        },
      }}
      config={{ analyze: { provider: "openai", model: "old-primary" } }}
      statusNames={{ succeeded: "Done" }}
      select={() => {}}
    />,
  );
  assert.match(html, />gemini · model unreported/);
});

test("workflow graph shows the effective backup model without rewriting captured configuration", () => {
  const html = renderToStaticMarkup(
    <WorkflowGraph
      stages={[
        {
          id: "analyze",
          title: "Check CV match",
          detail: "Compare CV",
          output: "Analysis",
          status: "succeeded",
        },
      ]}
      run={{
        id: "run",
        outcomes: {
          analyze: {
            backend: {
              routing: {
                effective: { provider: "gemini", model: "backup-model" },
                chain: [
                  { provider: "openai", model: "primary-model" },
                  { provider: "gemini", model: "backup-model" },
                ],
              },
            },
          },
        },
      }}
      config={{ analyze: { provider: "openai", model: "primary-model" } }}
      statusNames={{ succeeded: "Done" }}
      select={() => {}}
    />,
  );
  assert.match(html, /backup-model.*Backup/);
  assert.match(html, /Requested openai \/ primary-model/);
});

test("application identities, disabled selection and untrusted labels survive React rendering", () => {
  const html = renderToStaticMarkup(
    <ApplicationList
      rows={[
        {
          branch: {
            name: "application-a",
            displayName: "<script>CV & role</script>",
            local: true,
            subject: "Saved <img src=x>",
            author: "Synthetic author",
            modifiedAt: "2026-01-01",
            timestamp: 1,
          },
          selected: false,
          selectable: false,
          status: "review",
          label: "Needs review",
          failure: "<svg onload=alert(1)>",
        },
      ]}
      empty="Nothing here"
      onOpen={() => {}}
      onSelect={() => {}}
      relative={() => "1d ago"}
    />,
  );
  assert.match(html, /data-branch="application-a"/);
  assert.match(html, /disabled=""/);
  assert.match(
    html,
    /aria-label="Open &lt;script&gt;CV &amp; role&lt;\/script&gt;"/,
  );
  assert.ok(!html.includes("<script>"));
  assert.ok(!html.includes("<img"));
  assert.ok(!html.includes("<svg onload"));
  assert.match(html, /Needs review/);
});

test("workflow retains native review state, captured route and historical evidence", () => {
  const html = renderToStaticMarkup(
    <WorkflowGraph
      stages={[
        {
          id: "extract",
          status: "succeeded",
          title: "Identify job requirements",
          detail: "Verified definition",
          output: "Job requirements",
        },
        {
          id: "adapt",
          status: "previous",
          title: "Tailor CV",
          detail: "Earlier preparation",
          output: "main.tex",
          previousRun: "earlier-run",
        },
      ]}
      run={{
        id: "run",
        requirementsRevision: "abcdef1234567890",
        requirementsApprovalNeeded: true,
      }}
      selected="adapt"
      select={() => {}}
      config={{
        adapt: {
          provider: "gemini",
          model: "captured-model",
          reasoning: "high",
        },
      }}
      statusNames={{ succeeded: "Done", previous: "Done earlier" }}
    />,
  );
  assert.match(html, /Needs requirements review/);
  assert.match(html, /Historical result · not loaded/);
  assert.match(html, /captured-model/);
  assert.match(html, /Requirements abcdef123456/);
  assert.match(
    html,
    /data-step="adapt" data-status="previous" aria-pressed="true"/,
  );
  assert.match(html, /Its results were not loaded or verified/);
});
