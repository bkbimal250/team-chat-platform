"use client";

import { useCallback, useEffect, useState } from "react";
import { AuthProvider as WorkspaceProvider } from "@/workspace/features/auth/auth-provider";
import { hasSession, clearSession } from "@/lib/auth/session";
import { Conversation } from "@/features/chat/api";
import { Login } from "@/features/auth/login";
import { DesktopApp } from "./layout/desktop-app";
import type { AppSection } from "./navigation/app-nav-config";

export function GlobalChatApp({
  initialSection = "chats",
  initialSettingsPage = "Profile",
}: {
  initialSection?: AppSection;
  initialSettingsPage?: string;
}) {
  const [authenticated, setAuthenticated] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [requested, setRequested] = useState<Conversation | null>(null);
  useEffect(() => {
    const timer = setTimeout(() => {
      setAuthenticated(hasSession());
      setLoaded(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);
  const signOut = useCallback(() => {
    clearSession();
    setRequested(null);
    setAuthenticated(false);
  }, []);
  const signIn = useCallback(() => setAuthenticated(true), []);
  useEffect(() => {
    window.addEventListener("globalchat:session-expired", signOut);
    return () =>
      window.removeEventListener("globalchat:session-expired", signOut);
  }, [signOut]);
  if (!loaded)
    return (
      <main className="grid min-h-dvh place-items-center bg-aurora-background">
        <p role="status" className="animate-pulse font-semibold text-aurora-primary">
          GlobalChat · Loading…
        </p>
      </main>
    );
  return authenticated ? (
    <WorkspaceProvider>
      <DesktopApp
        onSignedOut={signOut}
        requested={requested}
        initialSection={initialSection}
        initialSettingsPage={initialSettingsPage}
      />
    </WorkspaceProvider>
  ) : (
    <Login onAuthenticated={signIn} />
  );
}
