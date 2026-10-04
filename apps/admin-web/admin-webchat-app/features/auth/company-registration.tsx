"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { apiRequest, ApiError } from "@/lib/api/client";
import type { Tokens } from "@/lib/api/contracts";
import { useAuth } from "./auth-provider";

type Challenge = {
  registration_id: string;
  expires_at: string;
  resend_after: number;
  development_code?: string | null;
};
const endpoint = "/api/v1/auth/registration/company";
export function CompanyRegistration() {
  const auth = useAuth(),
    router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    owner_name: "",
    email: "",
    phone: "",
  });
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [otp, setOtp] = useState("");
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState("");
  const [retryProvisioning, setRetryProvisioning] = useState(false);
  const [remaining, setRemaining] = useState(0),
    [expiry, setExpiry] = useState(0);
  const [deadline, setDeadline] = useState(0);
  useEffect(() => {
    if (!challenge) return;
    const tick = () => {
      setRemaining(Math.max(0, Math.ceil((deadline - Date.now()) / 1000)));
      setExpiry(
        Math.max(
          0,
          Math.ceil((Date.parse(challenge.expires_at) - Date.now()) / 1000),
        ),
      );
    };
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [challenge, deadline]);
  function accept(value: Challenge) {
    setChallenge(value);
    setDeadline(Date.now() + value.resend_after * 1000);
    setOtp("");
  }
  async function perform(action: "start" | "verify" | "resend") {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      if (action === "start") {
        accept(
          await apiRequest<Challenge>(endpoint + "/start", {
            public: true,
            method: "POST",
            body: JSON.stringify(form),
          }),
        );
      } else if (action === "resend") {
        accept(
          await apiRequest<Challenge>(endpoint + "/resend", {
            public: true,
            method: "POST",
            body: JSON.stringify({
              registration_id: challenge?.registration_id,
            }),
          }),
        );
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
        const tokens = await apiRequest<Tokens>(endpoint + "/verify", {
          public: true,
          method: "POST",
          body: JSON.stringify({
            registration_id: challenge?.registration_id,
            otp,
            device: {
              installation_id,
              platform: "WEB",
              device_name: "GlobalChat Admin Browser",
            },
          }),
        });
        setOtp("");
        setChallenge(null);
        await auth.login(tokens);
        router.replace("/dashboard");
      }
    } catch (value) {
      setRetryProvisioning(
        value instanceof ApiError && value.code === "PROVISIONING_RETRY",
      );
      setError(
        value instanceof Error
          ? value.message
          : "Registration could not complete.",
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 p-4">
      <section className="w-full max-w-lg rounded-xl border bg-white p-6 shadow-sm sm:p-8">
        <p className="font-semibold text-indigo-600">
          GlobalChat · Company registration
        </p>
        <h1 className="my-4 text-2xl font-semibold">
          {challenge ? "Verify company owner" : "Create your company workspace"}
        </h1>
        <p className="mb-6 text-sm text-slate-600">
          {challenge
            ? "Verify your phone to provision your company and Owner access."
            : "You become the initial company owner. Existing workspaces remain invitation-only."}
        </p>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            void perform(challenge ? "verify" : "start");
          }}
        >
          {!challenge ? (
            (Object.keys(form) as (keyof typeof form)[]).map((key) => (
              <label className="block" key={key}>
                {
                  {
                    company_name: "Company Name",
                    owner_name: "Owner Name",
                    email: "Email",
                    phone: "Phone Number",
                  }[key]
                }
                <input
                  required
                  minLength={key.endsWith("name") ? 2 : undefined}
                  maxLength={key === "email" ? 254 : key === "phone" ? 64 : 200}
                  type={
                    key === "email" ? "email" : key === "phone" ? "tel" : "text"
                  }
                  autoComplete={
                    key === "email"
                      ? "email"
                      : key === "phone"
                        ? "tel"
                        : key === "owner_name"
                          ? "name"
                          : "organization"
                  }
                  pattern={key === "phone" ? "[+][1-9][0-9]{7,14}" : undefined}
                  className="mt-2 w-full rounded border p-3 focus-visible:outline-indigo-600"
                  disabled={busy}
                  value={form[key]}
                  onChange={(event) =>
                    setForm({ ...form, [key]: event.target.value })
                  }
                />
              </label>
            ))
          ) : (
            <>
              <label className="block">
                Verification code
                <input
                  autoFocus
                  required
                  pattern="[0-9]{6}"
                  maxLength={6}
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={otp}
                  disabled={busy}
                  onChange={(event) => setOtp(event.target.value)}
                  className="mt-2 w-full rounded border p-3 focus-visible:outline-indigo-600"
                />
              </label>
              <p className="text-sm text-slate-600">
                {retryProvisioning
                  ? "Verified. Retry with the same code to resume safely; do not register again."
                  : expiry > 0
                    ? `Code expires in ${expiry}s`
                    : "Code expired. Start a new registration."}
              </p>
              {process.env.NODE_ENV === "development" &&
                /^https?:\/\/(localhost|127\.0\.0\.1)(:|\/|$)/.test(
                  process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
                ) &&
                challenge.development_code && (
                  <p className="rounded bg-amber-50 p-2">
                    Local development code: {challenge.development_code}
                  </p>
                )}
            </>
          )}
          {error && (
            <p role="alert" className="text-sm text-rose-700">
              {error}
            </p>
          )}
          {busy && (
            <p role="status">
              {challenge
                ? "Verifying and provisioning your workspace…"
                : "Requesting verification…"}
            </p>
          )}
          <Button type="submit" disabled={busy} className="w-full">
            {busy
              ? "Please wait…"
              : challenge
                ? retryProvisioning
                  ? "Resume provisioning"
                  : "Verify and create company"
                : "Request registration code"}
          </Button>
          {challenge && (
            <Button
              type="button"
              variant="outline"
              disabled={busy || remaining > 0 || retryProvisioning}
              onClick={() => void perform("resend")}
            >
              {remaining > 0 ? `Resend in ${remaining}s` : "Resend code"}
            </Button>
          )}
          {challenge && expiry === 0 && !retryProvisioning && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setChallenge(null);
                setOtp("");
                setError("");
              }}
            >
              Start again
            </Button>
          )}
        </form>
        <Link
          href="/login"
          className="mt-6 block text-center font-medium text-indigo-600 underline"
        >
          Already have an account? Sign in
        </Link>
      </section>
    </main>
  );
}
