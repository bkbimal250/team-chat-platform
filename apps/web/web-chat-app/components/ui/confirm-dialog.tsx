"use client";
import { ReactNode, useEffect, useRef } from "react";
import { Button } from "./button";
export function ConfirmDialog({
  title,
  children,
  busy,
  onCancel,
  onConfirm,
}: {
  title: string;
  children: ReactNode;
  busy?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-3xl bg-aurora-surface p-7 text-aurora-text shadow-2xl backdrop:bg-slate-950/50"
    >
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="my-5 text-sm leading-6 text-aurora-muted">{children}</div>
      <div className="flex justify-end gap-3">
        <Button disabled={busy} onClick={onCancel}>Cancel</Button>
        <Button disabled={busy} variant="secondary" onClick={onConfirm}>
          {busy ? "Working…" : "Confirm"}
        </Button>
      </div>
    </dialog>
  );
}
