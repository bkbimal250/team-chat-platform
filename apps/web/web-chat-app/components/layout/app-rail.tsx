"use client";

import { MessageCircle } from "lucide-react";
import { AppSection, RailItem } from "../navigation/app-nav-config";
import { Badge } from "../ui/badge";
import { IconButton, iconSize } from "../ui/icon-button";
import { Avatar } from "../ui/avatar";

export function AppRail({
  active,
  onSelect,
  visible,
  displayName,
  mediaId,
  hasOrg,
  notificationCount = 0,
}: {
  active: AppSection;
  onSelect: (id: AppSection) => void;
  visible: RailItem[];
  displayName: string;
  mediaId?: string | null;
  hasOrg: boolean;
  notificationCount?: number;
}) {
  const groups = {
    primary: visible.filter((i) => i.group === "primary"),
    workspace: visible.filter((i) => i.group === "workspace"),
    bottom: visible.filter((i) => i.group === "bottom"),
  };
  function item(item: RailItem) {
    const isActive =
      active === item.id ||
      (item.id === "profile" && active === "settings");
    return (
      <IconButton
        key={item.id}
        label={item.label}
        onClick={() => onSelect(item.id)}
        className={`relative ${isActive ? "bg-aurora-primary/15 text-aurora-primary" : "text-aurora-muted hover:text-aurora-text"}`}
      >
        <item.icon className={iconSize} />
        {item.id === "notifications" && notificationCount > 0 && (
          <span className="absolute -right-0.5 -top-0.5">
            <Badge>{notificationCount > 9 ? "9+" : notificationCount}</Badge>
          </span>
        )}
      </IconButton>
    );
  }
  return (
    <nav
      aria-label="Application"
      className="flex w-16 shrink-0 flex-col items-center border-r border-aurora-border bg-aurora-surface py-3"
    >
      <div className="mb-4 grid size-10 place-items-center rounded-xl bg-aurora-primary text-white">
        <MessageCircle className="size-5" aria-hidden />
        <span className="sr-only">GlobalChat</span>
      </div>
      <div className="flex flex-col gap-1">{groups.primary.map(item)}</div>
      {hasOrg && groups.workspace.length > 0 && (
        <>
          <div className="my-3 h-px w-8 bg-aurora-border" />
          <div className="flex flex-col gap-1">{groups.workspace.map(item)}</div>
        </>
      )}
      <div className="mt-auto flex flex-col gap-1 pt-3">
        {groups.bottom.map((row) =>
          row.id === "profile" ? (
            <button
              key={row.id}
              type="button"
              title="Profile"
              aria-label="Profile"
              onClick={() => onSelect("profile")}
              className={`rounded-lg p-1.5 ${active === "profile" ? "ring-2 ring-aurora-primary/40" : ""}`}
            >
              <Avatar name={displayName} mediaId={mediaId} size="sm" />
            </button>
          ) : (
            item(row)
          ),
        )}
      </div>
    </nav>
  );
}
