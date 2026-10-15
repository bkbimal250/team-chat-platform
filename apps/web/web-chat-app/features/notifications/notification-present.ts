import type { Notice } from "./types";

export function noticeTitle(row: Notice) {
  if (row.preview_mode === "NONE") return "Workspace notification";
  return row.title || "Workspace notification";
}

export function noticeDescription(row: Notice) {
  if (row.preview_mode === "FULL" && row.body) return row.body;
  if (row.preview_mode === "NONE") return "Open to view in conversation";
  return "Tap to open the related chat";
}

export function noticeTime(row: Notice) {
  if (!row.created_at) return undefined;
  const date = new Date(row.created_at);
  if (Number.isNaN(date.getTime())) return undefined;
  const now = Date.now();
  const diff = now - date.getTime();
  if (diff < 60_000) return "Just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}
