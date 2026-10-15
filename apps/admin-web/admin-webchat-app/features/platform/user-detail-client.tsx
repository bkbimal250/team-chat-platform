"use client";

import Link from "next/link";
import { useState } from "react";

import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useResource } from "@/lib/api/use-resource";
import { SessionRevocationButton } from "./session-revocation";

type Identity = {
  id: string;
  email: string | null;
  status: string;
  created_at: string;
  email_verified: boolean;
  phone_verified: boolean;
};
type Membership = {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_display_name: string;
  status: string;
  roles: string[];
  joined_at: string | null;
};
type MembershipPage = { total: number; items: Membership[] };
type Session = {
  id: string;
  device_id: string;
  device_name: string | null;
  platform: string | null;
  device_status: string | null;
  status: string;
  created_at: string;
  last_activity_at: string;
  expires_at: string;
  revoked_at: string | null;
};
type SessionPage = { total: number; items: Session[] };

export function UserDetailClient({ identityId }: { identityId: string }) {
  const [sessionPage, setSessionPage] = useState(0);
  const identity = useResource<Identity>(
    `/api/v1/platform/identities/${identityId}`,
  );
  const memberships = useResource<MembershipPage>(
    `/api/v1/platform/identities/${identityId}/memberships/?limit=100`,
  );
  const sessions = useResource<SessionPage>(
    `/api/v1/platform/sessions?identity_id=${identityId}&limit=20&offset=${sessionPage * 20}`,
  );
  if (identity.loading || memberships.loading || sessions.loading)
    return <p role="status">Loading user…</p>;
  if (identity.error)
    return <ErrorState description={identity.error} retry={identity.reload} />;
  if (memberships.error)
    return (
      <ErrorState description={memberships.error} retry={memberships.reload} />
    );
  if (sessions.error)
    return <ErrorState description={sessions.error} retry={sessions.reload} />;
  if (!identity.data)
    return (
      <ErrorState
        title="User unavailable"
        description="The identity no longer exists or is unavailable."
      />
    );
  return (
    <section className="space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">
          {identity.data.email || "Identity"}
        </h1>
        <p className="text-sm text-slate-500">
          Platform-safe identity and organization memberships.
        </p>
      </header>
      <Card className="p-5">
        <h2 className="font-semibold">Profile & identity</h2>
        <dl className="mt-3 grid gap-2 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-slate-500">Email</dt>
            <dd>{identity.data.email || "Unavailable"}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-500">Status</dt>
            <dd>{identity.data.status}</dd>
          </div>
          <div>
            <dt className="text-sm text-slate-500">Verified</dt>
            <dd>
              {identity.data.email_verified ? "Email" : "—"}
              {identity.data.phone_verified ? " · Phone" : ""}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-slate-500">Created</dt>
            <dd>{new Date(identity.data.created_at).toLocaleString()}</dd>
          </div>
        </dl>
      </Card>
      <Card className="p-5">
        <h2 className="font-semibold">
          Organizations & memberships{" "}
          <span className="text-sm font-normal text-slate-500">
            {memberships.data?.total ?? 0}
          </span>
        </h2>
        {memberships.data?.items.length ? (
          <ul className="mt-3 divide-y">
            {memberships.data.items.map((membership) => (
              <li
                key={membership.id}
                className="flex justify-between gap-3 py-3"
              >
                <div>
                  <Link
                    className="font-medium text-indigo-700 underline"
                    href={`/organizations/${membership.organization_id}`}
                  >
                    {membership.organization_display_name ||
                      membership.organization_name}
                  </Link>
                  <p className="text-sm text-slate-500">
                    {membership.roles.join(", ") || "No role"} ·{" "}
                    {membership.status}
                  </p>
                </div>
                <time className="text-xs text-slate-500">
                  {membership.joined_at
                    ? new Date(membership.joined_at).toLocaleDateString()
                    : "—"}
                </time>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            This user has no linked organization memberships.
          </p>
        )}
      </Card>
      <SessionsCard
        identityId={identityId}
        sessions={sessions.data?.items ?? []}
        total={sessions.data?.total ?? 0}
        page={sessionPage}
        onPageChange={setSessionPage}
        onRefresh={sessions.reload}
      />
    </section>
  );
}

function SessionsCard({
  identityId,
  sessions,
  total,
  page,
  onPageChange,
  onRefresh,
}: {
  identityId: string;
  sessions: Session[];
  total: number;
  page: number;
  onPageChange: (page: number) => void;
  onRefresh: () => void;
}) {
  const hasNextPage = (page + 1) * 20 < total;
  return (
    <Card className="overflow-x-auto p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold">
          Sessions{" "}
          <span className="text-sm font-normal text-slate-500">{total}</span>
        </h2>
        <SessionRevocationButton
          identityId={identityId}
          revokeAll
          onComplete={onRefresh}
        />
      </div>
      {sessions.length ? (
        <>
          <table className="mt-3 w-full text-left text-sm">
            <thead>
              <tr className="border-b text-slate-500">
                <th className="p-2">Device</th>
                <th className="p-2">Status</th>
                <th className="p-2">Created</th>
                <th className="p-2">Last activity</th>
                <th className="p-2">Expires</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.id} className="border-b">
                  <td className="p-2">
                    {session.device_name || "Device information unavailable"}
                    <p className="text-xs text-slate-500">
                      {session.platform || "—"}
                    </p>
                  </td>
                  <td className="p-2">{session.status}</td>
                  <td className="p-2">
                    {new Date(session.created_at).toLocaleString()}
                  </td>
                  <td className="p-2">
                    {new Date(session.last_activity_at).toLocaleString()}
                  </td>
                  <td className="p-2">
                    {new Date(session.expires_at).toLocaleString()}
                  </td>
                  <td className="p-2">
                    <SessionRevocationButton
                      identityId={identityId}
                      session={session}
                      onComplete={onRefresh}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <nav
            className="mt-4 flex items-center justify-end gap-2"
            aria-label="Session pagination"
          >
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => onPageChange(page - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-slate-500">Page {page + 1}</span>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!hasNextPage}
              onClick={() => onPageChange(page + 1)}
            >
              Next
            </Button>
          </nav>
        </>
      ) : (
        <p className="mt-3 text-sm text-slate-500">
          This user has no sessions.
        </p>
      )}
    </Card>
  );
}
