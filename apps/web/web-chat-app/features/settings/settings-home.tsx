"use client";

import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { SettingsHub } from "./settings-hub";

export function SettingsHome({ onSelect }: { onSelect: (page: string) => void }) {
  return (
    <DetailScaffold width="narrow" title="Settings" subtitle="Profile, privacy, devices, and preferences.">
      <SettingsHub onSelect={onSelect} />
    </DetailScaffold>
  );
}
