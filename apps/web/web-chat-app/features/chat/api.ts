import type { Attachment } from "@/features/media/api";
import { apiRequest } from "@/lib/api/client";

export type Conversation = {
  id: string;
  type: "DIRECT" | "GROUP" | string;
  title: string | null;
  description: string | null;
  avatar_media_id: string | null;
  status: string;
  member_count: number;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  last_message_sequence?: number | null;
  unread_count?: number;
};
export type ChatMessage = {
  attachment?: Attachment | null;
  id: string;
  conversation_id: string;
  sender_member_id: string;
  text: string | null;
  type: string;
  sequence: number;
  status: string;
  created_at: string;
  edited_at?: string | null;
  deleted_at?: string | null;
  forward_from_message_id?: string | null;
  forward_from_conversation_id?: string | null;
  client_message_id?: string;
  member_id?: string;
  active?: boolean;
  expires_at?: string;
};
export type RealtimeFrame = {
  version: 1;
  type: string;
  payload?: ChatMessage & {
    conversation_id: string;
    message_id?: string;
    member_id?: string;
    active?: boolean;
    expires_at?: string;
  };
};

export const chatApi = {
  listConversations: (token: string, signal?: AbortSignal) =>
    apiRequest<Conversation[]>("/api/v1/conversations", { signal }, token),
  listMessages: (
    conversationId: string,
    token: string,
    before?: number,
    after?: number,
  ) => {
    const query = new URLSearchParams({ limit: "50" });
    if (before) query.set("before_sequence", String(before));
    if (after) query.set("after_sequence", String(after));
    return apiRequest<ChatMessage[]>(
      `/api/v1/conversations/${conversationId}/messages?${query}`,
      {},
      token,
    );
  },
  sendMessage: (
    conversationId: string,
    text: string,
    clientMessageId: string,
    token: string,
  ) =>
    apiRequest<ChatMessage>(
      `/api/v1/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({
          client_message_id: clientMessageId,
          type: "TEXT",
          text,
        }),
      },
      token,
    ),
  forwardMessage: (
    conversationId: string,
    messageId: string,
    token: string,
  ) =>
    apiRequest<ChatMessage>(
      `/api/v1/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({
          client_message_id: crypto.randomUUID(),
          type: "TEXT",
          forward_from_message_id: messageId,
        }),
      },
      token,
    ),
  sendAttachment: (
    conversationId: string,
    type: string,
    media_id: string,
    client_message_id: string,
    token: string,
  ) =>
    apiRequest<ChatMessage>(
      `/api/v1/conversations/${conversationId}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ type, media_id, client_message_id }),
      },
      token,
    ),
  markDelivered: (conversationId: string, sequence: number, token: string) =>
    apiRequest<unknown>(
      `/api/v1/conversations/${conversationId}/delivered`,
      { method: "POST", body: JSON.stringify({ sequence }) },
      token,
    ),
  markRead: (conversationId: string, sequence: number, token: string) =>
    apiRequest<unknown>(
      `/api/v1/conversations/${conversationId}/read`,
      { method: "POST", body: JSON.stringify({ sequence }) },
      token,
    ),
};
