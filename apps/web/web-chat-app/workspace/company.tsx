"use client";
import { useResource } from "./lib/api/use-resource";
import { useAuth } from "./features/auth/auth-provider";
import { SettingsClient } from "./features/settings/settings-client";
import { apiRequest } from "./lib/api/client";
import { useState } from "react";
import type { Organization, CursorPage } from "./lib/api/contracts";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { Field, Input } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Section } from "@/components/content/section";
import { DetailRow } from "@/components/content/detail-row";
import { ListRow } from "@/components/ui/list-row";
import { Avatar } from "@/components/ui/avatar";

export function Company() {
  const auth = useAuth();
  const permitted = auth.permissions.has("organization.view");
  const org = useResource<Organization>("/api/v1/organizations/current/", permitted);
  const members = useResource<CursorPage<{ id: string; display_name: string; roles: string[] }>>(
    "/api/v1/members/?page_size=50",
    auth.permissions.has("member.view"),
  );
  const roles = useResource<CursorPage<{ id: string; name: string; kind: string }>>(
    "/api/v1/roles/?page_size=50",
    auth.permissions.has("role.view"),
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const ownerNames = new Set(roles.data?.results.filter((r) => r.kind === "OWNER").map((r) => r.name));
  if (!permitted) return <p role="alert" className="p-6">Your role does not grant company access.</p>;
  const title = org.data?.display_name || org.data?.name || "Company";
  return (
    <DetailScaffold width="medium" title={title} subtitle={org.data?.email || "Organization profile"} avatarName={title}>
      {org.loading && <p role="status" className="text-sm text-aurora-muted">Loading company…</p>}
      {org.error && <AlertBanner message={org.error} />}
      {org.data && (
        <>
          <Section title="Organization">
            <dl>
              <DetailRow label="Country" value={org.data.country_code} />
              <DetailRow label="Timezone" value={org.data.timezone} />
            </dl>
          </Section>
          {auth.permissions.has("organization.update") && (
            <form
              key={org.data.id}
              className="mt-4 space-y-4"
              onSubmit={async (event) => {
                event.preventDefault();
                if (busy) return;
                const data = new FormData(event.currentTarget);
                setBusy(true);
                setError("");
                try {
                  await apiRequest("/api/v1/organizations/current/", {
                    method: "PATCH",
                    body: JSON.stringify({ display_name: data.get("display_name") }),
                  });
                  org.reload();
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Unable to update company.");
                } finally {
                  setBusy(false);
                }
              }}
            >
              <Field label="Display name">
                <Input name="display_name" required maxLength={200} defaultValue={org.data.display_name} />
              </Field>
              <Button type="submit" variant="primary" disabled={busy}>Save company</Button>
              {error && <AlertBanner message={error} />}
            </form>
          )}
        </>
      )}
      {auth.permissions.has("member.view") && auth.permissions.has("role.view") && (
        <Section title="Owners">
          <ul className="divide-y divide-aurora-border">
            {members.data?.results
              .filter((m) => m.roles.some((r) => ownerNames.has(r)))
              .map((m) => (
                <li key={m.id}>
                  <ListRow
                    active={false}
                    onClick={() => {}}
                    leading={<Avatar name={m.display_name} />}
                    title={m.display_name}
                    subtitle="Organization owner"
                  />
                </li>
              ))}
          </ul>
        </Section>
      )}
      <div className="mt-6 border-t border-aurora-border pt-6">
        <SettingsClient organizationOnly />
      </div>
    </DetailScaffold>
  );
}
