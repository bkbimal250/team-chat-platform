"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { apiRequest, ApiError } from "@/lib/api/client";
import { deviceInput } from "@/lib/auth/device";
import { saveSession } from "@/lib/auth/session";

type Invitation = { company_name: string; recipient_name: string; recipient_phone_masked: string; expires_at: string };
type Challenge = { onboarding_id: string; expires_at: string; resend_after: number; verified?: boolean; development_code?: string | null };
export function invitationError(error: unknown): string {
  const messages: Record<string, string> = {
    INVITATION_INVALID: "This invitation link is invalid. Ask your administrator for a new invitation.",
    INVITATION_EXPIRED: "This invitation has expired. Ask your administrator for a new invitation.",
    INVITATION_REVOKED: "Your administrator has revoked this invitation.",
    INVITATION_ACCEPTED: "This invitation has already been accepted. Sign in to your existing account.",
    OTP_INVALID: "That code is incorrect. Please try again.",
    OTP_EXPIRED: "Your verification code has expired. Request a new code.",
    OTP_TOO_MANY_ATTEMPTS: "Too many verification attempts. Contact your administrator.",
    PROVISIONING_RETRY: "Your phone was verified, but onboarding could not finish. Retry with the same code.",
    INVITATION_VERIFIED: "Your phone was verified. Retry verification with the same code to finish onboarding.",
    RATE_LIMITED: "Please wait before requesting another code.",
    OTP_RESEND_COOLDOWN: "Please wait before requesting another code.",
    NETWORK_ERROR: "We could not connect. Check your connection and retry.",
  };
  return error instanceof ApiError ? messages[error.code] ?? "Onboarding could not complete. Contact your administrator or retry." : "Onboarding is unavailable. Please retry.";
}
export function PhoneOTPInvitationJoin() {
  const router = useRouter();
  const token = useRef("");
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [code, setCode] = useState("");
  const [countdown, setCountdown] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    // Fragment secrets never reach the web server or referrers. Remove before rendering.
    token.current ||= new URLSearchParams(window.location.hash.slice(1)).get("invite") ?? "";
    window.history.replaceState(null, "", window.location.pathname);
    apiRequest<Invitation>("/api/v1/auth/invitations/validate", { method: "POST", signal: controller.signal, body: JSON.stringify({ token: token.current }) })
      .then((data) => { if (!controller.signal.aborted) setInvitation(data); })
      .catch((issue) => { if (!controller.signal.aborted) setError(invitationError(issue)); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const timer = setInterval(() => setCountdown((n) => Math.max(0, n - 1)), 1000);
    return () => clearInterval(timer);
  }, []);
  async function requestCode() {
    if (busy || countdown || !invitation) return;
    setBusy(true); setError("");
    try {
      const data = await apiRequest<Challenge>("/api/v1/auth/invitations/" + (challenge ? "resend" : "request"), { method: "POST", body: JSON.stringify({ token: token.current }) });
      setChallenge(data); setCountdown(data.resend_after); setCode("");
    } catch (issue) { setError(invitationError(issue)); }
    finally { setBusy(false); }
  }
  async function verify(event: FormEvent) {
    event.preventDefault();
    if (busy || !challenge || !/^\d{6}$/.test(code)) return;
    setBusy(true); setError("");
    try {
      const tokens = await apiRequest<{ access_token: string; refresh_token: string | null }>("/api/v1/auth/invitations/verify", { method: "POST", body: JSON.stringify({ onboarding_id: challenge.onboarding_id, otp: code, device: deviceInput() }) });
      saveSession(tokens); setCode(""); token.current = ""; router.replace("/");
    } catch (issue) { setError(invitationError(issue)); }
    finally { setBusy(false); }
  }
  return <main className="grid min-h-dvh place-items-center bg-aurora-background p-4 text-aurora-text">
    <section className="w-full max-w-md space-y-6 rounded-3xl border border-aurora-border bg-aurora-surface p-7 shadow-sm" aria-label="Employee invitation">
      <Link href="/" className="text-xl font-bold">GlobalChat</Link>
      <h1 className="text-2xl font-semibold">Join your workspace</h1>
      {loading ? <p role="status">Checking your invitation…</p> : invitation ? <>
        <div className="space-y-2"><h2 className="text-lg font-medium">{invitation.company_name}</h2><p>Hello, {invitation.recipient_name}.</p><p>Verify the invited phone <strong>{invitation.recipient_phone_masked}</strong> to continue. Your administrator has assigned your role and memberships.</p></div>
        {!challenge ? <button disabled={busy} onClick={requestCode} className="w-full rounded-xl bg-teal-700 p-3 font-medium text-white disabled:opacity-50">{busy ? "Requesting…" : "Request invitation code"}</button> : <form onSubmit={verify} className="space-y-4">
          {challenge.verified && <p className="text-sm">Phone already verified. Enter the same code to resume onboarding.</p>}
          <label className="block">Verification code<input autoFocus required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} className="mt-2 block w-full rounded-xl border border-aurora-border bg-aurora-background p-3 tracking-widest" /></label>
          {challenge.development_code && <p className="text-sm">Local development code: <span data-testid="invitation-development-code">{challenge.development_code}</span></p>}
          <button disabled={busy || code.length !== 6} className="w-full rounded-xl bg-teal-700 p-3 font-medium text-white disabled:opacity-50">{busy ? "Joining…" : "Verify and join workspace"}</button>
          <button type="button" disabled={busy || countdown > 0} onClick={requestCode} className="w-full rounded-xl border border-aurora-border p-3 disabled:opacity-50">{countdown ? `Resend code in ${countdown}s` : "Resend code"}</button>
        </form>}
      </> : null}
      {error && <p role="alert" className="rounded-xl border border-red-300 p-3 text-sm text-red-600">{error}</p>}
      <Link href="/" className="block text-sm underline">Already joined? Sign in</Link>
    </section>
  </main>;
}
