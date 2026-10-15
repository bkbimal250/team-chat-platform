"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { ApiError, apiRequest } from "@/lib/api/client";
import type {
  Tokens,
  UserProfile,
} from "@/lib/api/contracts";
import { readSession, saveSession, clearSession } from "@/lib/auth/session";
import { canUseAdmin } from "./permissions";
type AuthState = {
  status: "loading" | "anonymous" | "ready" | "denied" | "error";
  profile: UserProfile | null;
  permissions: Set<string>;
  error: string;
  session: Tokens | null;
};
const initial: AuthState = {
  status: "loading",
  profile: null,
  permissions: new Set(),
  error: "",
  session: null,
};
async function loadSession(): Promise<AuthState> {
  const session = readSession();
  if (!session) return { ...initial, status: "anonymous" };
  try {
    await apiRequest("/api/v1/auth/me");
    const grant = await apiRequest<{
      identity_id: string;
      role: string;
      permissions: string[];
    }>("/api/v1/platform/me");
    if (!readSession()) return { ...initial, status: "anonymous" };
    const permissions = new Set(Array.isArray(grant.permissions) ? grant.permissions : []);
    return {
      status: canUseAdmin(permissions) ? "ready" : "denied",
      profile: null,
      permissions,
      error: "",
      session: readSession(),
    };
  } catch (error) {
    if (error instanceof ApiError && error.status === 403)
      return { ...initial, status: "denied", session: readSession() };
    return {
      ...initial,
      status: readSession() ? "error" : "anonymous",
      session: readSession(),
      error:
        error instanceof Error ? error.message : "Could not validate session.",
    };
  }
}
const Context = createContext<
  | (AuthState & {
      login: (tokens: Tokens) => Promise<void>;
      logout: () => Promise<void>;
      reload: () => Promise<void>;
    })
  | null
>(null);
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState(initial);
  const reload = useCallback(async () => {
    setState({ ...initial, status: "loading" });
    setState(await loadSession());
  }, []);
  useEffect(() => {
    let active = true;
    const handler = () => {
      if (!readSession()) setState({ ...initial, status: "anonymous" });
    };
    window.addEventListener("globalchat:admin-session", handler);
    loadSession().then((next) => {
      if (active) setState(next);
    });
    return () => {
      active = false;
      window.removeEventListener("globalchat:admin-session", handler);
    };
  }, []);
  const login = async (tokens: Tokens) => {
    saveSession(tokens);
    await reload();
  };
  const logout = async () => {
    await apiRequest("/api/v1/auth/logout", { method: "POST", body: "{}" });
    clearSession();
  };
  return (
    <Context.Provider value={{ ...state, login, logout, reload }}>
      {children}
    </Context.Provider>
  );
}
export function useAuth() {
  const value = useContext(Context);
  if (!value) throw new Error("AuthProvider required");
  return value;
}
