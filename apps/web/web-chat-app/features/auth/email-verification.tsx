"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ApiError, apiRequest } from "@/lib/api/client";

const genericMessage =
  "If an eligible account exists for this email, verification instructions have been prepared.";

function AuthCard({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-[var(--background)] p-5 text-[var(--foreground)]">
      <section className="w-full max-w-md rounded-3xl border border-aurora-border p-8 shadow-sm">
        <Link href="/login" className="font-bold text-indigo-600">
          GlobalChat
        </Link>
        {children}
      </section>
    </main>
  );
}

function verificationError(issue: unknown) {
  if (
    issue instanceof ApiError &&
    issue.code === "EMAIL_VERIFICATION_INVALID"
  ) {
    return "This verification link is invalid, expired, or has already been used.";
  }
  return issue instanceof Error
    ? issue.message
    : "Unable to verify this email address.";
}

export function VerifyEmail() {
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);

  async function verify() {
    if (pending.current) return;
    const token =
      new URLSearchParams(window.location.search).get("token") ?? "";
    if (!token) {
      setError("This verification link is invalid or incomplete.");
      return;
    }
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      await apiRequest("/api/v1/auth/email/verify", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setComplete(true);
      toast.success("Email verified successfully");
    } catch (issue) {
      setError(verificationError(issue));
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return (
    <AuthCard>
      <h1 className="mt-5 text-3xl font-semibold">Verify your email</h1>
      <p className="mt-2 text-sm text-aurora-muted">
        Confirm this email address to help secure your GlobalChat account.
      </p>
      {complete ? (
        <div className="mt-6 space-y-5">
          <p
            role="status"
            className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900"
          >
            Email verified successfully.
          </p>
          <Link
            className="text-sm font-semibold text-indigo-700 underline"
            href="/"
          >
            Continue to GlobalChat
          </Link>
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {error && (
            <p role="alert" className="text-sm text-rose-700">
              {error}
            </p>
          )}
          <button
            onClick={() => void verify()}
            disabled={busy}
            className="w-full rounded-xl bg-aurora-primary p-3 font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Verifying…" : "Verify email"}
          </button>
        </div>
      )}
    </AuthCard>
  );
}

type Me = { identity?: { email?: string | null; email_verified?: boolean } };

export function EmailVerificationStatus({ token }: { token: string }) {
  const [state, setState] = useState<
    "loading" | "verified" | "unverified" | "error"
  >("loading");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    apiRequest<Me>("/api/v1/auth/me", {}, token)
      .then((result) => {
        if (!active) return;
        setEmail(result.identity?.email ?? "");
        setState(result.identity?.email_verified ? "verified" : "unverified");
      })
      .catch(() => active && setState("error"));
    return () => {
      active = false;
    };
  }, [token]);

  async function resend() {
    if (!email || busy) return;
    setBusy(true);
    try {
      await apiRequest("/api/v1/auth/email/verification/resend", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      toast.success("Verification instructions prepared");
    } catch (issue) {
      toast.error(
        issue instanceof Error
          ? issue.message
          : "Unable to resend verification instructions.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (state === "loading")
    return (
      <p className="mt-2 text-sm text-aurora-muted">
        Checking email verification…
      </p>
    );
  if (state === "error")
    return (
      <p role="alert" className="mt-2 text-sm text-rose-700">
        Email verification status is unavailable.
      </p>
    );
  if (state === "verified")
    return <p className="mt-2 text-sm text-emerald-700">Email verified</p>;
  return (
    <div className="mt-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
      <p className="font-medium">Email not verified</p>
      <p className="mt-1">Verify your email to help secure your account.</p>
      <button
        onClick={() => void resend()}
        disabled={busy}
        className="mt-3 font-semibold underline disabled:opacity-50"
      >
        {busy ? "Preparing…" : "Resend verification"}
      </button>
      <p className="mt-2 text-xs">{genericMessage}</p>
    </div>
  );
}
