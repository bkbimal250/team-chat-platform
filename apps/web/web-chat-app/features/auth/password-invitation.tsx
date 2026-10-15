"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api/client";
import { saveSession } from "@/lib/auth/session";
import { deviceInput } from "@/lib/auth/device";
import type { Tokens } from "@/features/devices/api";

export function PasswordInvitation() {
  const router = useRouter(), token = useRef(""), pending = useRef(false);
  const [ready, setReady] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [email, setEmail] = useState(""), [password, setPassword] = useState(""), [confirm, setConfirm] = useState(""), [show, setShow] = useState(false);
  useEffect(() => { token.current = new URLSearchParams(window.location.hash.slice(1)).get("invite") ?? new URLSearchParams(window.location.search).get("token") ?? ""; window.history.replaceState(null, "", "/join"); setReady(!!token.current); if (!token.current) setError("This invitation link is invalid. Ask your administrator for a new link."); }, []);
  async function submit(event: FormEvent) {
    event.preventDefault(); if (pending.current || !ready) return;
    if (password !== confirm) { setError("Passwords do not match."); return; }
    pending.current = true; setBusy(true); setError("");
    try { const tokens = await apiRequest<Tokens>("/api/v1/auth/invitations/password", { method: "POST", body: JSON.stringify({ token: token.current, email, password, device: deviceInput() }) }); saveSession(tokens); setPassword(""); setConfirm(""); token.current = ""; router.replace("/"); }
    catch (issue) { setError(issue instanceof Error ? issue.message : "Invitation could not be accepted."); }
    finally { pending.current = false; setBusy(false); }
  }
  return <main className="flex min-h-dvh items-center justify-center p-5"><section className="w-full max-w-md space-y-5 rounded-3xl border p-7"><p className="font-bold">GlobalChat</p><h1 className="text-2xl font-semibold">Join your workspace</h1><p className="text-sm">Use the invited email. Set your own password, or enter your existing account password. Your workspace, role and team are assigned by the invitation.</p><form onSubmit={submit} className="space-y-4"><label className="block">Email<input required type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="mt-2 w-full rounded border bg-transparent p-3" /></label><label className="block">Password<input required type={show ? "text" : "password"} maxLength={128} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className="mt-2 w-full rounded border bg-transparent p-3" /></label><label className="block">Confirm password<input required type={show ? "text" : "password"} maxLength={128} autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} className="mt-2 w-full rounded border bg-transparent p-3" /></label><button type="button" aria-pressed={show} onClick={() => setShow(!show)} className="text-sm underline">{show ? "Hide passwords" : "Show passwords"}</button><p className="text-xs">New passwords require 12–128 characters. Existing passwords are never replaced.</p>{error && <p role="alert" className="text-rose-600">{error}</p>}<button disabled={!ready || busy} className="w-full rounded bg-aurora-primary p-3 text-white disabled:opacity-50">{busy ? "Joining…" : "Join workspace"}</button></form></section></main>;
}
