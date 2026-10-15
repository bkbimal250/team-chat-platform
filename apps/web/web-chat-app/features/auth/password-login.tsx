"use client";
import Link from "next/link";
import { useRef, useState, type FormEvent } from "react";
import { apiRequest } from "@/lib/api/client";
import { deviceInput } from "@/lib/auth/device";
import { saveSession } from "@/lib/auth/session";
import type { Tokens } from "@/features/devices/api";
import { QRLogin } from "./qr-login";

export function PasswordLogin({
  onAuthenticated,
}: {
  onAuthenticated: () => void;
}) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState("");
  const [busy, setBusy] = useState(false),
    [show, setShow] = useState(false),
    [qr, setQr] = useState(false);
  const pending = useRef(false);
  const success = (tokens: Tokens) => {
    saveSession(tokens);
    setPassword("");
    onAuthenticated();
  };
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      success(
        await apiRequest<Tokens>("/api/v1/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: email.trim(),
            password,
            device: deviceInput(),
          }),
        }),
      );
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Unable to sign in.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  return (
    <main className="flex min-h-dvh items-center justify-center bg-[var(--background)] p-5 text-[var(--foreground)]">
      <section className="w-full max-w-md rounded-3xl border border-aurora-border p-8">
        <p className="font-bold text-indigo-600">GlobalChat</p>
        <h1 className="mt-5 text-3xl font-semibold">
          Sign in to your workspace
        </h1>
        {qr ? (
          <QRLogin onCancel={() => setQr(false)} onSuccess={success} />
        ) : (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block">
              Email
              <input
                type="email"
                autoComplete="email"
                required
                maxLength={320}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 w-full rounded-xl border bg-transparent p-3 focus:ring-2 focus:ring-indigo-500"
              />
            </label>
            <label className="block">
              Password
              <input
                type={show ? "text" : "password"}
                autoComplete="current-password"
                required
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border bg-transparent p-3 focus:ring-2 focus:ring-indigo-500"
              />
            </label>
            <button
              type="button"
              aria-pressed={show}
              onClick={() => setShow(!show)}
              className="text-sm underline"
            >
              {show ? "Hide password" : "Show password"}
            </button>
            <Link
              href="/forgot-password"
              className="ml-4 text-sm text-aurora-primary underline"
            >
              Forgot password?
            </Link>
            {error && (
              <p role="alert" className="text-rose-600">
                {error}
              </p>
            )}
            <button
              disabled={busy}
              className="w-full rounded-xl bg-aurora-primary p-3 font-semibold text-white disabled:opacity-50"
            >
              {busy ? "Signing in…" : "Sign In"}
            </button>
          </form>
        )}
        <button
          type="button"
          onClick={() => setQr(!qr)}
          className="mt-5 text-sm underline"
        >
          {qr ? "Sign in with email" : "Link with QR"}
        </button>
        <p className="mt-4">
          <Link
            className="text-sm text-aurora-primary underline"
            href="/register"
          >
            Create an account
          </Link>
        </p>
        <p className="mt-4 text-xs text-aurora-muted">
          Access requires a workspace invitation.
        </p>
      </section>
    </main>
  );
}
