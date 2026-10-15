"use client";
import { CountryPhone, registrationPhone } from "./country-phone";
import type { CountryCode } from "libphonenumber-js";
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
export function CompanyOTPRegistration() {
  const auth = useAuth(),
    router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    owner_name: "",
    email: "",
    phone: "",
  });
  const [country, setCountry] = useState<CountryCode>("IN");
  const [requestDeadline, setRequestDeadline] = useState(0);
  const [requestWait, setRequestWait] = useState(0);
  useEffect(() => {
    const tick = () => setRequestWait(Math.max(0, Math.ceil((requestDeadline - Date.now()) / 1000)));
    tick(); const timer = setInterval(tick, 1000); return () => clearInterval(timer);
  }, [requestDeadline]);
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
    if (pending.current || requestDeadline > Date.now()) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      if (action === "start") {
        accept(
          await apiRequest<Challenge>(endpoint + "/start", {
            public: true,
            method: "POST",
            body: JSON.stringify({ ...form, phone: registrationPhone(form.phone, country) }),
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
      if (value instanceof ApiError && value.status === 429) {
        const seconds = value.retryAfter ?? (value.code === "OTP_RESEND_COOLDOWN" ? 60 : 3600);
        setRequestDeadline(Date.now() + seconds * 1000);
      }
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
      <section className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-10">
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
        <ol aria-label="Registration progress" className="mb-6 grid grid-cols-3 gap-2 text-xs sm:text-sm">
          {["Company details", "Verify owner", "Workspace ready"].map((label, index) => <li key={label} aria-current={index === (challenge ? 1 : 0) ? "step" : undefined} className={`rounded-lg border p-3 ${index === (challenge ? 1 : 0) ? "border-indigo-300 bg-indigo-50 font-medium text-indigo-700" : "border-slate-200 text-slate-500"}`}>{index + 1}. {label}</li>)}
        </ol>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            void perform(challenge ? "verify" : "start");
          }}
        >
          {!challenge ? (
            <>
            {(["company_name", "owner_name", "email"] as const).map((key) => (
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
                  maxLength={key === "email" ? 254 : 200}
                  type={
                    key === "email" ? "email" : "text"
                  }
                  autoComplete={
                    key === "email"
                      ? "email"
                      : key === "owner_name"
                          ? "name"
                          : "organization"
                  }

                  className="mt-2 w-full rounded border p-3 focus-visible:outline-indigo-600"
                  disabled={busy}
                  value={form[key]}
                  onChange={(event) =>
                    setForm({ ...form, [key]: event.target.value })
                  }
                />
              </label>
            ))}
            <CountryPhone value={form.phone} country={country} onCountryChange={setCountry} onChange={phone => setForm({ ...form, phone })} disabled={busy} />
            </>
          ) : (
            <>
              <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">Creating <strong>{form.company_name}</strong> for {form.owner_name}. Check your phone for the six-digit verification code.</p>
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
          {requestWait > 0 && <p role="status" className="rounded bg-amber-50 p-3 text-sm text-amber-900">Too many code requests. Please wait {Math.ceil(requestWait / 60)} minute(s). Repeated requests will not send a code.</p>}
          {busy && (
            <p role="status">
              {challenge
                ? "Verifying and provisioning your workspace…"
                : "Requesting verification…"}
            </p>
          )}
          <Button type="submit" disabled={busy || requestWait > 0} className="w-full">
            {requestWait > 0 ? `Try again in ${requestWait}s` : busy
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
              disabled={busy || requestWait > 0 || remaining > 0 || retryProvisioning}
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
        <p className="mt-6 text-xs leading-relaxed text-slate-500">Your workspace is created only after phone verification. You receive Owner access; employees join by secure invitation. No password is required.</p>
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
