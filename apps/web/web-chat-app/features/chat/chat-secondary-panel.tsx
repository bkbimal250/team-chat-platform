"use client";

import { MessageSquarePlus, Users } from "lucide-react";
import { OverflowMenu } from "@/components/ui/overflow-menu";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { AlertBanner } from "@/components/ui/alert-banner";
import { EmptyState } from "@/components/ui/empty-state";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { SearchField } from "@/components/ui/search-field";
import { SecondaryPanel } from "@/components/layout/secondary-panel";
import { MessageCircle } from "lucide-react";
import { formatMessageTime } from "./message-utils";
import { Conversation } from "./api";
import type { useChatController } from "./use-chat-controller";

type ChatState = ReturnType<typeof useChatController>;

export function ChatSecondaryPanel({
  chat,
  onNewChat,
  onNewGroup,
}: {
  chat: ChatState;
  onNewChat: () => void;
  onNewGroup?: () => void;
}) {
  return (
    <SecondaryPanel
      title="Chats"
      actions={
        <>
          <OverflowMenu
            label="Chat options"
            items={[
              {
                id: "new-group",
                label: "New group",
                icon: <Users className={iconSize} aria-hidden />,
                onSelect: () => onNewGroup?.(),
              },
            ]}
          />
          <IconButton label="New chat" onClick={onNewChat} className="text-aurora-primary">
            <MessageSquarePlus className={iconSize} />
          </IconButton>
        </>
      }
    >
      <div className="space-y-2 border-b border-aurora-border p-3">
        <SearchField
          label="Search conversations"
          placeholder="Search chats or recent messages"
          value={chat.search}
          onChange={chat.setSearch}
        />
        <div className="flex gap-2" role="group" aria-label="Filter chats">
          {(["all", "unread", "groups"] as const).map(filter => (
            <button key={filter} type="button" aria-pressed={chat.filter === filter} onClick={() => chat.setFilter(filter)} className={`rounded-full px-3 py-1.5 text-xs font-medium capitalize transition-colors focus-visible:outline-2 focus-visible:outline-aurora-primary ${chat.filter === filter ? "bg-aurora-primary text-white" : "bg-aurora-surface-alt text-aurora-muted hover:text-aurora-text"}`}>{filter}</button>
          ))}
        </div>
        <p role="status" className="text-[11px] text-aurora-muted">
          {chat.connection === "Connected"
            ? "Live"
            : chat.connection}
        </p>
      </div>
      {chat.loading && (
        <div className="space-y-2 p-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-14 animate-pulse rounded-xl bg-aurora-surface-alt"
            />
          ))}
        </div>
      )}
      {chat.error && (
        <div className="p-3">
          <AlertBanner message={chat.error} />
          <button
            type="button"
            onClick={() => void chat.load()}
            className="mt-2 text-xs font-semibold text-aurora-primary"
          >
            Retry
          </button>
        </div>
      )}
      {!chat.loading && !chat.error && chat.conversations.length === 0 && (
        <EmptyState
          icon={MessageCircle}
          title={chat.search.trim() || chat.filter !== "all" ? "No matching chats" : "No conversations"}
          detail={
            chat.search.trim() || chat.filter !== "all" ? "Try another search or chat filter." : chat.personal
              ? "Message a saved contact to start chatting."
              : "Workspace conversations appear here."
          }
        />
      )}
      <ul className="divide-y divide-aurora-border">
        {chat.conversations.map((conversation) => (
          <ConversationRow
            key={conversation.id}
            conversation={conversation}
            active={chat.selected?.id === conversation.id}
            onSelect={() => chat.choose(conversation)}
          />
        ))}
      </ul>
    </SecondaryPanel>
  );
}

function ConversationRow({
  conversation,
  active,
  onSelect,
}: {
  conversation: Conversation;
  active: boolean;
  onSelect: () => void;
}) {
  const title = conversation.title || "Direct conversation";
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        aria-current={active ? "true" : undefined}
        className={`flex w-full gap-3 px-3 py-3 text-left transition-colors hover:bg-aurora-surface-alt ${active ? "bg-aurora-surface-alt" : ""}`}
      >
        <Avatar name={title} mediaId={conversation.avatar_media_id} />
        <span className="min-w-0 flex-1">
          <span className="flex items-center justify-between gap-2">
            <span className="truncate font-medium text-sm">{title}</span>
            {conversation.last_message_at && (
              <time className="shrink-0 text-[10px] text-aurora-muted">
                {formatMessageTime(conversation.last_message_at)}
              </time>
            )}
          </span>
          <span className="mt-0.5 flex items-center justify-between gap-2">
            <span className="truncate text-xs text-aurora-muted">
              {conversation.last_message_preview || "No messages yet"}
            </span>
            {!!conversation.unread_count && (
              <span aria-label={`${conversation.unread_count} unread messages`}><Badge>{conversation.unread_count}</Badge></span>
            )}
          </span>
        </span>
      </button>
    </li>
  );
}
