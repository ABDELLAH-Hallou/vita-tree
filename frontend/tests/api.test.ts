import test from "node:test";
import assert from "node:assert/strict";
import { QueryClient, onlineManager } from "@tanstack/react-query";
import { createApiClient } from "../src/api/client.ts";

test("GET requests deduplicate only the same branch URL and return isolated drafts", async (context) => {
  const client = new QueryClient();
  context.after(() => client.clear());
  const calls: string[] = [];
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const api = createApiClient(client, async (input) => {
    calls.push(String(input));
    await gate;
    return new Response(
      JSON.stringify({ branch: String(input), document: { text: "captured" } }),
    );
  });
  const first = api("/api/workspace?branch=one");
  const duplicate = api("/api/workspace?branch=one");
  const second = api("/api/workspace?branch=two");
  release();
  const [a, b, c] = await Promise.all([first, duplicate, second]);
  assert.equal(calls.length, 2);
  assert.equal(a.branch, b.branch);
  assert.notEqual(a.branch, c.branch);
  (a.document as { text: string }).text = "local edit";
  assert.equal((b.document as { text: string }).text, "captured");
});

test("explicit mutations preserve the session token and are never replayed or deduplicated", async (context) => {
  const client = new QueryClient();
  context.after(() => client.clear());
  const requests: RequestInit[] = [];
  const api = createApiClient(client, async (_input, init) => {
    requests.push(init || {});
    return new Response(
      JSON.stringify({
        error: "Push failed",
        commitCreated: true,
        canRetry: true,
      }),
      { status: 502 },
    );
  });
  for (let i = 0; i < 2; i++)
    await assert.rejects(
      api("/api/commit", { branch: "one" }, "fixture-token"),
      (error) => {
        assert.equal((error as Error).message, "Push failed");
        assert.equal((error as { commitCreated: boolean }).commitCreated, true);
        return true;
      },
    );
  assert.equal(requests.length, 2);
  assert.equal(
    (requests[0].headers as Record<string, string>)["X-Vita-Token"],
    "fixture-token",
  );
  assert.equal(requests[0].method, "POST");
});

test("failed reads and malformed responses fail once with actionable errors", async (context) => {
  const client = new QueryClient();
  context.after(() => client.clear());
  let calls = 0;
  const failing = createApiClient(client, async () => {
    calls++;
    return new Response("<html>Bad gateway</html>", { status: 502 });
  });
  await assert.rejects(failing("/api/jobs"), /could not be read/);
  assert.equal(calls, 1);
  const array = createApiClient(client, async () => new Response("[]"));
  await assert.rejects(array("/api/jobs"), /could not be read/);
  await assert.rejects(
    array("https://outside.invalid/api/jobs"),
    /Invalid API destination/,
  );
});

test("lint cancellation reaches the fetch request without mutation retries", async (context) => {
  const client = new QueryClient();
  context.after(() => client.clear());
  const controller = new AbortController();
  const api = createApiClient(client, async (_input, init) => {
    assert.equal(init?.signal, controller.signal);
    throw new DOMException("Cancelled", "AbortError");
  });
  await assert.rejects(
    api("/api/lint", { content: "synthetic" }, "fixture-token", {
      signal: controller.signal,
    }),
    { name: "AbortError" },
  );
});

test("a save fences earlier in-flight reads from the next workspace load", async (context) => {
  const client = new QueryClient();
  context.after(() => client.clear());
  let finishEarlier!: (value: Response) => void;
  let reads = 0;
  const api = createApiClient(client, async (_path, init) => {
    if (init?.method === "POST") return new Response('{"saved":true}');
    reads++;
    if (reads === 1)
      return new Promise((resolve) => {
        finishEarlier = resolve;
      });
    return new Response('{"revision":"new"}');
  });
  const earlier = api("/api/branch?name=one");
  await api("/api/save", { branch: "one" }, "fixture-token");
  const afterSave = api("/api/branch?name=one");
  finishEarlier(new Response('{"revision":"old"}'));
  assert.equal((await afterSave).revision, "new");
  assert.equal((await earlier).revision, "old");
  assert.equal(reads, 2);
});

test("fresh snapshots never share a capture begun before background publication", async (context) => {
  const client = new QueryClient();
  context.after(() => client.clear());
  let reads = 0;
  const api = createApiClient(
    client,
    async () => new Response(JSON.stringify({ revision: ++reads })),
  );
  const [a, b] = await Promise.all([
    api("/api/workspace?branch=one", undefined, "", { fresh: true }),
    api("/api/workspace?branch=one", undefined, "", { fresh: true }),
  ]);
  assert.notEqual(a.revision, b.revision);
  assert.equal(reads, 2);
});

test("local requests run even when the browser reports no internet connection", async (context) => {
  const client = new QueryClient();
  context.after(() => {
    onlineManager.setOnline(true);
    client.clear();
  });
  onlineManager.setOnline(false);
  const api = createApiClient(
    client,
    async () => new Response('{"local":true}'),
  );
  assert.equal((await api("/api/jobs")).local, true);
  assert.equal(
    (await api("/api/save", { branch: "one" }, "fixture-token")).local,
    true,
  );
});
