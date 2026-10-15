"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";

export function SettingsClient({
  organizationOnly = false,
}: {
  organizationOnly?: boolean;
}) {
  if (organizationOnly) {
    return (
      <Card className="p-5 text-sm text-slate-500">
        Organization settings are tenant-scoped and are not available in
        platform administration.
      </Card>
    );
  }
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Card className="p-5">
        <h2 className="font-semibold">Platform administration</h2>
        <p className="mt-2 text-sm text-slate-500">
          Company settings and notification preferences require a company
          membership and are intentionally unavailable here.
        </p>
        <div className="mt-4 flex gap-4 text-sm">
          <Link className="text-indigo-700 underline" href="/profile">
            Platform profile
          </Link>
          <Link className="text-indigo-700 underline" href="/devices">
            Your sessions
          </Link>
        </div>
      </Card>
    </section>
  );
}
