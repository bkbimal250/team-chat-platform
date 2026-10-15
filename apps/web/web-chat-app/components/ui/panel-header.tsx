"use client";

import { ChevronLeft } from "lucide-react";
import { ReactNode } from "react";
import { IconButton, iconSize } from "./icon-button";

export function PanelHeader({
  title,
  onBack,
  actions,
}: {
  title: string;
  onBack?: () => void;
  actions?: ReactNode;
}) {
  return (
    <header className="flex items-center gap-1 border-b border-aurora-border px-2 py-2.5 sm:px-3">
      {onBack ? (
        <IconButton label="Back" onClick={onBack} className="shrink-0 text-aurora-text">
          <ChevronLeft className={iconSize} />
        </IconButton>
      ) : (
        <span className="w-9 shrink-0" aria-hidden />
      )}
      <h2 className="min-w-0 flex-1 truncate text-base font-semibold text-aurora-text">
        {title}
      </h2>
      {actions ? (
        <div className="flex shrink-0 items-center gap-0.5">{actions}</div>
      ) : (
        <span className="w-9 shrink-0" aria-hidden />
      )}
    </header>
  );
}
