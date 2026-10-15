"use client";

import { MessageCircle, UserRound } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

export function ContactsWelcome() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-[linear-gradient(180deg,var(--aurora-surface-alt)_0%,var(--background)_42%)] p-8">
      <div className="max-w-md text-center">
        <EmptyState
          icon={UserRound}
          title="Your contacts"
          detail="Select someone from the list to open a chat. People on GlobalChat open in Chats, just like WhatsApp."
        />
        <p className="mt-6 flex items-center justify-center gap-2 text-xs text-aurora-muted">
          <MessageCircle className="size-4" aria-hidden />
          Tap a contact to message
        </p>
      </div>
    </div>
  );
}
