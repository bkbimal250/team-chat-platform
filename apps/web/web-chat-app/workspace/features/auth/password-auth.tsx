"use client";

import Link from "next/link";
import { useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import type { CountryCode } from "libphonenumber-js";
import { ApiError, apiRequest } from "@/workspace/lib/api/client";
import type { Tokens } from "@/workspace/lib/api/contracts";
import { useAuth } from "./auth-provider";
import { CountryPhone, registrationPhone } from "./country-phone";
import { Button } from "@/workspace/components/ui/button";
import { toast } from "sonner";

const inputClass =
  "mt-2 w-full rounded-xl border border-aurora-border bg-transparent px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500";

function displayAuthError(issue: unknown) {
  if (issue instanceof ApiError && issue.code === "ACCOUNT_EXISTS") {
    return "An account already exists for this email. Sign in to your workspace instead.";
  }
  return issue instanceof Error
    ? issue.message
    : "Authentication is unavailable. Please try again.";
}

function RegistrationSteps({
  step,
}: {
  step: 1 | 2;
}) {
  const items = [
    { n: 1, label: "Your details" },
    { n: 2, label: "Secure your account" },
  ];
  return (
    <ol
      className="mt-5 flex gap-2"
      aria-label="Registration progress"
    >
      {items.map((item) => {
        const active = step === item.n;
        const done = step > item.n;
        return (
          <li key={item.n} className="flex min-w-0 flex-1 flex-col gap-1.5">
            <div
              className={`h-1.5 rounded-full transition-colors ${
                active || done ? "bg-indigo-600" : "bg-aurora-border"
              }`}
              aria-hidden
            />
            <span
              className={`truncate text-xs font-medium ${
                active ? "text-indigo-700" : "text-aurora-muted"
              }`}
            >
              Step {item.n}: {item.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export function PasswordAuth({
  registration = false,
}: {
  registration?: boolean;
}) {
  const auth = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    owner_name: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
  });
  const [mode, setMode] = useState<"personal" | "company">("personal");
  const [country, setCountry] = useState<CountryCode>("IN");
  const [regStep, setRegStep] = useState<1 | 2>(1);
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);

  function validateProfileStep(): string | null {
    if (mode === "company" && form.company_name.trim().length < 2) {
      return "Enter your company name.";
    }
    if (form.owner_name.trim().length < 2) {
      return "Enter your name.";
    }
    const email = form.email.trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return "Enter a valid email address.";
    }
    try {
      const phone = registrationPhone(form.phone, country);
      if (!phone) return "Enter a valid phone number.";
    } catch {
      return "Enter a valid phone number.";
    }
    return null;
  }

  function continueRegistration() {
    setError("");
    const issue = validateProfileStep();
    if (issue) {
      setError(issue);
      return;
    }
    setRegStep(2);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current) return;
    setError("");
    if (registration && regStep === 1) {
      continueRegistration();
      return;
    }
    if (registration && form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    let phone = "";
    try {
      phone = registration ? registrationPhone(form.phone, country) : "";
    } catch {
      setError("Enter a valid phone number.");
      return;
    }
    if (registration && !phone) {
      setError("Enter a valid phone number.");
      return;
    }
    pending.current = true;
    setBusy(true);
    try {
      let installation = localStorage.getItem(
        "globalchat.workspace.installation",
      );
      if (!installation) {
        installation = crypto.randomUUID();
        localStorage.setItem("globalchat.workspace.installation", installation);
      }
      const body = {
        email: form.email.trim(),
        password: form.password,
        device: {
          installation_id: installation,
          platform: "WEB",
          device_name: "GlobalChat Workspace Browser",
        },
        ...(registration
          ? {
              ...(mode === "company"
                ? {
                    company_name: form.company_name,
                    owner_name: form.owner_name,
                  }
                : { display_name: form.owner_name }),
              phone,
            }
          : {}),
      };
      const tokens = await apiRequest<Tokens>(
        registration
          ? `/api/v1/auth/registration/${mode}`
          : "/api/v1/auth/login",
        { public: true, method: "POST", body: JSON.stringify(body) },
      );
      setForm((previous) => ({ ...previous, password: "", confirm: "" }));
      await auth.login(tokens);
      router.replace(tokens.organization_id ? "/workspace" : "/");
    } catch (issue) {
      const message = displayAuthError(issue);
      setError(message);
      if (
        registration &&
        issue instanceof ApiError &&
        issue.code === "ACCOUNT_EXISTS"
      ) {
        toast.error("Account already exists", {
          description:
            "Sign in with this email to access your existing workspace.",
          action: { label: "Sign in", onClick: () => router.push("/login") },
        });
      } else {
        toast.error("Unable to continue", { description: message });
      }
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  const field = (key: keyof typeof form, label: string, type = "text") => (
    <label className="block text-sm font-medium">
      {label}
      <input
        name={key}
        required
        type={type}
        value={form[key]}
        minLength={
          key === "password" && registration
            ? 12
            : key === "company_name" || key === "owner_name"
              ? 2
              : undefined
        }
        maxLength={
          key === "password" || key === "confirm"
            ? 128
            : key === "email"
              ? 254
              : 200
        }
        autoComplete={
          key === "password" || key === "confirm"
            ? registration
              ? "new-password"
              : "current-password"
            : key === "email"
              ? "email"
              : key === "owner_name"
                ? "name"
                : "organization"
        }
        onChange={(event) => setForm({ ...form, [key]: event.target.value })}
        className={inputClass}
      />
    </label>
  );

  const modeOptions = (
    <div
      className="mt-5 grid grid-cols-2 gap-2 rounded-2xl border border-aurora-border bg-aurora-background/60 p-1.5"
      role="group"
      aria-label="Account type"
    >
      {(["personal", "company"] as const).map((value) => {
        const selected = mode === value;
        return (
          <button
            key={value}
            type="button"
            aria-pressed={selected}
            disabled={busy}
            onClick={() => {
              setMode(value);
              setError("");
              setRegStep(1);
            }}
            className={`rounded-xl px-3 py-3 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-500 ${
              selected
                ? "border border-indigo-200 bg-aurora-surface text-indigo-900 shadow-sm"
                : "border border-transparent text-aurora-muted hover:text-aurora-text"
            }`}
          >
            {value === "personal" ? "Personal account" : "Create a company"}
          </button>
        );
      })}
    </div>
  );

  const profileFields = (
    <>
      {mode === "company" && field("company_name", "Company name")}
      {field("owner_name", mode === "company" ? "Owner name" : "Your name")}
      {field("email", "Email", "email")}
      <CountryPhone
        country={country}
        onCountryChange={setCountry}
        value={form.phone}
        onChange={(phone) => setForm({ ...form, phone })}
        disabled={busy}
      />
    </>
  );

  const securityFields = (
    <>
      {field("password", "Password", show ? "text" : "password")}
      {field("confirm", "Confirm password", show ? "text" : "password")}
      <button
        type="button"
        aria-pressed={show}
        onClick={() => setShow(!show)}
        className="text-sm text-indigo-700 underline"
      >
        {show ? "Hide passwords" : "Show passwords"}
      </button>
      <p className="text-xs leading-relaxed text-aurora-muted">
        Use 12–128 characters. Phone and email are not marked verified by
        registration.
      </p>
    </>
  );

  return (
    <main className="flex min-h-dvh items-center justify-center bg-aurora-background px-4 py-10 text-aurora-text">
      <section className="w-full max-w-lg rounded-3xl border border-aurora-border bg-aurora-surface p-7 shadow-sm sm:p-8">
        <Link href="/login" className="font-bold text-indigo-600">
          GlobalChat
        </Link>
        <h1 className="mt-5 text-3xl font-semibold tracking-tight">
          {registration ? "Create your GlobalChat account" : "Welcome back"}
        </h1>
        <p className="mt-2 text-sm text-aurora-muted">
          {registration
            ? regStep === 1
              ? mode === "company"
                ? "Step 1 — Tell us about your company and how to reach you."
                : "Step 1 — Your profile and contact details."
              : "Step 2 — Choose a strong password to protect your account."
            : "Sign in with your workspace email and password."}
        </p>

        {registration && (
          <>
            {modeOptions}
            <RegistrationSteps step={regStep} />
          </>
        )}

        <form onSubmit={submit} className="mt-6 space-y-4">
          {registration ? (
            regStep === 1 ? profileFields : securityFields
          ) : (
            <>
              {field("email", "Email", "email")}
              {field("password", "Password", show ? "text" : "password")}
              <button
                type="button"
                aria-pressed={show}
                onClick={() => setShow(!show)}
                className="text-sm text-indigo-700 underline"
              >
                {show ? "Hide password" : "Show password"}
              </button>
            </>
          )}

          {error && (
            <p
              role="alert"
              className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-950/40 dark:text-rose-200"
            >
              {error}
              {registration &&
                error.startsWith("An account already exists") && (
                  <Link href="/login" className="ml-1 font-semibold underline">
                    Sign in instead
                  </Link>
                )}
            </p>
          )}

          {registration && regStep === 2 ? (
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                type="button"
                variant="outline"
                disabled={busy}
                className="w-full sm:flex-1"
                onClick={() => {
                  setError("");
                  setRegStep(1);
                }}
              >
                Back
              </Button>
              <Button type="submit" disabled={busy} className="w-full sm:flex-[2]">
                {busy
                  ? "Please wait…"
                  : mode === "company"
                    ? "Create company"
                    : "Create account"}
              </Button>
            </div>
          ) : (
            <Button type="submit" disabled={busy} className="w-full">
              {busy
                ? "Please wait…"
                : registration
                  ? "Continue"
                  : "Sign in"}
            </Button>
          )}
        </form>

        <p className="mt-5 text-sm">
          <Link
            href={registration ? "/login" : "/register"}
            className="text-indigo-700 underline"
          >
            {registration ? "Already registered? Sign in" : "Create an account"}
          </Link>
        </p>
        <p className="mt-3 text-xs text-aurora-muted">
          <Link href="/forgot-password" className="underline">
            Forgot your password?
          </Link>
        </p>
      </section>
    </main>
  );
}
