"use client";
import { useAdminConnection } from "@/features/admin/live-provider";
export function RealtimeStatus() {
 const state = useAdminConnection();
 if (state === "connected" || state === "not-configured") return null;
 return <span role="status" className="text-xs text-amber-700">{state === "offline" ? "Offline — changes will sync when connected" : state === "connecting" ? "Connecting…" : "Reconnecting…"}</span>;
}
