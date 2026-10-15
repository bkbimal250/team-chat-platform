"use client";

import { ChevronRight, GitBranch, Mail, RefreshCw, Users, UsersRound } from "lucide-react";
import type { AppSection } from "@/components/navigation/app-nav-config";
import { useAuth } from "@/workspace/features/auth/auth-provider";
import { useResource } from "@/workspace/lib/api/use-resource";
import type { CursorPage, Organization, Audit } from "@/workspace/lib/api/contracts";
import { workspaceCapabilities } from "@/lib/auth/workspace-permissions";
import { refreshAdmin } from "@/workspace/lib/realtime/refresh";
import { Avatar } from "@/components/ui/avatar";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { ListRow } from "@/components/ui/list-row";
import { ErrorState } from "@/workspace/components/feedback/error-state";
import { ContentLayout } from "@/components/content/content-layout";
import { Section } from "@/components/content/section";
import { StatusPill } from "@/components/workspace/status-pill";
import { auditIconForAction, formatAuditEvent } from "./audit-present";

function countLabel(page: CursorPage<unknown> | null | undefined, loading?: boolean) {
  if (loading) return "…";
  const n = page?.results.length ?? 0;
  return page?.next ? `${n}+` : String(n);
}

function SummaryRow({
  icon: Icon,
  label,
  value,
  loading,
  onClick,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  loading?: boolean;
  onClick?: () => void;
}) {
  const body = (
    <>
      <Icon className={`${iconSize} shrink-0 text-aurora-muted`} aria-hidden />
      <span className="flex-1 text-sm">{label}</span>
      <span className="text-sm font-semibold tabular-nums">{loading ? "…" : value}</span>
      {onClick && <ChevronRight className={`${iconSize} text-aurora-muted`} aria-hidden />}
    </>
  );
  if (!onClick) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-aurora-border bg-aurora-surface px-3 py-2.5">
        {body}
      </div>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-3 rounded-xl border border-aurora-border bg-aurora-surface px-3 py-2.5 text-left transition-colors hover:bg-aurora-surface-alt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-aurora-primary"
    >
      {body}
    </button>
  );
}

export function OverviewContent({
  onNavigate,
}: {
  onNavigate?: (section: AppSection) => void;
}) {
  const auth = useAuth();
  const caps = workspaceCapabilities(auth.permissions);
  const org = useResource<Organization>(
    "/api/v1/organizations/current/",
    auth.permissions.has("organization.view"),
  );
  const members = useResource<CursorPage<{ id: string; display_name: string; roles: string[] }>>(
    "/api/v1/members/?page_size=5",
    caps.canViewMembers,
  );
  const teams = useResource<CursorPage<{ id: string }>>(
    "/api/v1/teams/?page_size=1",
    caps.canViewTeams,
  );
  const branches = useResource<CursorPage<{ id: string }>>(
    "/api/v1/branches/?page_size=1",
    caps.canViewBranches,
  );
  const audit = useResource<CursorPage<Audit>>(
    "/api/v1/audit-logs/?page_size=8",
    auth.permissions.has("audit.view"),
  );
  const invites = useResource<
    CursorPage<{ id: string; recipient_name: string; recipient_email: string; expires_at: string }>
  >(
    "/api/v1/invitations/?status=PENDING&page_size=5",
    auth.permissions.has("invitation.view"),
  );

  const name = org.data?.display_name || org.data?.name || "Workspace";

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <header className="border-b border-aurora-border bg-gradient-to-b from-aurora-surface to-aurora-background px-4 py-5 sm:px-6">
        <div className="flex items-center gap-4">
          <Avatar name={name} size="lg" />
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-semibold tracking-tight">{name}</h1>
            <p className="mt-0.5 text-sm text-aurora-muted">
              {auth.profile?.display_name
                ? `Signed in as ${auth.profile.display_name}`
                : "Your workspace home"}
            </p>
          </div>
          <IconButton label="Refresh workspace data" onClick={() => refreshAdmin()}>
            <RefreshCw className={iconSize} />
          </IconButton>
        </div>
      </header>
      <div className="space-y-5 p-4 sm:p-6">
        <ContentLayout width="medium">
        {org.error && <ErrorState description={org.error} retry={org.reload} />}
        <Section title="At a glance">
          <div className="grid gap-0 sm:grid-cols-2 sm:divide-x sm:divide-aurora-border">
            <SummaryRow
              icon={Users}
              label="Members"
              value={countLabel(members.data, members.loading)}
              loading={members.loading}
              onClick={caps.canViewMembers ? () => onNavigate?.("members") : undefined}
            />
            <SummaryRow
              icon={UsersRound}
              label="Teams"
              value={countLabel(teams.data, teams.loading)}
              loading={teams.loading}
              onClick={caps.canViewTeams ? () => onNavigate?.("teams") : undefined}
            />
            <SummaryRow
              icon={GitBranch}
              label="Branches"
              value={countLabel(branches.data, branches.loading)}
              loading={branches.loading}
              onClick={caps.canViewBranches ? () => onNavigate?.("branches") : undefined}
            />
            <SummaryRow
              icon={Mail}
              label="Pending invites"
              value={countLabel(invites.data, invites.loading)}
              loading={invites.loading}
              onClick={
                auth.permissions.has("invitation.view")
                  ? () => onNavigate?.("invitations")
                  : undefined
              }
            />
          </div>
        </Section>
        {caps.canViewMembers && (
          <section>
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-aurora-muted">
                Recent members
              </h2>
              {onNavigate && (
                <button
                  type="button"
                  onClick={() => onNavigate("members")}
                  className="text-xs font-medium text-aurora-primary hover:underline"
                >
                  View all
                </button>
              )}
            </div>
            {members.loading ? (
              <div className="h-24 animate-pulse rounded-xl bg-aurora-surface-alt" />
            ) : members.data?.results.length ? (
              <ul className="divide-y divide-aurora-border rounded-xl border border-aurora-border bg-aurora-surface">
                {members.data.results.map((m) => (
                  <li key={m.id}>
                    <ListRow
                      active={false}
                      onClick={() => onNavigate?.("members")}
                      leading={<Avatar name={m.display_name} />}
                      title={m.display_name}
                      subtitle={m.roles.length ? m.roles.join(", ") : "Member"}
                      trailing={
                        m.roles[0] ? <StatusPill>{m.roles[0]}</StatusPill> : undefined
                      }
                    />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-aurora-muted">No members yet.</p>
            )}
          </section>
        )}
        {auth.permissions.has("audit.view") && (
          <section>
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-aurora-muted">
              Recent activity
            </h2>
            {audit.loading ? (
              <div className="h-32 animate-pulse rounded-xl bg-aurora-surface-alt" />
            ) : audit.data?.results.length ? (
              <ul className="divide-y divide-aurora-border rounded-xl border border-aurora-border bg-aurora-surface">
                {audit.data.results.map((row) => {
                  const Icon = auditIconForAction(row.action, row.resource_type);
                  return (
                    <li key={row.id} className="flex items-start gap-3 px-3 py-2.5">
                      <span className="mt-0.5 rounded-lg bg-aurora-surface-alt p-2">
                        <Icon className={`${iconSize} text-aurora-muted`} aria-hidden />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">
                          {formatAuditEvent(row.action, row.resource_type)}
                        </p>
                        <time className="text-xs text-aurora-muted">
                          {new Date(row.created_at).toLocaleString([], {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })}
                        </time>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-sm text-aurora-muted">Activity will appear as your team makes changes.</p>
            )}
          </section>
        )}
        </ContentLayout>
      </div>
    </div>
  );
}
