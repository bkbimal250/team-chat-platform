"use client";

import { useState } from "react";

import { useResource } from "@/lib/api/use-resource";

import type { Organization } from "@/lib/api/contracts";

import { ResourceScreen } from "@/features/admin/resource-screen";

import { SettingsClient } from "@/features/settings/settings-client";

import { ErrorState } from "@/components/feedback/error-state";

import { Card } from "@/components/ui/card";

import { Button } from "@/components/ui/button";

export function OrganizationDetailClient({
  organizationId,
}: {
  organizationId: string;
}) {
  const org = useResource<Organization>("/api/v1/organizations/current/");
  const [tab, setTab] = useState("Overview");

  if (org.loading) return <p role="status">Loading organization…</p>;

  if (org.error)
    return <ErrorState description={org.error} retry={org.reload} />;

  if (!org.data || org.data.id !== organizationId)
    return (
      <ErrorState
        title="Organization unavailable"
        description="This organization is outside your current session or does not exist."
      />
    );

  return (
    <section className="space-y-5">
      <h1 className="text-2xl font-semibold">
        {org.data.display_name || org.data.name}
      </h1>
      <nav aria-label="Organization sections" className="flex flex-wrap gap-2">
        {["Overview", "Branches", "Teams", "Members", "Settings", "Audit"].map(
          (t) => (
            <Button
              key={t}
              aria-current={t === tab ? "page" : undefined}
              variant={t === tab ? "primary" : "outline"}
              onClick={() => setTab(t)}
            >
              {t}
            </Button>
          ),
        )}
      </nav>
      {tab === "Overview" ? (
        <>
          <Card className="p-5">
            <h2 className="font-semibold">Workspace information</h2>
            <dl className="mt-3 grid gap-2 sm:grid-cols-2">
              {["name", "slug", "status", "timezone", "country_code"].map(
                (key) => (
                  <div key={key}>
                    <dt className="text-sm text-slate-500">{key}</dt>
                    <dd>
                      {String(org.data?.[key as keyof Organization] ?? "—")}
                    </dd>
                  </div>
                ),
              )}
            </dl>
          </Card>
          <h2 className="font-semibold">Recent members</h2>
          <ResourceScreen resource="members" compact />
          <h2 className="font-semibold">Recent activity</h2>
          <ResourceScreen resource="audit-logs" compact />
        </>
      ) : tab === "Settings" ? (
        <SettingsClient organizationOnly />
      ) : (
        <ResourceScreen
          key={tab}
          resource={tab === "Audit" ? "audit-logs" : tab.toLowerCase()}
          compact
        />
      )}
    </section>
  );
}
