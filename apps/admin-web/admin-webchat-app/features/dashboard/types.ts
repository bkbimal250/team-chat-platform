export type Status = "active" | "inactive" | "pending" | "suspended" | "online" | "away" | "offline" | "operational" | "degraded" | "unavailable" | "failed";
export type Metric = { label: string; value: string; change: string };
export type Member = { name: string; email: string; organization: string; role: string; status: Status; joined: string };
export type Health = { name: string; status: Status; latency: string };
