import {
  getAccessToken,
  readStoredSession,
  saveSession as save,
  clearSession as clear,
} from "@/lib/auth/session";
import type { Tokens } from "../api/contracts";
export function readSession(): Tokens | null {
  const access_token = getAccessToken();
  if (!access_token) return null;
  try {
    const raw = readStoredSession();
    if (!raw) return null;
    const claims = JSON.parse(
      atob(access_token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
    );
    return {
      ...raw,
      organization_id: claims.org ?? null,
      member_id: claims.mid ?? null,
    };
  } catch {
    return null;
  }
}
export function saveSession(tokens: Tokens) { save(tokens); window.dispatchEvent(new Event("globalchat:workspace-session")); }
export function clearSession() { clear(); window.dispatchEvent(new Event("globalchat:session-expired")); }
