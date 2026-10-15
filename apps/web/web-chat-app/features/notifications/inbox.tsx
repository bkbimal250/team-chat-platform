"use client";

import { useState } from "react";
import { Conversation } from "@/features/chat/api";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { NotificationsListPanel } from "./notifications-list-panel";
import { NotificationsDetailPanel } from "./notifications-detail-panel";
import { useNotifications } from "./use-notifications";
import type { Notice } from "./types";

export function NotificationInbox({
  token,
  onConversation,
}: {
  token: string;
  onConversation: (row: Conversation) => void;
}) {
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Notice | null>(null);
  const feed = useNotifications(page, Boolean(token));

  return (
    <DetailScaffold title="Notifications" subtitle="Workspace alerts and chat updates">
      <div className="flex min-h-[420px] flex-col overflow-hidden rounded-xl border border-aurora-border md:flex-row">
        <div className="min-h-0 flex-1 border-b border-aurora-border md:max-w-sm md:border-b-0 md:border-r">
          <NotificationsListPanel
            embedded
            rows={feed.rows}
            loading={feed.loading}
            error={feed.error}
            page={page}
            hasPrev={feed.hasPrev}
            hasNext={feed.hasNext}
            selectedId={selected?.id ?? null}
            onSelect={setSelected}
            onPageChange={setPage}
            onRetry={feed.reload}
          />
        </div>
        <div className="min-h-0 flex-1">
          <NotificationsDetailPanel
            token={token}
            selected={selected ?? feed.rows[0] ?? null}
            onConversation={onConversation}
          />
        </div>
      </div>
    </DetailScaffold>
  );
}
