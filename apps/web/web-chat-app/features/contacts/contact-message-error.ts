import { ApiError } from "@/workspace/lib/api/client";

const FALLBACK_MESSAGE =
  "This contact is unavailable for messaging. Check discoverability and try again.";

export function contactMessageError(issue: unknown): string {
  if (issue instanceof ApiError && issue.status === 403) return issue.message;
  return FALLBACK_MESSAGE;
}
