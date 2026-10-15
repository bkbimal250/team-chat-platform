"use client";

import { useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/feedback/error-state";
import { useResource } from "@/lib/api/use-resource";

type Identity = {
  id: string;
  email: string | null;
  status: string;
  created_at: string;
  email_verified: boolean;
  phone_verified: boolean;
  platform_role?: string;
};
type Session = {
  id: string;
  identity_id: string;
  device_name: string | null;
  platform: string | null;
  status: string;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
};
type Audit = {
  id: string;
  actor: string;
  action: string;
  target: string;
  result: string;
  created_at: string;
};
type List<T> = { items: T[]; total?: number };

export function IdentitiesTable({
  adminsOnly = false,
}: {
  adminsOnly?: boolean;
}) {
  const [search, setSearch] = useState("");
  const data = useResource<List<Identity>>(
    `${adminsOnly ? "/api/v1/platform/admins" : `/api/v1/platform/identities?limit=100${search ? `&search=${encodeURIComponent(search)}` : ""}`}`,
  );
  return (
    <section className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">
          {adminsOnly ? "Platform Administrators" : "Users"}
        </h1>
        <p className="text-sm text-slate-500">
          {adminsOnly
            ? "Persistent platform grants are read-only in this release."
            : "Authentication identities across GlobalChat. No passwords, tokens or phone numbers are shown."}
        </p>
      </header>
      {!adminsOnly && (
        <input
          aria-label="Search users"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search email or identity ID"
          className="w-full max-w-md rounded border p-2"
        />
      )}
      <Card className="overflow-x-auto p-5">
        {data.loading ? (
          <p role="status">Loading identities…</p>
        ) : data.error ? (
          <ErrorState description={data.error} retry={data.reload} />
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="p-2">Identity</th>
                {adminsOnly && <th className="p-2">Platform role</th>}
                <th className="p-2">Status</th>
                <th className="p-2">Verified</th>
                <th className="p-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.data?.items.map((row) => (
                <tr key={row.id} className="border-b">
                  <td className="p-2">
                    <Link className="text-indigo-700 underline" href={`/users/${row.id}`}>{row.email || "Email unavailable"}</Link>
                    <code className="text-xs text-slate-500">{row.id}</code>
                  </td>
                  {adminsOnly && <td className="p-2">{row.platform_role}</td>}
                  <td className="p-2">{row.status}</td>
                  <td className="p-2">
                    {row.email_verified ? "Email" : "—"}
                    {row.phone_verified ? " · Phone" : ""}
                  </td>
                  <td className="p-2">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </section>
  );
}

export function SessionsTable() {
  const data = useResource<List<Session>>(
    "/api/v1/platform/sessions?limit=100",
  );
  return (
    <section className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Sessions</h1>
        <p className="text-sm text-slate-500">
          Safe session metadata only. Tokens and device secrets are never
          exposed.
        </p>
      </header>
      <Card className="overflow-x-auto p-5">
        {data.loading ? (
          <p role="status">Loading sessions…</p>
        ) : data.error ? (
          <ErrorState description={data.error} retry={data.reload} />
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="p-2">Device</th>
                <th className="p-2">Identity</th>
                <th className="p-2">Status</th>
                <th className="p-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {data.data?.items.map((row) => (
                <tr key={row.id} className="border-b">
                  <td className="p-2">{row.device_name || "Device information unavailable"}<p className="text-xs text-slate-500">{row.platform || "—"}</p></td>
                  <td className="p-2">
                    <Link className="text-indigo-700 underline" href={`/users/${row.identity_id}`}>View user</Link>
                  </td>
                  <td className="p-2">{row.status}</td>
                  <td className="p-2">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </section>
  );
}
export function AuditTable() {
  const data = useResource<List<Audit>>("/api/v1/platform/audit?limit=100");
  return (
    <section className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Platform audit</h1>
        <p className="text-sm text-slate-500">
          Platform-grant operations only; no credentials or payload secrets.
        </p>
      </header>
      <Card className="overflow-x-auto p-5">
        {data.loading ? (
          <p role="status">Loading audit records…</p>
        ) : data.error ? (
          <ErrorState description={data.error} retry={data.reload} />
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="p-2">When</th>
                <th className="p-2">Actor</th>
                <th className="p-2">Action</th>
                <th className="p-2">Target</th>
                <th className="p-2">Result</th>
              </tr>
            </thead>
            <tbody>
              {data.data?.items.map((row) => (
                <tr key={row.id} className="border-b">
                  <td className="p-2">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="p-2">{row.actor}</td>
                  <td className="p-2">{row.action}</td>
                  <td className="p-2">{row.target}</td>
                  <td className="p-2">{row.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </section>
  );
}
export function ServicesTable() {
  const data = useResource<{
    items: { name: string; live: boolean; ready: boolean }[];
  }>("/api/v1/platform/services");
  return (
    <section className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Services</h1>
        <p className="text-sm text-slate-500">
          Live and readiness checks only. Configuration and credentials are
          never exposed.
        </p>
      </header>
      <Card className="p-5">
        {data.loading ? (
          <p role="status">Checking services…</p>
        ) : data.error ? (
          <ErrorState description={data.error} retry={data.reload} />
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.data?.items.map((service) => (
              <li key={service.name} className="rounded border p-4">
                <p className="font-medium">{service.name}</p>
                <p
                  className={
                    service.live && service.ready
                      ? "text-sm text-emerald-700"
                      : "text-sm text-rose-700"
                  }
                >
                  {service.live && service.ready ? "Healthy" : "Unavailable"}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </section>
  );
}
