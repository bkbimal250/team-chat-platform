"use client";

import { HelpCircle, Mail } from "lucide-react";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { Section } from "@/components/content/section";
import { SettingRow } from "@/components/content/setting-row";

export function HelpContent() {
  return (
    <DetailScaffold
      width="narrow"
      title="Help"
      subtitle="Support for your GlobalChat account and workspace."
    >
      <Section title="Get support">
        <SettingRow
          icon={HelpCircle}
          title="Workspace access"
          description="Ask your company administrator to invite you or adjust your role."
          control={<span className="text-xs text-aurora-muted">Admin managed</span>}
        />
        <SettingRow
          icon={Mail}
          title="Account issues"
          description="For sign-in, devices, or privacy questions, contact your organization IT or admin."
          control={<span className="text-xs text-aurora-muted">—</span>}
        />
      </Section>
      <p className="text-sm leading-relaxed text-aurora-muted">
        GlobalChat keeps workspace data in your organization&apos;s tenant. Your admin can help with
        membership, branches, teams, and compliance requests.
      </p>
    </DetailScaffold>
  );
}
