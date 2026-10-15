"use client";

import { ReactNode, useEffect, useRef } from "react";
import { X } from "lucide-react";
import { IconButton, iconSize } from "./icon-button";

export function SheetDialog({
  title,
  open,
  onClose,
  children,
}: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open) dialog.showModal();
    else dialog.close();
  }, [open]);
  if (!open) return null;
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      className="m-auto w-[calc(100%-1.5rem)] max-w-md rounded-2xl border border-aurora-border bg-aurora-surface p-0 text-aurora-text shadow-xl backdrop:bg-slate-950/40"
    >
      <header className="flex items-center justify-between border-b border-aurora-border px-4 py-3">
        <h2 className="text-base font-semibold">{title}</h2>
        <IconButton label="Close" onClick={onClose}>
          <X className={iconSize} />
        </IconButton>
      </header>
      <div className="max-h-[min(80vh,32rem)] overflow-y-auto p-4">{children}</div>
    </dialog>
  );
}
