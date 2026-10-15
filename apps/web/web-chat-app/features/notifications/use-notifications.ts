"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/workspace/lib/api/client";
import { isAbortError, safeAbort } from "@/workspace/lib/api/abort";
import { ADMIN_REFRESH, refreshMatches } from "@/workspace/lib/realtime/refresh";
import type { Notice } from "./types";

const PAGE_SIZE = 20;

export function useNotifications(page: number, enabled = true) {
  const [rows, setRows] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  const reload = useCallback(() => setRetry((v) => v + 1), []);

  useEffect(() => {
    const handler = (event: Event) => {
      if (enabled && refreshMatches("/api/v1/notifications", (event as CustomEvent).detail)) {
        reload();
      }
    };
    window.addEventListener(ADMIN_REFRESH, handler);
    return () => window.removeEventListener(ADMIN_REFRESH, handler);
  }, [enabled, reload]);

  useEffect(() => {
    if (!enabled) {
      const reset = window.setTimeout(() => { setLoading(false); setRows([]); setError(""); }, 0);
      return () => window.clearTimeout(reset);
    }

    const abort = new AbortController();
    const startRequest = window.setTimeout(() => {
    setLoading(true);
    setError("");
    apiRequest<Notice[]>(
      `/api/v1/notifications?limit=${PAGE_SIZE}&offset=${page * PAGE_SIZE}`,
      { signal: abort.signal },
    )
      .then((result) => {
        if (abort.signal.aborted) return;
        setRows(Array.isArray(result) ? result : []);
        setError("");
      })
      .catch((e) => {
        if (abort.signal.aborted || isAbortError(e)) return;
        setError(
          e instanceof ApiError && e.status === 503
            ? "Notifications are temporarily unavailable. Is the notification service running?"
            : e instanceof ApiError
              ? e.message
              : "Notifications could not be loaded.",
        );
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoading(false);
      });

    }, 0);
    return () => {
      window.clearTimeout(startRequest);
      safeAbort(abort);
    };
  }, [page, retry, enabled]);

  return {
    rows,
    loading,
    error,
    page,
    pageSize: PAGE_SIZE,
    hasPrev: page > 0,
    hasNext: rows.length >= PAGE_SIZE,
    reload,
  };
}
