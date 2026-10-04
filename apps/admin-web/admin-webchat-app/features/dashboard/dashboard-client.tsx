"use client";

import Link from "next/link";

import { useResource } from "@/lib/api/use-resource";

import type {
  Organization,
  Member,
  Branch,
  Team,
  CursorPage,
  Audit,
} from "@/lib/api/contracts";

import { Card } from "@/components/ui/card";

import { Button } from "@/components/ui/button";

import { ErrorState } from "@/components/feedback/error-state";

import { useAuth } from "@/features/auth/auth-provider";

function LoadedMetric({ title, path }: { title: string; path: string }) {
  const response = useResource<CursorPage<Member | Branch | Team>>(path);
  return (
    <Card className="p-5">
      <h2 className="text-sm text-slate-500">{title}</h2>
      {response.loading ? (
        <p role="status">Loading…</p>
      ) : response.error ? (
        <ErrorState description={response.error} retry={response.reload} />
      ) : (
        <>
          <p className="mt-2 text-2xl font-semibold">
            {response.data?.results.length}
            {response.data?.next ? "+" : ""}
          </p>
          <p className="text-xs text-slate-500">
            {response.data?.next
              ? "First 50 records; more exist"
              : "Records visible in your current organization"}
          </p>
        </>
      )}
    </Card>
  );
}

export function DashboardClient() {
  const auth = useAuth();
  const org = useResource<Organization>("/api/v1/organizations/current/");
  const audit = useResource<CursorPage<Audit>>(
    "/api/v1/audit-logs/?page_size=5",
  );

  return (
    <main className="mx-auto max-w-7xl space-y-5 p-4 sm:p-6">
      <header>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-slate-500">
          {org.data?.display_name || org.data?.name || "Current workspace"} ·
          Real organization data
        </p>
      </header>
      {org.error && <ErrorState description={org.error} retry={org.reload} />}
      <section className="grid gap-4 md:grid-cols-3">
        <LoadedMetric title="Members" path="/api/v1/members/?page_size=50" />
        <LoadedMetric title="Branches" path="/api/v1/branches/?page_size=50" />
        <LoadedMetric title="Teams" path="/api/v1/teams/?page_size=50" />
      </section>
      <Card className="p-5">
        <h2 className="font-semibold">Recent organization activity</h2>
        {!auth.permissions.has("audit.view") ? (
          <p className="mt-3 text-sm text-slate-500">
            Audit access is restricted by your role.
          </p>
        ) : audit.loading ? (
          <p role="status">Loading activity…</p>
        ) : audit.error ? (
          <ErrorState description={audit.error} retry={audit.reload} />
        ) : audit.data?.results.length ? (
          <ul className="divide-y">
            {audit.data.results.map((row) => (
              <li
                className="flex flex-wrap justify-between gap-2 py-3 text-sm"
                key={row.id}
              >
                <span>
                  {row.action} · {row.resource_type}
                </span>
                <time dateTime={row.created_at}>
                  {new Date(row.created_at).toLocaleString()}
                </time>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm">No activity recorded.</p>
        )}
        <Button
          variant="outline"
          className="mt-3"
          onClick={() => {
            org.reload();
            audit.reload();
          }}
        >
          Refresh overview
        </Button>
      </Card>
      <Card className="p-5 text-sm text-slate-500">
        <h2 className="font-semibold text-slate-900">
          Unavailable platform analytics
        </h2>
        <p className="mt-2">
          Growth charts, online-user counts, system-wide conversations and
          billing metrics have no authorized backend contract. No simulated
          statistics are shown.
        </p>
        <Link
          className="mt-3 inline-block text-indigo-700 underline"
          href="/organizations"
        >
          Open current organization
        </Link>
      </Card>
    </main>
  );
}
