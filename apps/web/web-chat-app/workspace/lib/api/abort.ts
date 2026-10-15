export function isAbortError(error: unknown): boolean {
  if (!error) return false;
  if (error instanceof DOMException && error.name === "AbortError") return true;
  if (error instanceof Error && error.name === "AbortError") return true;
  if (typeof error === "object" && "name" in error && error.name === "AbortError")
    return true;
  if (
    error instanceof Error &&
    /aborted|AbortError/i.test(error.message)
  )
    return true;
  return false;
}

/** Cancel in-flight fetches without surfacing dev-runtime AbortError overlays. */
export function safeAbort(
  controller: AbortController | null | undefined,
  reason = "cancelled",
) {
  if (!controller || controller.signal.aborted) return;
  try {
    controller.abort(reason);
  } catch {
    /* Some runtimes throw synchronously when aborting; ignore. */
  }
}
