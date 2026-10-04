"use client";

import Link from "next/link";
import { useState } from "react";

import { useRouter } from "next/navigation";

import { apiRequest, ApiError } from "@/lib/api/client";

import type { Tokens } from "@/lib/api/contracts";

import { useAuth } from "./auth-provider";

import { Button } from "@/components/ui/button";

export function Login() {
  const auth = useAuth(),
    router = useRouter();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [challenge, setChallenge] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [localCode, setLocalCode] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      if (!challenge) {
        if (!/^\+[1-9]\d{7,14}$/.test(phone))
          throw new Error(
            "Enter an international phone number, including country code.",
          );
        const result = await apiRequest<{
          challenge_id: string | null;
          development_code?: string | null;
        }>("/api/v1/auth/otp/request", {
          public: true,
          method: "POST",
          body: JSON.stringify({ phone_number: phone, purpose: "LOGIN" }),
        });
        if (!result.challenge_id)
          throw new Error(
            "If this number is eligible, a code will be sent. Contact your administrator if you cannot continue.",
          );
        setChallenge(result.challenge_id);
        if (
          process.env.NODE_ENV === "development" &&
          /^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(
            process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
          )
        )
          setLocalCode(result.development_code ?? null);
      } else {
        let installation_id = localStorage.getItem(
          "globalchat.admin.installation",
        );
        if (!installation_id) {
          installation_id = crypto.randomUUID();
          localStorage.setItem(
            "globalchat.admin.installation",
            installation_id,
          );
        }
        const tokens = await apiRequest<Tokens>("/api/v1/auth/otp/verify", {
          public: true,
          method: "POST",
          body: JSON.stringify({
            challenge_id: challenge,
            code,
            device: {
              installation_id,
              platform: "WEB",
              device_name: "GlobalChat Admin Browser",
            },
          }),
        });
        setCode("");
        setLocalCode(null);
        await auth.login(tokens);
        router.replace("/dashboard");
      }
    } catch (e) {
      setError(
        e instanceof ApiError && e.code === "REGISTRATION_NOT_ALLOWED"
          ? "This phone number has not been invited. Contact your organization administrator for access."
          : e instanceof Error
            ? e.message
            : "Sign-in failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-4">
      <section className="w-full max-w-md rounded-xl border bg-white p-8 shadow-sm">
        <p className="font-semibold text-indigo-600">
          GlobalChat · Admin Console
        </p>
        <h1 className="my-4 text-2xl font-semibold">
          {challenge ? "Verify your code" : "Sign in to your workspace"}
        </h1>
        <p className="mb-6 text-sm text-slate-500">
          Sign in with your verified phone. Admin access requires an active
          workspace membership with administration permissions.
        </p>
        <form onSubmit={submit} className="space-y-4">
          <label className="block">
            {challenge ? "Verification code" : "Phone number"}
            <input
              autoFocus
              required
              className="mt-2 w-full rounded border p-3"
              type={challenge ? "text" : "tel"}
              inputMode={challenge ? "numeric" : "tel"}
              autoComplete={challenge ? "one-time-code" : "tel"}
              pattern={challenge ? "[0-9]{6}" : "[+][1-9][0-9]{7,14}"}
              value={challenge ? code : phone}
              onChange={(e) =>
                challenge ? setCode(e.target.value) : setPhone(e.target.value)
              }
              disabled={busy}
            />
          </label>
          {localCode && (
            <p className="rounded bg-amber-50 p-2 text-sm">
              Local development code: {localCode}
            </p>
          )}
          {error && (
            <p role="alert" className="text-sm text-rose-700">
              {error}
            </p>
          )}
          <Button className="w-full" type="submit" disabled={busy}>
            {busy
              ? "Please wait…"
              : challenge
                ? "Verify and sign in"
                : "Request code"}
          </Button>
          {challenge && (
            <Button
              variant="ghost"
              type="button"
              disabled={busy}
              onClick={() => {
                setChallenge(null);
                setCode("");
                setLocalCode(null);
              }}
            >
              Use another number
            </Button>
          )}
        </form>
        <Link
          className="mt-6 block text-center font-medium text-indigo-600 underline focus-visible:outline-2"
          href="/register"
        >
          Create Company
        </Link>
      </section>
    </main>
  );
}
