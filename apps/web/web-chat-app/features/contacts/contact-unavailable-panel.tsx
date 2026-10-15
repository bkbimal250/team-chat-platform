"use client";

import { UserRound } from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { Pencil, Trash2 } from "lucide-react";
import type { Contact } from "./api";
import { contactSubtitle, contactTitle } from "./use-contacts";

export function ContactUnavailablePanel({
  contact,
  busy,
  onEdit,
  onRemove,
}: {
  contact: Contact;
  busy: boolean;
  onEdit: () => void;
  onRemove: () => void;
}) {
  const title = contactTitle(contact);
  return (
    <div className="flex flex-1 flex-col bg-[linear-gradient(180deg,var(--aurora-surface-alt)_0%,var(--background)_38%)]">
      <header className="flex items-center gap-3 border-b border-aurora-border bg-aurora-surface px-4 py-4">
        <Avatar name={title} mediaId={contact.matched_user?.avatar_media_id} />
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-lg font-semibold">{title}</h1>
          <p className="truncate text-sm text-aurora-muted">{contactSubtitle(contact)}</p>
        </div>
        <IconButton label={`Edit ${title}`} onClick={onEdit}>
          <Pencil className={iconSize} />
        </IconButton>
        <IconButton label={`Remove ${title}`} onClick={onRemove} className="text-rose-600">
          <Trash2 className={iconSize} />
        </IconButton>
      </header>
      <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
        <UserRound className="mb-4 size-12 text-aurora-muted" aria-hidden />
        <p className="text-lg font-medium">Can&apos;t chat yet</p>
        <p className="mt-2 max-w-sm text-sm text-aurora-muted">
          This number isn&apos;t on GlobalChat or the person has discoverability turned off.
          When they join, tap them again to start a conversation.
        </p>
        <Button className="mt-6" variant="outline" disabled={busy} onClick={onEdit}>
          Edit contact
        </Button>
      </div>
    </div>
  );
}
