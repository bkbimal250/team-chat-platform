"use client";

import { useState } from "react";
import { Bell, MessageCircle } from "lucide-react";
import { apiRequest } from "@/lib/api/client";
import { Conversation } from "@/features/chat/api";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { EmptyState } from "@/components/ui/empty-state";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { Section } from "@/components/content/section";
import { DetailRow } from "@/components/content/detail-row";
import { previewModeLabel } from "@/components/content/labels";
import { noticeDescription, noticeTime, noticeTitle } from "./notification-present";
import type { Notice } from "./types";

export function NotificationsDetailPanel({
  token,
  selected,
  onConversation,
}: {
  token: string;
  selected: Notice | null;
  onConversation: (row: Conversation) => void;
}) {
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState("");

  if (!selected) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <EmptyState
          icon={Bell}
          title="Select a notification"
          detail="Choose an item from the list to preview and open its conversation."
        />
      </div>
    );
  }

  async function openChat() {
    if (!selected) return;
    setOpening(true);
    setError("");
    try {
      onConversation(
        await apiRequest<Conversation>(
          `/api/v1/conversations/${selected.conversation_id}`,
          {},
          token,
        ),
      );
    } catch {
      setError("This conversation is no longer available to you.");
    } finally {
      setOpening(false);
    }
  }

  const time = noticeTime(selected);

  return (
    <DetailScaffold
      width="medium"
      title={noticeTitle(selected)}
      subtitle={time ?? "Workspace alert"}
      avatarName={noticeTitle(selected)}
      actions={
        <IconButton label="Open conversation" disabled={opening} onClick={() => void openChat()}>
          <MessageCircle className={iconSize} />
        </IconButton>
      }
    >
      {error && (
        <div className="mb-4">
          <AlertBanner message={error} />
        </div>
      )}
      <Section title="Preview">
        <p className="px-4 py-3 text-sm leading-relaxed text-aurora-text">
          {noticeDescription(selected)}
        </p>
      </Section>
      {selected.preview_mode === "FULL" && selected.body && (
        <Section title="Message">
          <p className="whitespace-pre-wrap px-4 py-3 text-sm text-aurora-text">{selected.body}</p>
        </Section>
      )}
      <Section title="Details">
        <dl>
          <DetailRow label="Preview" value={previewModeLabel(selected.preview_mode)} />
          {time && <DetailRow label="Received" value={time} />}
        </dl>
      </Section>
      <Button className="mt-4" variant="primary" disabled={opening} onClick={() => void openChat()}>
        <MessageCircle className={iconSize} aria-hidden />
        Open conversation
      </Button>
      <p className="mt-6 text-xs text-aurora-muted">
        Unread badges are not available for workspace notifications on this client.
      </p>
    </DetailScaffold>
  );
}
