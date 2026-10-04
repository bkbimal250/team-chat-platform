"use client";
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "./client";
export function useResource<T>(path: string) {
  const [result, setResult] = useState<{
    key: string;
    data: T | null;
    error: string;
  }>({ key: "", data: null, error: "" });
  const [version, setVersion] = useState(0);
  const key = path + "#" + version;
  const reload = useCallback(() => setVersion((v) => v + 1), []);
  useEffect(() => {
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
  }, [path, key]);
  return {
    data: result.key === key ? result.data : null,
    error: result.key === key ? result.error : "",
    loading: result.key !== key,
    reload,
  };
}
