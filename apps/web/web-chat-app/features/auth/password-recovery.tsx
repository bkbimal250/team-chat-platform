"use client";

import Link from "next/link";
import { useRef, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { ApiError, apiRequest } from "@/lib/api/client";

const genericMessage =
  "If an account exists for this email, password reset instructions have been prepared.";

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

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiRequest("/api/v1/auth/password/forgot", {
        method: "POST",
        body: JSON.stringify({ email: email.trim() }),
      });
      setComplete(true);
      toast.success("Reset instructions prepared");
    } catch (issue) {
      setError(
        issue instanceof Error
          ? issue.message
          : "Unable to prepare reset instructions.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard>
      <h1 className="mt-5 text-3xl font-semibold">Reset your password</h1>
      <p className="mt-2 text-sm text-aurora-muted">
        Enter your workspace email address.
      </p>
      {complete ? (
        <div className="mt-6 space-y-5">
          <p
            role="status"
            className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900"
          >
            {genericMessage}
          </p>
          <Link
            className="text-sm font-semibold text-indigo-700 underline"
            href="/login"
          >
            Back to sign in
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            Email
            <input
              required
              type="email"
              autoComplete="email"
              maxLength={320}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-xl border bg-transparent p-3 focus:ring-2 focus:ring-indigo-500"
            />
          </label>
          {error && (
            <p role="alert" className="text-sm text-rose-700">
              {error}
            </p>
          )}
          <button
            disabled={busy}
            className="w-full rounded-xl bg-aurora-primary p-3 font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Preparing…" : "Send reset instructions"}
          </button>
        </form>
      )}
    </AuthCard>
  );
}

function resetError(issue: unknown) {
  if (issue instanceof ApiError && issue.code === "PASSWORD_RESET_INVALID")
    return "This password reset link is invalid, expired, or has already been used.";
  if (issue instanceof ApiError && issue.code === "PASSWORD_POLICY")
    return "Use a password between 12 and 128 characters.";
  return issue instanceof Error
    ? issue.message
    : "Unable to reset your password.";
}

export function ResetPassword() {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current) return;
    const token =
      new URLSearchParams(window.location.search).get("token") ?? "";
    if (!token) {
      setError("This password reset link is invalid or incomplete.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      await apiRequest("/api/v1/auth/password/reset", {
        method: "POST",
        body: JSON.stringify({ token, new_password: password }),
      });
      setPassword("");
      setConfirm("");
      setComplete(true);
      toast.success("Password updated successfully");
    } catch (issue) {
      setError(resetError(issue));
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return (
    <AuthCard>
      <h1 className="mt-5 text-3xl font-semibold">Choose a new password</h1>
      <p className="mt-2 text-sm text-aurora-muted">
        Use 12–128 characters. Existing sessions will be signed out.
      </p>
      {complete ? (
        <div className="mt-6 space-y-5">
          <p
            role="status"
            className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-900"
          >
            Password updated successfully.
          </p>
          <Link
            className="text-sm font-semibold text-indigo-700 underline"
            href="/login"
          >
            Sign in
          </Link>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block">
            New password
            <input
              required
              minLength={12}
              maxLength={128}
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-xl border bg-transparent p-3 focus:ring-2 focus:ring-indigo-500"
            />
          </label>
          <label className="block">
            Confirm password
            <input
              required
              minLength={12}
              maxLength={128}
              type="password"
              autoComplete="new-password"
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
              className="mt-2 w-full rounded-xl border bg-transparent p-3 focus:ring-2 focus:ring-indigo-500"
            />
          </label>
          {error && (
            <p role="alert" className="text-sm text-rose-700">
              {error}
            </p>
          )}
          <button
            disabled={busy}
            className="w-full rounded-xl bg-aurora-primary p-3 font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Updating…" : "Update password"}
          </button>
        </form>
      )}
    </AuthCard>
  );
}
