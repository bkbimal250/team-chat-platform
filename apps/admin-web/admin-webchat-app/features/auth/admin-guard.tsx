"use client";

import { useEffect, useState } from "react";

import { useRouter } from "next/navigation";

import { useAuth } from "./auth-provider";

import { Button } from "@/components/ui/button";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const router = useRouter();
  const [logoutError, setLogoutError] = useState<string | null>(null);

  useEffect(() => {
    if (auth.status === "anonymous") router.replace("/login");
  }, [auth.status, router]);

  if (auth.status === "loading" || auth.status === "anonymous")
    return (
      <main role="status" className="p-12 text-center">
        Validating admin session…
      </main>
    );

  if (auth.status === "denied" || auth.status === "error")
    return (
      <main className="mx-auto max-w-lg space-y-4 p-12">
        <h1 className="text-2xl font-semibold">
          {auth.status === "denied"
            ? "Platform administration unavailable"
            : "Session validation unavailable"}
        </h1>
        <p role="alert">
          {auth.error ||
            "This account has no active GlobalChat platform grant. Company ownership does not grant platform access."}
        </p>
        {logoutError && <p role="alert">{logoutError}</p>}
        <Button onClick={() => void auth.reload()}>Retry</Button>
        <Button
          variant="outline"
          onClick={() =>
            void auth
              .logout()
              .catch(() =>
                setLogoutError(
                  "Sign out could not be confirmed. Please retry.",
                ),
              )
          }
        >
          Sign out
        </Button>
      </main>
    );

  return children;
}
