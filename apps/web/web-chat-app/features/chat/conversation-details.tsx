"use client";
import { useEffect, useRef, useState } from "react";
import { Info } from "lucide-react";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { Conversation } from "./api";
export function ConversationDetails({
  conversation,
}: {
  conversation: Conversation;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <IconButton
        label="Details"
        onClick={() => setOpen(true)}
        className="border border-aurora-border text-xs"
      >
        <Info className={iconSize} />
      </IconButton>
      {open && (
        <Details conversation={conversation} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
function Details({
  conversation,
  onClose,
}: {
  conversation: Conversation;
  onClose: () => void;
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
      onCancel={onClose}
      aria-label="Conversation details"
      className="m-auto h-dvh max-h-dvh w-full max-w-sm rounded-2xl bg-aurora-surface p-7 text-aurora-text backdrop:bg-slate-950/40 md:mr-0"
    >
      <button
        autoFocus
        onClick={onClose}
        className="mb-8 rounded-xl border px-4 py-2"
      >
        Back to conversation
      </button>
      <h2 className="text-2xl font-semibold">
        {conversation.title || "Direct conversation"}
      </h2>
      <p className="mt-3 text-sm text-aurora-muted">
        {conversation.description || "No description provided."}
      </p>
      <dl className="mt-8 space-y-4 text-sm">
        <div>
          <dt className="text-aurora-muted">Type</dt>
          <dd>{conversation.type}</dd>
        </div>
        <div>
          <dt className="text-aurora-muted">Members</dt>
          <dd>{conversation.member_count}</dd>
        </div>
        <div>
          <dt className="text-aurora-muted">Status</dt>
          <dd>{conversation.status}</dd>
        </div>
      </dl>
    </dialog>
  );
}
