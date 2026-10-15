"use client";

import Link from "next/link";
import { useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { Organization } from "@/lib/api/contracts";
import { useResource } from "@/lib/api/use-resource";

type Membership = {
  id: string;
  user_id: string | null;
  display_name: string;
  status: string;
  joined_at: string | null;
  roles: string[];
};
type Named = { id: string; name: string; status: string };
type Detail = Organization & { branches?: Named[]; teams?: Named[] };
type Page<T> = { total: number; items: T[] };
type Invitation = { id: string; recipient_name: string; recipient_email: string | null; role: string; status: string; created_at: string; expires_at: string };
type SecuritySummary = { owners: number; administrators: number; active_members: number; inactive_members: number; member_statuses: Record<string, number>; invitation_statuses: Record<string, number> };

export function OrganizationDetailClient({ organizationId }: { organizationId: string }) {
  const [tab, setTab] = useState("Overview");
  const org = useResource<Detail>(`/api/v1/platform/organizations/${organizationId}/`);
  const owners = useResource<Page<Membership>>(
    `/api/v1/platform/organizations/${organizationId}/owners/`,
    tab === "Owners",
  );
  const members = useResource<Page<Membership>>(
    `/api/v1/platform/organizations/${organizationId}/memberships/?limit=100`,
    tab === "Members",
  );
  const invitations = useResource<Page<Invitation>>(
    `/api/v1/platform/organizations/${organizationId}/invitations/?limit=100`,
    tab === "Invitations",
  );
  const security = useResource<SecuritySummary>(
    `/api/v1/platform/organizations/${organizationId}/security/`,
    tab === "Security",
  );
  if (org.loading) return <p role="status">Loading organization…</p>;
  if (org.error) return <ErrorState description={org.error} retry={org.reload} />;
  if (!org.data) return <ErrorState title="Organization unavailable" description="The organization no longer exists or is unavailable." />;
  const tabs = ["Overview", "Owners", "Members", "Branches", "Teams", "Invitations", "Security", "Diagnostics"];
  const resources = tab === "Branches" ? org.data.branches : org.data.teams;
  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">{org.data.display_name || org.data.name}</h1>
        <p className="text-sm text-slate-500">Read-only platform organization administration.</p>
      </header>
      <nav aria-label="Organization sections" className="flex flex-wrap gap-2">
        {tabs.map((name) => <Button key={name} aria-current={name === tab ? "page" : undefined} variant={name === tab ? "primary" : "outline"} onClick={() => setTab(name)}>{name}</Button>)}
      </nav>
      {tab === "Overview" && <Card className="p-5"><h2 className="font-semibold">Organization information</h2><dl className="mt-3 grid gap-2 sm:grid-cols-2"><div><dt className="text-sm text-slate-500">Name</dt><dd>{org.data.name}</dd></div><div><dt className="text-sm text-slate-500">Status</dt><dd>{org.data.status}</dd></div><div><dt className="text-sm text-slate-500">Created</dt><dd>{new Date(org.data.created_at).toLocaleString()}</dd></div></dl></Card>}
      {tab === "Owners" && <MembershipList title="Owners" resource={owners} />}
      {tab === "Members" && <MembershipList title="Members" resource={members} />}
      {tab === "Invitations" && <InvitationList resource={invitations} />}
      {tab === "Security" && <SecuritySummaryCard resource={security} />}
      {["Branches", "Teams"].includes(tab) && <Card className="p-5"><h2 className="font-semibold">{tab}</h2>{resources?.length ? <ul className="mt-3 divide-y">{resources.map((row) => <li key={row.id} className="py-2 text-sm">{row.name} <span className="text-slate-500">· {row.status}</span></li>)}</ul> : <p className="mt-3 text-sm text-slate-500">No {tab.toLowerCase()} are available.</p>}</Card>}
      {tab === "Diagnostics" && <Card className="p-5 text-sm text-slate-500">Diagnostics are not available in the current platform contract.</Card>}
    </section>
  );
}

function SecuritySummaryCard({ resource }: { resource: ReturnType<typeof useResource<SecuritySummary>> }) {
  if (resource.loading) return <p role="status">Loading security summary…</p>;
  if (resource.error) return <ErrorState description={resource.error} retry={resource.reload} />;
  if (!resource.data) return null;
  const facts = [["Owners", resource.data.owners], ["Administrators", resource.data.administrators], ["Active members", resource.data.active_members], ["Inactive memberships", resource.data.inactive_members]];
  return <section className="space-y-4"><Card className="p-5"><h2 className="font-semibold">Security overview</h2><p className="mt-1 text-sm text-slate-500">Factual membership and invitation status. No score or inferred risk level.</p><dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{facts.map(([label, value]) => <div key={String(label)}><dt className="text-sm text-slate-500">{label}</dt><dd className="text-2xl font-semibold">{value}</dd></div>)}</dl></Card><StatusFacts title="Membership status" statuses={resource.data.member_statuses} /><StatusFacts title="Invitation status" statuses={resource.data.invitation_statuses} /></section>;
}

function StatusFacts({ title, statuses }: { title: string; statuses: Record<string, number> }) {
  const facts = Object.entries(statuses);
  return <Card className="p-5"><h2 className="font-semibold">{title}</h2>{facts.length ? <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{facts.map(([status, count]) => <div key={status}><dt className="text-sm text-slate-500">{status}</dt><dd className="text-xl font-semibold">{count}</dd></div>)}</dl> : <p className="mt-3 text-sm text-slate-500">No records.</p>}</Card>;
}

function InvitationList({ resource }: { resource: ReturnType<typeof useResource<Page<Invitation>>> }) {
  if (resource.loading) return <p role="status">Loading invitations…</p>;
  if (resource.error) return <ErrorState description={resource.error} retry={resource.reload} />;
  const rows = resource.data?.items ?? [];
  return <Card className="p-5"><h2 className="font-semibold">Invitations <span className="text-sm font-normal text-slate-500">{resource.data?.total ?? 0}</span></h2>{rows.length ? <ul className="mt-3 divide-y">{rows.map((row) => <li key={row.id} className="py-3"><p className="font-medium">{row.recipient_name || row.recipient_email || "Recipient unavailable"}</p><p className="text-sm text-slate-500">{row.role} · {row.status} · expires {new Date(row.expires_at).toLocaleDateString()}</p></li>)}</ul> : <p className="mt-3 text-sm text-slate-500">No invitations are available.</p>}</Card>;
}

function MembershipList({ title, resource }: { title: string; resource: ReturnType<typeof useResource<Page<Membership>>> }) {
  if (resource.loading) return <p role="status">Loading {title.toLowerCase()}…</p>;
  if (resource.error) return <ErrorState description={resource.error} retry={resource.reload} />;
  const rows = resource.data?.items ?? [];
  return <Card className="p-5"><h2 className="font-semibold">{title} <span className="text-sm font-normal text-slate-500">{resource.data?.total ?? 0}</span></h2>{rows.length ? <ul className="mt-3 divide-y">{rows.map((row) => <li key={row.id} className="flex items-center justify-between gap-3 py-3"><div><p className="font-medium">{row.user_id ? <Link className="text-indigo-700 underline" href={`/users/${row.user_id}`}>{row.display_name}</Link> : row.display_name}</p><p className="text-sm text-slate-500">{row.roles.join(", ") || "No role"} · {row.status}</p></div><time className="text-xs text-slate-500">{row.joined_at ? new Date(row.joined_at).toLocaleDateString() : "—"}</time></li>)}</ul> : <p className="mt-3 text-sm text-slate-500">No {title.toLowerCase()} are available.</p>}</Card>;
}
