"use client";
import { useEffect, useRef, useState } from "react";
import { Conversation } from "./api";
export function ConversationDetails({
  conversation,
}: {
  conversation: Conversation;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Conversation details"
        className="ml-auto rounded-xl border px-3 py-2 text-xs"
      >
        Details
      </button>
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
      className="m-auto h-dvh max-h-dvh w-full max-w-sm rounded-2xl bg-white p-7 text-slate-900 backdrop:bg-slate-950/40 md:mr-0"
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
      <p className="mt-3 text-sm text-slate-500">
        {conversation.description || "No description provided."}
      </p>
      <dl className="mt-8 space-y-4 text-sm">
        <div>
          <dt className="text-slate-500">Type</dt>
          <dd>{conversation.type}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Members</dt>
          <dd>{conversation.member_count}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Status</dt>
          <dd>{conversation.status}</dd>
        </div>
      </dl>
    </dialog>
  );
}
