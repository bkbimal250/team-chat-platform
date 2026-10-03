const key = "globalchat.session";
type Session = { access_token: string; refresh_token: string | null };
export function saveSession(tokens: Session) {
  sessionStorage.setItem(key, JSON.stringify(tokens));
}
export function hasSession() {
  return typeof window !== "undefined" && Boolean(sessionStorage.getItem(key));
}
export function clearSession() {
  sessionStorage.removeItem(key);
}
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return (
      (JSON.parse(sessionStorage.getItem(key) ?? "null") as Session | null)
        ?.access_token ?? null
    );
  } catch {
    return null;
  }
}
export function getMemberId(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    return (
      (
        JSON.parse(
          atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")),
        ) as { mid?: string }
      ).mid ?? null
    );
  } catch {
    return null;
  }
}
