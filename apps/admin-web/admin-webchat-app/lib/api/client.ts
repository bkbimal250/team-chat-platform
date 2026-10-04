import { clearSession, readSession, saveSession } from "@/lib/auth/session";
import type { Tokens } from "./contracts";
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly code = "REQUEST_FAILED",
    public readonly fields: Record<string, string> = {},
  ) {
    super(message);
  }
}
type Options = RequestInit & {
  public?: boolean;
  query?: Record<string, string | number | undefined>;
};
let refreshing: Promise<Tokens> | null = null;
export function gatewayPath(path: string): string {
  const parsed = new URL(path, "http://gateway.local");
  if (
    !parsed.pathname.startsWith("/api/v1/") &&
    !/^\/health\/(live|ready)$/.test(parsed.pathname)
  )
    throw new ApiError("Unsupported Gateway route.");
  return parsed.pathname + parsed.search;
}
async function request<T>(
  path: string,
  options: Options,
  retry: boolean,
): Promise<T> {
  const { public: isPublic = false, query, ...init } = options;
  const route = new URL(gatewayPath(path), "http://gateway.local");
  Object.entries(query ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== "") route.searchParams.set(k, String(v));
  });
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  const session = readSession();
  if (!isPublic && session)
    headers.set("Authorization", `Bearer ${session.access_token}`);
  let response: Response;
  try {
    response = await fetch(`/api/gateway${route.pathname}${route.search}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: init.signal ?? AbortSignal.timeout(15000),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new ApiError(
      "Cannot reach GlobalChat. Check your connection and retry.",
      undefined,
      "NETWORK_ERROR",
    );
  }
  if (response.status === 401 && !isPublic && retry && session?.refresh_token) {
    refreshing ??= request<Tokens>(
      "/api/v1/auth/refresh",
      {
        public: true,
        method: "POST",
        body: JSON.stringify({ refresh_token: session.refresh_token }),
      },
      false,
    )
      .then((tokens) => {
        saveSession(tokens);
        return tokens;
      })
      .finally(() => {
        refreshing = null;
      });
    try {
      await refreshing;
    } catch (error) {
      if (
        error instanceof ApiError &&
        [401, 403, 422].includes(error.status ?? 0)
      )
        clearSession();
      throw error;
    }
    return request<T>(path, options, false);
  }
  if (response.status === 401 && !isPublic) clearSession();
  const data: unknown =
    response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const fields: Record<string, string> = {};
    let code = "REQUEST_FAILED",
      message =
        response.status === 403
          ? "You do not have permission to perform this action."
          : "Request failed. Please retry.";
    if (data && typeof data === "object") {
      const issue =
        "error" in data && data.error && typeof data.error === "object"
          ? data.error
          : data;
      if ("code" in issue && typeof issue.code === "string") code = issue.code;
      if ("message" in issue && typeof issue.message === "string")
        message = issue.message;
      if ("detail" in issue && typeof issue.detail === "string")
        message = issue.detail;
      for (const [key, value] of Object.entries(issue))
        if (Array.isArray(value) && value.every((x) => typeof x === "string"))
          fields[key] = value.join(" ");
      if (Object.keys(fields).length)
        message = Object.entries(fields)
          .map(([k, v]) => `${k}: ${v}`)
          .join("; ");
    }
    throw new ApiError(message, response.status, code, fields);
  }
  return data as T;
}
export function apiRequest<T>(path: string, options: Options = {}): Promise<T> {
  return request<T>(path, options, true);
}
export function jsonBody(value: object): RequestInit {
  return { body: JSON.stringify(value) };
}
