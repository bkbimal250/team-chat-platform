"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Contact } from "./api";
import { contactsApi } from "./api";
import { contactMessageError } from "./contact-message-error";
import { ContactsDetailPanel, ContactsListPanel, useContactsSelection } from "./contacts-panels";

/** Standalone layout for tests and /contacts deep links */
export function Contacts() {
  const router = useRouter();
  const ctx = useContactsSelection();
  const [openingId, setOpeningId] = useState<string | null>(null);

  async function openChat(contact: Contact) {
    ctx.setSelectedId(contact.id);
    if (!contact.matched_user) return;
    setOpeningId(contact.id);
    ctx.store.setError("");
    try {
      const conversation = await contactsApi.message(contact.id);
      router.push("/?conversation=" + encodeURIComponent(conversation.id));
    } catch (issue) {
      ctx.store.setError(contactMessageError(issue));
    } finally {
      setOpeningId(null);
    }
  }

  return (
    <div className="flex h-full min-h-[32rem] overflow-hidden">
      <ContactsListPanel
        ctx={ctx}
        openingId={openingId}
        onOpenChat={(contact) => void openChat(contact)}
        onAdd={ctx.beginAdd}
      />
      <div className="min-w-0 flex-1">
        <ContactsDetailPanel ctx={ctx} />
      </div>
    </div>
  );
}
