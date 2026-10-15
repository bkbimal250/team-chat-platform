"use client";

import { LogOut, Smartphone } from "lucide-react";
import { EmailVerificationStatus } from "@/features/auth/email-verification";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { Button } from "@/components/ui/button";
import { Section } from "@/components/content/section";
import { SettingRow } from "@/components/content/setting-row";

export function AccountSettings({
  token,
  onDevices,
  onLogout,
}: {
  token: string;
  onDevices: () => void;
  onLogout: () => void;
}) {
  return (
    <DetailScaffold
      width="narrow"
      title="Account"
      subtitle="Security, verification, and signed-in devices."
    >
      <Section title="Verification">
        <div className="px-4 py-3">
          <EmailVerificationStatus token={token} />
        </div>
      </Section>
      <Section title="Devices & sessions">
        <SettingRow
          icon={Smartphone}
          title="Linked devices"
          description="See where you are signed in and sign out remotely."
          control={
            <Button type="button" variant="outline" onClick={onDevices}>
              Manage
            </Button>
          }
        />
      </Section>
      <Section title="Session">
        <SettingRow
          icon={LogOut}
          title="Log out"
          description="End your session on this device."
          control={
            <Button type="button" variant="danger" onClick={onLogout}>
              Log out
            </Button>
          }
        />
      </Section>
      <p className="mt-4 text-xs text-aurora-muted">
        Workspace membership and roles are managed by your organization administrator.
      </p>
    </DetailScaffold>
  );
}
