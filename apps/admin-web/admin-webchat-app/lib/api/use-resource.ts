"use client";
import { useCallback, useEffect, useState } from "react";
import { ADMIN_REFRESH, refreshMatches } from "@/lib/realtime/refresh";
import { apiRequest } from "./client";
export function useResource<T>(path: string, enabled = true) {
  const [result, setResult] = useState<{
    key: string;
    data: T | null;
    error: string;
  }>({ key: "", data: null, error: "" });
  const [version, setVersion] = useState(0);
  const key = path + "#" + version;
  const reload = useCallback(() => setVersion((v) => v + 1), []);
  useEffect(() => {
    const handler = (event: Event) => { if (enabled && refreshMatches(path, (event as CustomEvent).detail)) reload(); };
    window.addEventListener(ADMIN_REFRESH, handler);
    return () => window.removeEventListener(ADMIN_REFRESH, handler);
  }, [path, reload, enabled]);
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    apiRequest<T>(path, { signal: controller.signal })
      .then((data) => {
        if (!controller.signal.aborted) setResult({ key, data, error: "" });
      })
      .catch((e) => {
        if (!controller.signal.aborted)
          setResult({
            key,
            data: null,
            error: e instanceof Error ? e.message : "Request failed.",
          });
      });
    return () => controller.abort();
  }, [path, key, enabled]);
  // Preserve the authoritative last result during background reconciliation.
  // A different path (filters, tenant or cursor) still gets a fresh loading state.
  const sameResource = result.key.startsWith(path + "#");
  return {
    data: sameResource ? result.data : null,
    error: sameResource ? result.error : "",
    loading: enabled && !sameResource,
    refreshing: enabled && result.key !== key,
    reload,
  };
}
