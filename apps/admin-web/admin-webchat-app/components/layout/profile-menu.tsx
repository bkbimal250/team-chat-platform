"use client";

import Link from "next/link";

import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/features/auth/auth-provider";

import { Button } from "@/components/ui/button";

export function ProfileMenu() {
  const auth = useAuth();
  const [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const ref=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(!open)return;const close=(e:KeyboardEvent)=>{if(e.key==="Escape")setOpen(false);};const outside=(e:PointerEvent)=>{if(!ref.current?.contains(e.target as Node))setOpen(false);};window.addEventListener("keydown",close);window.addEventListener("pointerdown",outside);return ()=>{window.removeEventListener("keydown",close);window.removeEventListener("pointerdown",outside);};},[open]);
  return (
    <div className="relative min-w-0" ref={ref}>
      <Button
        variant="ghost"
        className="max-w-32 truncate sm:max-w-48"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {auth.profile?.display_name || "Your account"}
      </Button>
      {open && (
        <div className="absolute right-0 z-40 mt-2 w-64 space-y-2 rounded border bg-white p-3 shadow">
          <p className="text-sm font-medium">{auth.profile?.display_name}</p>
          <Link href="/profile" className="block text-sm underline" onClick={()=>setOpen(false)}>Your profile</Link>
          <Link
            className="block text-sm underline"
            href="/settings"
            onClick={() => setOpen(false)}
          >
            Account settings
          </Link>
          {error && (
            <p role="alert" className="text-sm text-rose-700">
              {error}
            </p>
          )}
          <Button
            disabled={busy}
            variant="outline"
            onClick={async () => {
              setBusy(true);
              setError("");
              try {
                await auth.logout();
              } catch (e) {
                setError(
                  e instanceof Error ? e.message : "Sign-out failed. Retry.",
                );
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Signing out…" : "Sign out"}
          </Button>
        </div>
      )}
    </div>
  );
}
