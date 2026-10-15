"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Eye,
  Image,
  MessageSquare,
  Phone,
  Radio,
  User,
} from "lucide-react";
import { ProfilePhotoSettings } from "./profile-photo";
import { notify } from "@/components/ui/toast";
import { apiRequest } from "@/lib/api/client";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { Field, Input, TextArea } from "@/components/ui/field";
import { Switch } from "@/components/ui/switch";
import { ActionBar } from "@/components/content/action-bar";
import { Section } from "@/components/content/section";
import { SettingRow } from "@/components/content/setting-row";
import { VisibilitySelect } from "@/components/content/visibility-select";

type PrivacyData = Record<string, string | boolean>;

const PRIVACY_KEYS = [
  "profile_photo_visibility",
  "about_visibility",
  "online_status_visibility",
  "last_seen_visibility",
  "read_receipts_enabled",
  "discoverable",
] as const;

function snapshot(data: PrivacyData) {
  return JSON.stringify(data);
}

export function ProfileSettings({ token, privacy = false }: { token: string; privacy?: boolean }) {
  const [data, setData] = useState<PrivacyData | null>(null);
  const [baseline, setBaseline] = useState("");
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const path = privacy ? "/api/v1/users/me/privacy" : "/api/v1/users/me";

  useEffect(() => {
    let active = true;
    apiRequest<PrivacyData>(path, {}, token)
      .then((row) => {
        if (active) {
          setData(row);
          setBaseline(snapshot(row));
        }
      })
      .catch(() => {
        if (active) setError("Settings could not be loaded.");
      });
    return () => {
      active = false;
    };
  }, [path, token, retry]);

  const dirty = useMemo(
    () => !!data && baseline && snapshot(data) !== baseline,
    [data, baseline],
  );

  async function save() {
    if (!data || busy) return;
    setBusy(true);
    setSaved(false);
    setError("");
    const payload = privacy
      ? Object.fromEntries(PRIVACY_KEYS.map((key) => [key, data[key]]))
      : { display_name: data.display_name, about: data.about };
    try {
      const result = await apiRequest<PrivacyData>(path, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }, token);
      setData(result);
      setBaseline(snapshot(result));
      setSaved(true);
      notify("Settings saved.");
    } catch {
      setError("Changes were not saved. Please retry.");
    } finally {
      setBusy(false);
    }
  }

  function patch(partial: Record<string, string | boolean>) {
    if (!data) return;
    setSaved(false);
    setData({ ...data, ...partial });
  }

  return (
    <DetailScaffold
      width="narrow"
      title={privacy ? "Privacy" : "Profile"}
      subtitle={
        privacy
          ? "Control who can see your profile, activity, and how others can find you."
          : "Your name and about text on GlobalChat."
      }
    >
      {!privacy && <ProfilePhotoSettings token={token}/>}
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
      {!data ? (
        <p role="status" className="animate-pulse text-sm text-aurora-muted">Loading…</p>
      ) : privacy ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <Section title="Profile visibility">
            <SettingRow
              icon={Image}
              title="Profile photo"
              description="Who can see your profile picture."
              control={
                <VisibilitySelect
                  aria-label="Profile photo visibility"
                  value={String(data.profile_photo_visibility)}
                  onChange={(v) => patch({ profile_photo_visibility: v })}
                />
              }
            />
            <SettingRow
              icon={User}
              title="About"
              description="Who can read your about text."
              control={
                <VisibilitySelect
                  aria-label="About visibility"
                  value={String(data.about_visibility)}
                  onChange={(v) => patch({ about_visibility: v })}
                />
              }
            />
          </Section>
          <Section title="Activity privacy">
            <SettingRow
              icon={Radio}
              title="Online status"
              description="Whether others see when you are online."
              control={
                <VisibilitySelect
                  aria-label="Online status visibility"
                  value={String(data.online_status_visibility)}
                  onChange={(v) => patch({ online_status_visibility: v })}
                />
              }
            />
            <SettingRow
              icon={Eye}
              title="Last seen"
              description="Who can see when you were last active."
              control={
                <VisibilitySelect
                  aria-label="Last seen visibility"
                  value={String(data.last_seen_visibility)}
                  onChange={(v) => patch({ last_seen_visibility: v })}
                />
              }
            />
          </Section>
          <Section title="Messaging privacy">
            <SettingRow
              icon={MessageSquare}
              title="Read receipts"
              description="Let others know when you have read their messages."
              control={
                <Switch
                  label="Read receipts"
                  checked={Boolean(data.read_receipts_enabled)}
                  onChange={(v) => patch({ read_receipts_enabled: v })}
                />
              }
            />
          </Section>
          <Section title="Contact discovery">
            <SettingRow
              icon={Phone}
              title="Find me by phone"
              description="Allow contacts who know your number to discover your account."
              control={
                <Switch
                  label="Allow exact phone contact discovery"
                  checked={data.discoverable !== false}
                  onChange={(v) => patch({ discoverable: v })}
                />
              }
            />
          </Section>
          {(dirty || saved) && (
            <ActionBar>
              <Button type="submit" variant="primary" disabled={busy || !dirty}>
                {busy ? "Saving…" : "Save changes"}
              </Button>
              {saved && !dirty && (
                <p role="status" className="text-sm text-aurora-muted">Changes saved.</p>
              )}
            </ActionBar>
          )}
        </form>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <Field label="Display name">
            <Input
              required
              maxLength={200}
              value={String(data.display_name || "")}
              onChange={(e) => patch({ display_name: e.target.value })}
            />
          </Field>
          <Field label="About">
            <TextArea
              maxLength={2000}
              value={String(data.about || "")}
              onChange={(e) => patch({ about: e.target.value })}
              rows={4}
              placeholder="A short line about you"
            />
          </Field>
          {(dirty || saved) && (
            <ActionBar>
              <Button type="submit" variant="primary" disabled={busy || !dirty}>
                {busy ? "Saving…" : "Save changes"}
              </Button>
              {saved && !dirty && (
                <p role="status" className="text-sm text-aurora-muted">Changes saved.</p>
              )}
            </ActionBar>
          )}
        </form>
      )}
    </DetailScaffold>
  );
}
