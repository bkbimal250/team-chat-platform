"use client";

import { ReactNode } from "react";

export function NewChatActionRow({
  icon,
  title,
  onClick,
}: {
  icon: ReactNode;
  title: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-full items-center gap-4 px-4 py-3 text-left transition-colors hover:bg-aurora-surface-alt"
    >
      <span className="grid size-11 shrink-0 place-items-center rounded-full bg-aurora-primary/15 text-aurora-primary">
        {icon}
      </span>
      <span className="text-sm font-medium text-aurora-text">{title}</span>
    </button>
  );
}
