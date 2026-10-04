"use client";

import { useState } from "react";

import { apiRequest } from "@/lib/api/client";

import { useResource } from "@/lib/api/use-resource";

import type {
  OrganizationSettings,
  NotificationPreferences,
} from "@/lib/api/contracts";

import { useAuth } from "@/features/auth/auth-provider";

import { Button } from "@/components/ui/button";

import { Card } from "@/components/ui/card";

import { ErrorState } from "@/components/feedback/error-state";

export function SettingsClient({
  organizationOnly = false,
}: {
  organizationOnly?: boolean;
}) {
  const auth = useAuth();
  const org = useResource<OrganizationSettings>(
    "/api/v1/organizations/current/settings/",
  );
  const prefs = useResource<NotificationPreferences>(
    "/api/v1/notifications/preferences",
  );

  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);

  async function submit(
    e: React.FormEvent<HTMLFormElement>,
    target: "organization" | "notifications",
  ) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    const form = new FormData(e.currentTarget);
    try {
      await apiRequest(
        target === "organization"
          ? "/api/v1/organizations/current/settings/"
          : "/api/v1/notifications/preferences",
        {
          method: "PATCH",
          body: JSON.stringify(
            target === "organization"
              ? {
                  allow_member_invites:
                    form.get("allow_member_invites") === "on",
                  allow_group_creation:
                    form.get("allow_group_creation") === "on",
                  allow_external_chat: form.get("allow_external_chat") === "on",
                  default_timezone: String(form.get("default_timezone")),
                }
              : {
                  push_enabled: form.get("push_enabled") === "on",
                  notification_preview: String(form.get("preview")),
                },
          ),
        },
      );
      setNotice("Settings saved by the backend.");
      org.reload();
      prefs.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save settings.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      {error && (
        <p role="alert" className="text-rose-700">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="text-emerald-700">
          {notice}
        </p>
      )}
      <Card className="p-5">
        <h2 className="font-semibold">Current organization</h2>
        {org.loading ? (
          <p role="status">Loading…</p>
        ) : org.error ? (
          <ErrorState description={org.error} retry={org.reload} />
        ) : (
          org.data && (
            <form
              key={JSON.stringify(org.data)}
              onSubmit={(e) => void submit(e, "organization")}
              className="mt-4 space-y-3"
            >
              <fieldset
                disabled={busy || !auth.permissions.has("organization.update")}
                className="space-y-3"
              >
                {[
                  "allow_member_invites",
                  "allow_group_creation",
                  "allow_external_chat",
                ].map((key) => (
                  <label className="flex items-center gap-2" key={key}>
                    <input
                      type="checkbox"
                      name={key}
                      defaultChecked={Boolean(
                        org.data?.[key as keyof OrganizationSettings],
                      )}
                    />
                    {key.replaceAll("_", " ")}
                  </label>
                ))}
                <label className="block">
                  Default timezone
                  <input
                    name="default_timezone"
                    required
                    maxLength={64}
                    defaultValue={org.data.default_timezone}
                    className="ml-2 rounded border p-2"
                  />
                </label>
                <Button type="submit">Save organization settings</Button>
              </fieldset>
            </form>
          )
        )}
      </Card>
      {!organizationOnly && (
        <>
          <Card className="p-5">
            <h2 className="font-semibold">Your notification preferences</h2>
            <p className="text-sm text-slate-500">
              These settings belong to your own current membership; they do not
              configure other users.
            </p>
            {prefs.loading ? (
              <p role="status">Loading…</p>
            ) : prefs.error ? (
              <ErrorState description={prefs.error} retry={prefs.reload} />
            ) : (
              prefs.data && (
                <form
                  key={JSON.stringify(prefs.data)}
                  onSubmit={(e) => void submit(e, "notifications")}
                  className="mt-4 space-y-3"
                >
                  <fieldset disabled={busy} className="space-y-3">
                    <label className="flex gap-2">
                      <input
                        name="push_enabled"
                        type="checkbox"
                        defaultChecked={prefs.data.push_enabled}
                      />
                      Push notifications
                    </label>
                    <label className="block">
                      Content visibility
                      <select
                        name="preview"
                        defaultValue={prefs.data.preview}
                        className="ml-2 rounded border p-2"
                      >
                        {["FULL", "SENDER_ONLY", "NONE"].map((value) => (
                          <option key={value}>{value}</option>
                        ))}
                      </select>
                    </label>
                    <Button type="submit">Save notification preferences</Button>
                  </fieldset>
                </form>
              )
            )}
          </Card>
          <Card className="p-5 text-sm text-slate-500">
            Profile: {auth.profile?.display_name}. Account profile/privacy
            changes remain user-owned. Sound, group-specific notification
            controls and browser push are unavailable.
          </Card>
        </>
      )}
    </section>
  );
}
