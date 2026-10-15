"use client";

import { ChevronRight } from "lucide-react";
import { settingsMenuItems } from "@/components/navigation/app-nav-config";
import { iconSize } from "@/components/ui/icon-button";
import { Section } from "@/components/content/section";

export function SettingsHub({ onSelect }: { onSelect: (page: string) => void }) {
  return (
    <Section title="Menu">
      <ul>
        {settingsMenuItems.map(({ label, page, icon: ItemIcon }) => (
          <li key={page}>
            <button
              type="button"
              onClick={() => onSelect(page)}
              className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-aurora-surface-alt focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-aurora-primary"
            >
              <ItemIcon className={`${iconSize} text-aurora-muted`} aria-hidden />
              <span className="flex-1 text-sm font-medium">{label}</span>
              <ChevronRight className={`${iconSize} text-aurora-muted`} aria-hidden />
            </button>
          </li>
        ))}
      </ul>
    </Section>
  );
}
