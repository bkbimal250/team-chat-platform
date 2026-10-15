"use client";

import { useEffect, useMemo, useState } from "react";
import { Bell, Eye } from "lucide-react";
import { notify } from "@/components/ui/toast";
import { apiRequest } from "@/lib/api/client";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { Switch } from "@/components/ui/switch";
import { ActionBar } from "@/components/content/action-bar";
import { Section } from "@/components/content/section";
import { SettingRow } from "@/components/content/setting-row";
import { previewModeLabel } from "@/components/content/labels";

type Preferences = { push_enabled: boolean; preview: string };

export function NotificationSettings({ token }: { token: string }) {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [baseline, setBaseline] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [permission, setPermission] = useState<string>("checking");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const timer = setTimeout(
      () =>
        setPermission(
          typeof Notification === "undefined" ? "unsupported" : Notification.permission,
        ),
      0,
    );
    let active = true;
    apiRequest<Preferences>("/api/v1/notifications/preferences", {}, token)
      .then((row) => {
        if (active) {
          setPreferences(row);
          setBaseline(JSON.stringify(row));
        }
      })
      .catch(() => {
        if (active) setError("Notification preferences unavailable.");
      });
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [token, retry]);

  const dirty = useMemo(
    () => !!preferences && baseline && JSON.stringify(preferences) !== baseline,
    [preferences, baseline],
  );

  async function requestPermission() {
    try {
      setPermission(await Notification.requestPermission());
    } catch {
      setError("Notification permission could not be requested.");
    }
  }

  async function save() {
    if (!preferences || busy) return;
    setBusy(true);
    setSaved(false);
    setError("");
    try {
      const row = await apiRequest<Preferences>(
        "/api/v1/notifications/preferences",
        {
          method: "PATCH",
          body: JSON.stringify({
            push_enabled: preferences.push_enabled,
            notification_preview: preferences.preview,
          }),
        },
        token,
      );
      setPreferences(row);
      setBaseline(JSON.stringify(row));
      setSaved(true);
      notify("Settings saved.");
    } catch {
      setError("Preferences were not saved. Please retry.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <DetailScaffold
      width="narrow"
      title="Notifications"
      subtitle="Push alerts and how much message content to show."
    >
      <Section title="This browser">
        <SettingRow
          icon={Bell}
          title="Browser permission"
          description={
            permission === "denied"
              ? "Notifications are blocked in your browser settings."
              : permission === "granted"
                ? "This browser can show notifications when push is enabled."
                : "Allow notifications when prompted."
          }
          control={
            permission === "default" ? (
              <Button type="button" variant="outline" onClick={() => void requestPermission()}>
                Allow notifications
              </Button>
            ) : (
              <span className="text-sm capitalize text-aurora-muted">{permission}</span>
            )
          }
        />
        <p className="px-4 pb-3 text-xs text-aurora-muted">
          Delivery also depends on your workspace push configuration.
        </p>
      </Section>
      {error && (
        <div className="mb-4">
          <AlertBanner message={error} />
          <button
            type="button"
            className="mt-2 text-sm underline"
            onClick={() => {
              setError("");
              setRetry((v) => v + 1);
            }}
          >
            Retry loading
          </button>
        </div>
      )}
      {!preferences ? (
        <p role="status" className="animate-pulse text-sm text-aurora-muted">Loading preferences…</p>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <Section title="Alerts">
            <SettingRow
              icon={Bell}
              title="Message push notifications"
              description="Receive push alerts for new messages when supported."
              control={
                <Switch
                  label="Message push notifications"
                  checked={preferences.push_enabled}
                  onChange={(v) => {
                    setSaved(false);
                    setPreferences({ ...preferences, push_enabled: v });
                  }}
                />
              }
            />
            <SettingRow
              icon={Eye}
              title="Content visibility"
              description="How much of a message appears in the notification banner."
              control={
                <select
                  aria-label="Content visibility"
                  className="min-w-[10rem] rounded-lg border border-aurora-border bg-aurora-background px-2.5 py-1.5 text-sm"
                  value={preferences.preview}
                  onChange={(e) => {
                    setSaved(false);
                    setPreferences({ ...preferences, preview: e.target.value });
                  }}
                >
                  {["FULL", "SENDER_ONLY", "NONE"].map((value) => (
                    <option key={value} value={value}>{previewModeLabel(value)}</option>
                  ))}
                </select>
              }
            />
          </Section>
          {(dirty || saved) && (
            <ActionBar>
              <Button type="submit" variant="primary" disabled={busy || !dirty}>
                {busy ? "Saving…" : "Save preferences"}
              </Button>
              {saved && !dirty && (
                <p role="status" className="text-sm text-aurora-muted">Preferences saved.</p>
              )}
            </ActionBar>
          )}
        </form>
      )}
    </DetailScaffold>
  );
}
