"use client";
import { useEffect, useRef } from "react";
import { Conversation } from "./api";
import { WorkspacePeople } from "./workspace-people";
export function NewConversation({
  token,
  onCancel,
  onCreated,
}: {
  token: string;
  onCancel: () => void;
  onCreated: (row: Conversation) => void;
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
      onCancel={onCancel}
      className="m-auto w-[calc(100%-2rem)] max-w-lg rounded-3xl p-7 backdrop:bg-slate-950/50"
    >
      <h2 className="text-xl font-semibold">New direct conversation</h2>
      <WorkspacePeople token={token} onConversation={onCreated} />
      <button onClick={onCancel} className="mt-5 rounded-xl border px-4 py-2">
        Cancel
      </button>
    </dialog>
  );
}
