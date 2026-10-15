"use client";

import { ChevronRight, LogOut } from "lucide-react";
import { settingsMenuItems } from "@/components/navigation/app-nav-config";
import { Avatar } from "@/components/ui/avatar";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { SecondaryPanel } from "@/components/layout/secondary-panel";

export function SettingsSecondaryPanel({
  displayName,
  mediaId,
  email,
  activePage,
  onSelect,
  onLogout,
}: {
  displayName: string;
  mediaId?: string | null;
  email?: string;
  activePage: string;
  onSelect: (page: string) => void;
  onLogout: () => void;
}) {
  return (
    <SecondaryPanel
      title="Settings"
      actions={
        <IconButton label="Log out" onClick={onLogout} className="text-rose-600">
          <LogOut className={iconSize} />
        </IconButton>
      }
    >
      <div className="border-b border-aurora-border p-4">
        <div className="flex items-center gap-3 rounded-2xl border border-aurora-border bg-aurora-background p-3">
          <Avatar name={displayName} mediaId={mediaId} size="lg" />
          <div className="min-w-0">
            <p className="truncate font-semibold">{displayName || "Your account"}</p>
            {email && (
              <p className="truncate text-xs text-aurora-muted">{email}</p>
            )}
          </div>
        </div>
      </div>
      <ul className="p-2">
        {settingsMenuItems.map(({ label, page, icon: Icon }) => (
          <li key={page}>
            <button
              type="button"
              onClick={() => onSelect(page)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm ${activePage === page ? "bg-aurora-primary/10 text-aurora-primary" : "hover:bg-aurora-surface-alt"}`}
            >
              <Icon className={`${iconSize} text-aurora-muted`} aria-hidden />
              <span className="flex-1">{label}</span>
              <ChevronRight className={`${iconSize} text-aurora-muted`} aria-hidden />
            </button>
          </li>
        ))}
      </ul>
    </SecondaryPanel>
  );
}
