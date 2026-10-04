import type { Tokens } from "@/lib/api/contracts";
const key = "globalchat.admin.session";
let memory: Tokens | null = null;
export function readSession(): Tokens | null {
  if (memory) return memory;
  if (typeof window === "undefined") return null;
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(key) ?? "null");
    if (
      value &&
      typeof value === "object" &&
      "access_token" in value &&
      typeof value.access_token === "string" &&
      "member_id" in value &&
      typeof value.member_id === "string"
    )
      memory = value as Tokens;
  } catch {
    sessionStorage.removeItem(key);
  }
  return memory;
}
export function saveSession(tokens: Tokens) {
  memory = tokens;
  if (typeof window !== "undefined") {
    sessionStorage.setItem(key, JSON.stringify(tokens));
    window.dispatchEvent(new Event("globalchat:admin-session"));
  }
}
export function clearSession() {
  memory = null;
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(key);
    window.dispatchEvent(new Event("globalchat:admin-session"));
  }
}
