"use client";

import { ReactNode, useEffect, useRef, useState } from "react";
import { MoreVertical } from "lucide-react";
import { IconButton, iconSize } from "./icon-button";

export function OverflowMenu({
  label,
  items,
}: {
  label: string;
  items: { id: string; label: string; icon?: ReactNode; onSelect: () => void }[];
}) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", close);
    return () => window.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div ref={root} className="relative">
      <IconButton
        label={label}
        onClick={() => setOpen((v) => !v)}
        className="text-aurora-muted"
        aria-expanded={open}
      >
        <MoreVertical className={iconSize} />
      </IconButton>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-30 mt-1 min-w-[11rem] rounded-xl border border-aurora-border bg-aurora-surface py-1 shadow-lg"
        >
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              role="menuitem"
              className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm hover:bg-aurora-surface-alt"
              onClick={() => {
                setOpen(false);
                item.onSelect();
              }}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
