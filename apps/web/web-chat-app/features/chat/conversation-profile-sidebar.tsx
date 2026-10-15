"use client";

import { Search, X } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import type { Contact } from "@/features/contacts/api";
import { contactSubtitle, contactTitle } from "@/features/contacts/use-contacts";
import type { Conversation } from "./api";

export function ConversationProfileSidebar({
  conversation,
  contact,
  onClose,
}: {
  conversation: Conversation;
  contact: Contact | null;
  onClose: () => void;
}) {
  const title = contact ? contactTitle(contact) : conversation.title || "Direct chat";
  const avatarId = contact?.matched_user?.avatar_media_id ?? conversation.avatar_media_id;

  return (
    <aside
      className="flex w-full shrink-0 flex-col border-l border-aurora-border bg-aurora-surface max-md:absolute max-md:inset-0 max-md:z-40 md:w-[min(100%,360px)]"
      aria-label="Contact info"
    >
      <header className="flex items-center gap-2 border-b border-aurora-border px-3 py-3">
        <IconButton label="Close contact info" onClick={onClose}>
          <X className={iconSize} />
        </IconButton>
        <h2 className="text-base font-semibold">Contact info</h2>
      </header>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="flex flex-col items-center text-center">
          <Avatar name={title} mediaId={avatarId} size="lg" className="!size-28 !text-2xl" />
          <p className="mt-4 text-xl font-semibold">{title}</p>
          <div className="mt-5 flex gap-6 text-xs text-aurora-muted">
            <span className="flex flex-col items-center gap-1">
              <span className="grid size-11 place-items-center rounded-full bg-aurora-surface-alt text-aurora-text">
                <Search className={iconSize} aria-hidden />
              </span>
              Search
            </span>
          </div>
          {contact?.phone_display && (
            <p className="mt-1 text-sm text-aurora-muted">{contact.phone_display}</p>
          )}
          {contact && !contact.phone_display && (
            <p className="mt-1 text-sm text-aurora-muted">{contactSubtitle(contact)}</p>
          )}
        </div>

        <dl className="mt-8 space-y-4 border-t border-aurora-border pt-6 text-sm">
          <div>
            <dt className="text-aurora-muted">Chat type</dt>
            <dd className="mt-0.5 font-medium">{conversation.type}</dd>
          </div>
          <div>
            <dt className="text-aurora-muted">Members</dt>
            <dd className="mt-0.5 font-medium">{conversation.member_count}</dd>
          </div>
          {contact?.matched_user && (
            <div>
              <dt className="text-aurora-muted">GlobalChat profile</dt>
              <dd className="mt-0.5 font-medium">
                {contact.matched_user.display_name}
                {contact.matched_user.phone_verified ? " · Verified" : ""}
              </dd>
            </div>
          )}
          {conversation.description && (
            <div>
              <dt className="text-aurora-muted">About</dt>
              <dd className="mt-0.5">{conversation.description}</dd>
            </div>
          )}
        </dl>
      </div>
    </aside>
  );
}
