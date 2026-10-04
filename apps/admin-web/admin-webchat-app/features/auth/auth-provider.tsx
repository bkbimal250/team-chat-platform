"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { apiRequest } from "@/lib/api/client";
import { collectPages } from "@/lib/api/pagination";
import type {
  Role,
  RoleAssignment,
  Tokens,
  UserProfile,
} from "@/lib/api/contracts";
import { readSession, saveSession, clearSession } from "@/lib/auth/session";
import { canUseAdmin, memberPermissions } from "./permissions";
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
    const [roles, assignments, profile] = await Promise.all([
      collectPages<Role>("/api/v1/roles/"),
      collectPages<RoleAssignment>(
        `/api/v1/role-assignments/?member=${session.member_id}`,
      ),
      apiRequest<UserProfile>("/api/v1/users/me"),
    ]);
    if (!readSession()) return { ...initial, status: "anonymous" };
    const permissions = memberPermissions(
      session.member_id,
      roles,
      assignments,
    );
    return {
      status: canUseAdmin(permissions) ? "ready" : "denied",
      profile,
      permissions,
      error: "",
      session: readSession(),
    };
  } catch (error) {
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
