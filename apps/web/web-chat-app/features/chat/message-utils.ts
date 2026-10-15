import { ChatMessage, RealtimeFrame } from "./api";

export const messageKey = (message: ChatMessage) =>
  message.id ||
  message.client_message_id ||
  `${message.conversation_id}:${message.sequence}`;

export const realtimeMessage = (
  payload: NonNullable<RealtimeFrame["payload"]>,
): ChatMessage => ({ ...payload, id: payload.message_id ?? payload.id });

export const formatMessageTime = (value?: string) =>
  value
    ? new Intl.DateTimeFormat(undefined, {
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(value))
    : "";
