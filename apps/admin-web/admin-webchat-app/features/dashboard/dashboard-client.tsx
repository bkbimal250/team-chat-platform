"use client";

import Link from "next/link";

import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/feedback/error-state";
import { useAuth } from "@/features/auth/auth-provider";
import { useResource } from "@/lib/api/use-resource";

type PlatformList = { total: number; items: { id: string }[] };
type ServiceStatus = {
  items: { name: string; live: boolean; ready: boolean }[];
};

export function DashboardClient() {
  const auth = useAuth();
  const organizations = useResource<PlatformList>(
    "/api/v1/platform/organizations/",
  );
  const identities = useResource<PlatformList>("/api/v1/platform/identities");
  const services = useResource<ServiceStatus>("/api/v1/platform/services");
  const cards = [
    ["Organizations", organizations, "/organizations"],
    ["Identities", identities, "/members"],
  ] as const;
  return (
    <main className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6">
      <header>
        <p className="text-xs font-medium uppercase tracking-wider text-indigo-700">
          Platform administration
        </p>
        <h1 className="mt-1 text-2xl font-semibold">
          Welcome, {auth.profile?.display_name || "Super Admin"}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          GlobalChat platform health and metadata. This account does not need a
          company membership.
        </p>
      </header>
      <section className="grid gap-3 sm:grid-cols-2">
        {cards.map(([label, resource, href]) => (
          <Card key={label} className="p-5">
            <Link
              href={href}
              className="text-sm font-medium text-indigo-700 hover:underline"
            >
              {label}
            </Link>
            {resource.loading ? (
              <div className="mt-3 h-8 w-12 animate-pulse rounded bg-slate-100" />
            ) : resource.error ? (
              <ErrorState
                description={resource.error}
                retry={resource.reload}
              />
            ) : (
              <p className="mt-2 text-3xl font-semibold tabular-nums">
                {resource.data?.total ?? resource.data?.items?.length ?? 0}
              </p>
            )}
          </Card>
        ))}
      </section>
      <Card className="p-5">
        <h2 className="font-semibold">Service health</h2>
        {services.loading ? (
          <p role="status" className="mt-3">
            Checking services…
          </p>
        ) : services.error ? (
          <ErrorState description={services.error} retry={services.reload} />
        ) : (
          <ul className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {services.data?.items?.map((service) => (
              <li key={service.name} className="rounded border p-3 text-sm">
                <span className="font-medium">{service.name}</span>
                <span
                  className={
                    service.live && service.ready
                      ? "ml-2 text-emerald-700"
                      : "ml-2 text-rose-700"
                  }
                >
                  {service.live && service.ready
                    ? "Healthy"
                    : "Needs attention"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </main>
  );
}
