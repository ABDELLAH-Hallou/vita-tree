import { QueryClient } from "@tanstack/react-query";

export type JsonObject = Record<string, unknown>;
export type Fetcher = typeof fetch;
export interface RequestOptions {
  signal?: AbortSignal;
  fresh?: boolean;
}

export function objectResponse(value: unknown): JsonObject {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(
      "The server returned an invalid response. Refresh and try again.",
    );
  }
  return value as JsonObject;
}

export function createApiClient(
  client: QueryClient,
  fetcher: Fetcher = globalThis.fetch,
) {
  let epoch = 0;
  let freshRead = 0;
  async function send(
    path: string,
    data: unknown,
    token: string,
    signal?: AbortSignal,
  ) {
    if (!path.startsWith("/api/") || path.startsWith("//"))
      throw new Error("Invalid API destination.");
    const response = await fetcher(
      path,
      data === undefined
        ? { cache: "no-store", signal }
        : {
            method: "POST",
            signal,
            headers: {
              "Content-Type": "application/json",
              "X-Vita-Token": token,
            },
            body: JSON.stringify(data),
          },
    );
    let value: JsonObject;
    try {
      value = objectResponse(await response.json());
    } catch {
      throw new Error(
        "The server response could not be read. Check the connection and refresh.",
      );
    }
    if (!response.ok) {
      throw Object.assign(
        new Error(
          typeof value.error === "string"
            ? value.error
            : `Request failed (${response.status})`,
        ),
        value,
      );
    }
    return value;
  }
  return async function request(
    path: string,
    data?: unknown,
    token = "",
    options: RequestOptions = {},
  ): Promise<JsonObject> {
    const { signal, fresh } = options;
    // Reads are deduplicated by the full branch-specific URL. A caller gets its
    // own draft so editor changes cannot mutate cached server evidence.
    if (data === undefined && !signal) {
      const value = await client.fetchQuery({
        queryKey: ["vita", path, epoch, fresh ? ++freshRead : 0],
        queryFn: () => send(path, undefined, token),
        staleTime: 0,
        retry: false,
        networkMode: "always",
        gcTime: 60_000,
      });
      return structuredClone(value);
    }
    if (signal) return send(path, data, token, signal);
    // User actions, approval decisions and paid work are never automatically
    // retried, deduplicated or replayed by the data library.
    epoch++;
    const mutation = client.getMutationCache().build(client, {
      mutationFn: () => send(path, data, token),
      retry: false,
      networkMode: "always",
      gcTime: 60_000,
    });
    // An earlier read must never satisfy a reload after a write, including a
    // failed push that still created a local commit. Do not cancel its caller.
    try {
      return await mutation.execute(undefined);
    } finally {
      epoch++;
    }
  };
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
});
export const apiRequest = createApiClient(queryClient);
