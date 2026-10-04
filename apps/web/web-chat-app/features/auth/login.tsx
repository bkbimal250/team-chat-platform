"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ApiError, identityApi } from "@/lib/api/client";
import { saveSession } from "@/lib/auth/session";
import { QRLogin } from "./qr-login";
import { Tokens } from "@/features/devices/api";
import { e164 } from "./security";
export function Login({ onAuthenticated }: { onAuthenticated: () => void }) {
  const [view, setView] = useState<
    "welcome" | "phone" | "otp" | "rejected" | "qr"
  >("welcome");
  const [country, setCountry] = useState("91");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [challenge, setChallenge] = useState("");
  const [developmentCode, setDevelopmentCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [countdown, setCountdown] = useState(0);
  const success = useCallback(
    (tokens: Tokens) => {
      saveSession(tokens);
      onAuthenticated();
    },
    [onAuthenticated],
  );
  useEffect(() => {
    const timer = setInterval(
      () => setCountdown((n) => Math.max(0, n - 1)),
      1000,
    );
    return () => clearInterval(timer);
  }, []);
  async function request(event?: FormEvent) {
    event?.preventDefault();
    if (busy || countdown) return;
    const number = e164(country, phone);
    if (!number) {
      setError("Enter a valid phone number with its country code.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await identityApi.requestOtp(number);
      if (!result.challenge_id) {
        setError("Unable to begin verification. Try again later.");
        return;
      }
      setChallenge(result.challenge_id);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
      const localApi = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/?$/.test(apiUrl);
      setDevelopmentCode(process.env.NODE_ENV === "development" && localApi ? result.development_code ?? "" : "");
      setCode("");
      setCountdown(60);
      setView("otp");
    } catch (issue) {
      if (
        issue instanceof ApiError &&
        issue.code === "REGISTRATION_NOT_ALLOWED"
      )
        setView("rejected");
      else
        setError(
          issue instanceof Error ? issue.message : "Unable to request code.",
        );
    } finally {
      setBusy(false);
    }
  }
  async function verify(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      success(await identityApi.verifyOtp(challenge, code));
    } catch (issue) {
      if (
        issue instanceof ApiError &&
        issue.code === "REGISTRATION_NOT_ALLOWED"
      )
        setView("rejected");
      else
        setError(
          issue instanceof Error ? issue.message : "Unable to verify code.",
        );
    } finally {
      setBusy(false);
    }
  }
  const button =
    "w-full rounded-xl bg-cyan-800 px-5 py-3 font-semibold text-white disabled:opacity-50";
  return (
    <main className="grid min-h-dvh bg-slate-50 lg:grid-cols-2">
      <section className="hidden flex-col justify-between bg-cyan-950 p-16 text-white lg:flex">
        <div className="text-2xl font-bold">◈ GlobalChat</div>
        <div>
          <p className="mb-5 text-sm uppercase tracking-[.25em] text-cyan-300">
            Built for your team
          </p>
          <h1 className="max-w-lg text-5xl font-semibold leading-tight">
            Closer conversations.
            <br />
            Connected teams.
          </h1>
          <p className="mt-6 max-w-md text-cyan-100">
            A focused workspace for company communication, with secure access
            and seamless device linking.
          </p>
        </div>
        <p className="text-sm text-cyan-300">
          Your workspace. Your conversations.
        </p>
      </section>
      <section className="grid place-items-center p-6">
        <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <p className="mb-7 text-lg font-bold text-cyan-800">◈ GlobalChat</p>
          {view === "qr" ? (
            <QRLogin onCancel={() => setView("welcome")} onSuccess={success} />
          ) : (
            <>
              <h2 className="text-3xl font-semibold">
                {view === "otp"
                  ? "Verify your number"
                  : view === "rejected"
                    ? "Invitation required"
                    : "Welcome to GlobalChat"}
              </h2>
              <p className="mt-3 mb-7 text-sm leading-6 text-slate-500">
                Secure communication for your organization.
              </p>
              {view === "welcome" && (
                <div className="space-y-4">
                  <button onClick={() => setView("phone")} className={button}>
                    Continue with phone
                  </button>
                  <button
                    onClick={() => setView("qr")}
                    className="w-full rounded-xl border border-cyan-800 px-5 py-3 font-semibold text-cyan-800"
                  >
                    Link with QR code
                  </button>
                </div>
              )}
              {view === "phone" && (
                <form onSubmit={request} className="space-y-5">
                  <label className="block text-sm font-semibold">
                    Country code
                    <input
                      aria-label="Country calling code"
                      inputMode="numeric"
                      value={country}
                      onChange={(e) =>
                        setCountry(
                          e.target.value.replace(/\D/g, "").slice(0, 3),
                        )
                      }
                      className="mt-2 w-full rounded-xl border px-4 py-3"
                    />
                  </label>
                  <label className="block text-sm font-semibold">
                    Phone number
                    <input
                      required
                      autoComplete="tel"
                      inputMode="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="mt-2 w-full rounded-xl border px-4 py-3"
                    />
                  </label>
                  <button disabled={busy} className={button}>
                    {busy ? "Requesting code…" : "Send verification code"}
                  </button>
                </form>
              )}
              {view === "otp" && (
                <form onSubmit={verify} className="space-y-5">
                  <p className="text-sm text-slate-500">
                    Enter the six-digit code sent to your phone.
                  </p>
                  <label className="block text-sm font-semibold">
                    Verification code
                    {developmentCode && <span className="mt-2 block rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Local development code: {developmentCode}. No SMS was sent.</span>}
                    <input
                      autoFocus
                      required
                      autoComplete="one-time-code"
                      inputMode="numeric"
                      pattern="[0-9]{6}"
                      maxLength={6}
                      value={code}
                      onChange={(e) =>
                        setCode(e.target.value.replace(/\D/g, ""))
                      }
                      className="mt-2 w-full rounded-xl border px-4 py-3 text-center text-2xl tracking-widest"
                    />
                  </label>
                  <button
                    disabled={busy || code.length !== 6}
                    className={button}
                  >
                    {busy ? "Verifying…" : "Continue securely"}
                  </button>
                  <button
                    type="button"
                    disabled={busy || countdown > 0}
                    onClick={() => void request()}
                    className="w-full text-sm font-semibold text-cyan-800 disabled:text-slate-400"
                  >
                    {countdown
                      ? `Resend available in ${countdown}s`
                      : "Resend code"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setView("phone");
                      setError("");
                    }}
                    className="w-full text-sm text-slate-500"
                  >
                    Use another number
                  </button>
                </form>
              )}
              {view === "rejected" && (
                <div>
                  <p className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-950">
                    This phone number hasn’t been invited to this workspace yet.
                    Contact your organization administrator for access.
                  </p>
                  <button
                    onClick={() => {
                      setView("phone");
                      setError("");
                    }}
                    className="mt-5 text-sm font-semibold text-cyan-800"
                  >
                    Try another number
                  </button>
                </div>
              )}
              {error && (
                <p
                  role="alert"
                  className="mt-5 rounded-xl bg-rose-50 p-4 text-sm text-rose-800"
                >
                  {error}
                </p>
              )}
            </>
          )}
        </div>
      </section>
    </main>
  );
}
