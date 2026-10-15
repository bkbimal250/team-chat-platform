"use client";

import { Avatar } from "@/components/ui/avatar";
import { ListRow } from "@/components/ui/list-row";
import type { Contact } from "@/features/contacts/api";
import { contactSubtitle, contactTitle } from "@/features/contacts/use-contacts";

export function ContactPickerRow({
  contact,
  onPick,
}: {
  contact: Contact;
  onPick: () => void;
}) {
  const title = contactTitle(contact);
  return (
    <ListRow
      onClick={onPick}
      leading={
        <Avatar
          name={title}
          mediaId={contact.matched_user?.avatar_media_id}
        />
      }
      title={title}
      subtitle={contactSubtitle(contact)}
    />
  );
}
