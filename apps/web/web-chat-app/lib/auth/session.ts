const key = "globalchat.session";
type Session = { access_token: string; refresh_token: string | null };

function canUseStorage() {
  return typeof window !== "undefined";
}

/** Persist until explicit logout (survives browser restarts; per-origin). */
function readRaw(): string | null {
  if (!canUseStorage()) return null;
  const fromLocal = localStorage.getItem(key);
  if (fromLocal) return fromLocal;
  const fromSession = sessionStorage.getItem(key);
  if (fromSession) {
    localStorage.setItem(key, fromSession);
    sessionStorage.removeItem(key);
    return fromSession;
  }
  return null;
}

export function readStoredSession(): Session | null {
  try {
    const raw = readRaw();
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function saveSession(tokens: Session) {
  if (!canUseStorage()) return;
  localStorage.setItem(key, JSON.stringify(tokens));
  sessionStorage.removeItem(key);
}

export function hasSession() {
  return Boolean(readRaw());
}

export function clearSession() {
  if (!canUseStorage()) return;
  localStorage.removeItem(key);
  sessionStorage.removeItem(key);
}

export function getAccessToken(): string | null {
  return readStoredSession()?.access_token ?? null;
}

export function getMemberId(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const claims = JSON.parse(
      atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
    ) as { mid?: string; org?: string; sub?: string };
    return claims.mid ?? (!claims.org ? claims.sub ?? null : null);
  } catch {
    return null;
  }
}
