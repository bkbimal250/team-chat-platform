"use client";
import { ReactNode, useEffect, useRef } from "react";
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
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-3xl bg-white p-7 text-slate-900 shadow-2xl backdrop:bg-slate-950/50"
    >
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="my-5 text-sm leading-6 text-slate-600">{children}</div>
      <div className="flex justify-end gap-3">
        <button
          disabled={busy}
          onClick={onCancel}
          className="rounded-xl border px-4 py-2"
        >
          Cancel
        </button>
        <button
          disabled={busy}
          onClick={onConfirm}
          className="rounded-xl bg-cyan-800 px-4 py-2 text-white disabled:opacity-50"
        >
          {busy ? "Working…" : "Confirm"}
        </button>
      </div>
    </dialog>
  );
}
