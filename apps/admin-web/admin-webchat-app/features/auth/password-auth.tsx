"use client";
import Link from "next/link";
import { useRef, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import type { CountryCode } from "libphonenumber-js";
import { apiRequest } from "@/lib/api/client";
import type { Tokens } from "@/lib/api/contracts";
import { useAuth } from "./auth-provider";
import { CountryPhone, registrationPhone } from "./country-phone";
import { Button } from "@/components/ui/button";

export function PasswordAuth({
  registration = false,
}: {
  registration?: boolean;
}) {
  const auth = useAuth(),
    router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    owner_name: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
  });
  const [country, setCountry] = useState<CountryCode>("IN");
  const [show, setShow] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const pending = useRef(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current) return;
    setError("");
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
      let installation = localStorage.getItem("globalchat.admin.installation");
      if (!installation) {
        installation = crypto.randomUUID();
        localStorage.setItem("globalchat.admin.installation", installation);
      }
      const body = {
        email: form.email.trim(),
        password: form.password,
        device: {
          installation_id: installation,
          platform: "WEB",
          device_name: "GlobalChat Admin Browser",
        },
        ...(registration
          ? {
              company_name: form.company_name,
              owner_name: form.owner_name,
              phone,
            }
          : {}),
      };
      const tokens = await apiRequest<Tokens>(
        registration
          ? "/api/v1/auth/registration/company"
          : "/api/v1/auth/login",
        { public: true, method: "POST", body: JSON.stringify(body) },
      );
      setForm((previous) => ({ ...previous, password: "", confirm: "" }));
      await auth.login(tokens);
      router.replace("/dashboard");
    } catch (issue) {
      setError(
        issue instanceof Error
          ? issue.message
          : "Authentication is unavailable.",
      );
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
        className="mt-2 w-full rounded-xl border border-slate-300 bg-transparent px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />
    </label>
  );
  return (
    <main className="flex min-h-dvh items-center justify-center bg-slate-50 px-4 py-10 text-slate-900">
      <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
        <Link href="/login" className="font-bold text-indigo-600">
          GlobalChat
        </Link>
        <h1 className="mt-5 text-3xl font-semibold">
          {registration ? "Create your company" : "Welcome back"}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          {registration
            ? "Create your workspace and Owner account. No SMS verification required."
            : "Sign in with your workspace email and password."}
        </p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          {registration && (
            <>
              {field("company_name", "Company name")}
              {field("owner_name", "Owner name")}
            </>
          )}
          {field("email", "Email", "email")}
          {registration && (
            <CountryPhone
              country={country}
              onCountryChange={setCountry}
              value={form.phone}
              onChange={(phone) => setForm({ ...form, phone })}
              disabled={busy}
            />
          )}
          {field("password", "Password", show ? "text" : "password")}
          {registration &&
            field("confirm", "Confirm password", show ? "text" : "password")}
          <button
            type="button"
            aria-pressed={show}
            onClick={() => setShow(!show)}
            className="text-sm text-indigo-700 underline"
          >
            {show ? "Hide passwords" : "Show passwords"}
          </button>
          {registration && (
            <p className="text-xs text-slate-500">
              Use 12–128 characters. Phone and email are not marked verified by
              registration.
            </p>
          )}
          {error && (
            <p
              role="alert"
              className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700"
            >
              {error}
            </p>
          )}
          <Button type="submit" disabled={busy} className="w-full">
            {busy
              ? "Please wait…"
              : registration
                ? "Create Company"
                : "Sign In"}
          </Button>
        </form>
        <p className="mt-3 text-xs text-slate-500">
          Password reset is not available yet. Contact your workspace
          administrator for help.
        </p>
      </section>
    </main>
  );
}
