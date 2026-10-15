"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/feedback/error-state";
import { useResource } from "@/lib/api/use-resource";

type PlatformAccess = {
  identity_id: string;
  role: string;
  permissions: string[];
};

export function ProfileClient() {
  const access = useResource<PlatformAccess>("/api/v1/platform/me");
  return (
    <section className="mx-auto max-w-3xl space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">Platform profile</h1>
        <p className="mt-1 text-sm text-slate-500">
          Platform access is separate from company workspace membership.
        </p>
      </header>
      <Card className="p-5">
        {access.loading ? (
          <p role="status">Loading platform access…</p>
        ) : access.error ? (
          <ErrorState description={access.error} retry={access.reload} />
        ) : (
          <>
            <h2 className="font-semibold">{access.data?.role}</h2>
            <p className="mt-2 text-sm text-slate-500">
              This local account has platform administration access and no
              tenant membership is required.
            </p>
            <p className="mt-4 text-sm font-medium">Permissions</p>
            <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
              {access.data?.permissions?.map((permission) => (
                <li key={permission}>{permission}</li>
              ))}
            </ul>
          </>
        )}
      </Card>
      <Card className="p-5 text-sm">
        <Link className="text-indigo-700 underline" href="/devices">
          Manage your own sessions
        </Link>
      </Card>
    </section>
  );
}
