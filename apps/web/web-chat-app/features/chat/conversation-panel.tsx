"use client";

import {
  KeyboardEvent,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ArrowDown,
  ChevronLeft,
  Copy,
  Forward,
  Search,
  Send,
  Share2,
} from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { SearchField } from "@/components/ui/search-field";
import { AlertBanner } from "@/components/ui/alert-banner";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { OverflowMenu } from "@/components/ui/overflow-menu";
import { Button } from "@/components/ui/button";
import { AttachmentComposer } from "@/features/media/attachment-composer";
import { MediaContent } from "@/features/media/media-content";
import { downloadMedia } from "@/features/media/api";
import {
  chatApi,
  ChatMessage,
  Conversation,
  RealtimeFrame,
} from "./api";
import {
  formatMessageTime,
  messageKey,
  realtimeMessage,
} from "./message-utils";

export function ConversationPanel({
  conversation,
  conversations,
  token,
  memberId,
  socket,
  socketGeneration,
  onBack,
  onOpenProfile,
  profileAside,
}: {
  conversation: Conversation;
  conversations: Conversation[];
  token: string | null;
  memberId: string | null;
  socket: React.MutableRefObject<WebSocket | null>;
  socketGeneration: number;
  onBack: () => void;
  onOpenProfile?: () => void;
  profileAside?: ReactNode;
}) {
  const scroller = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const [newMessages, setNewMessages] = useState(false);
  const previousLatest = useRef(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionStatus, setActionStatus] = useState("");
  const [receiptError, setReceiptError] = useState("");
  const [forwardingMessage, setForwardingMessage] = useState<ChatMessage | null>(
    null,
  );
  const [forwarding, setForwarding] = useState(false);
  const [typers, setTypers] = useState<Record<string, number>>({});
  const typingLastSent = useRef(0);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const readSequence = useRef(0);
  const readInFlight = useRef(new Set<number>());
  const merge = useCallback(
    (rows: ChatMessage[]) =>
      setMessages((current) =>
        [...current, ...rows]
          .filter(
            (row, index, all) =>
              all.findIndex(
                (candidate) => messageKey(candidate) === messageKey(row),
              ) === index,
          )
          .sort((a, b) => a.sequence - b.sequence),
      ),
    [],
  );
  const load = useCallback(
    async (before?: number) => {
      if (!token) return;
      setLoading(!before);
      try {
        merge(await chatApi.listMessages(conversation.id, token, before));
      } catch (issue) {
        setError(
          issue instanceof Error ? issue.message : "Unable to load messages.",
        );
      } finally {
        setLoading(false);
      }
    },
    [conversation.id, merge, token],
  );

  const markReadThrough = useCallback(
    async (sequence: number) => {
      if (
        !token ||
        sequence <= readSequence.current ||
        readInFlight.current.has(sequence)
      )
        return;
      readInFlight.current.add(sequence);
      try {
        await chatApi.markDelivered(conversation.id, sequence, token);
        await chatApi.markRead(conversation.id, sequence, token);
        readSequence.current = Math.max(readSequence.current, sequence);
        setReceiptError("");
      } catch {
        setReceiptError("Unread messages could not be marked as read. Please retry.");
      } finally {
        readInFlight.current.delete(sequence);
      }
    },
    [conversation.id, token],
  );

  useEffect(() => {
    const sequence = conversation.last_message_sequence;
    if ((conversation.unread_count ?? 0) > 0 && sequence)
      void markReadThrough(sequence);
  }, [
    conversation.last_message_sequence,
    conversation.unread_count,
    markReadThrough,
  ]);
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setMessages([]);
      setError("");
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  useEffect(() => {
    const current = socket.current;
    if (!current) return;
    const handler = (event: MessageEvent) => {
      try {
        const frame = JSON.parse(event.data) as RealtimeFrame;
        const payload = frame.payload;
        if (!payload || payload.conversation_id !== conversation.id) return;
        if (frame.type === "typing.updated.v1" && payload.member_id) {
          const member = payload.member_id;
          const expiry = Date.parse(payload.expires_at || "");
          setTypers((current) => {
            const next = { ...current };
            if (payload.active && expiry > Date.now()) next[member] = expiry;
            else delete next[member];
            return next;
          });
          return;
        }
        if (
          frame.type === "message.created.v1" ||
          frame.type === "message.edited.v1"
        )
          merge([realtimeMessage(payload)]);
        if (frame.type === "message.deleted.v1")
          setMessages((rows) =>
            rows.map((row) =>
              row.id === (payload.message_id ?? payload.id)
                ? realtimeMessage(payload)
                : row,
            ),
          );
        if (
          (frame.type === "message.delivered.v1" ||
            frame.type === "message.read.v1") &&
          payload.sequence &&
          payload.member_id !== memberId
        )
          setMessages((rows) =>
            rows.map((row) =>
              row.sender_member_id === memberId &&
              row.sequence <= payload.sequence
                ? {
                    ...row,
                    status:
                      frame.type === "message.read.v1" ? "READ" : "DELIVERED",
                  }
                : row,
            ),
          );
      } catch {}
    };
    current.addEventListener("message", handler);
    return () => current.removeEventListener("message", handler);
  }, [conversation.id, memberId, merge, socket, socketGeneration]);
  useEffect(() => {
    const expiries = Object.values(typers);
    if (!expiries.length) return;
    const timer = setTimeout(
      () =>
        setTypers((current) =>
          Object.fromEntries(
            Object.entries(current).filter(([, expiry]) => expiry > Date.now()),
          ),
        ),
      Math.max(0, Math.min(...expiries) - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [typers]);
  useEffect(() => {
    const sequence = messages[messages.length - 1]?.sequence;
    if (sequence) void markReadThrough(sequence);
  }, [messages, markReadThrough]);
  useEffect(
    () => () => {
      if (typingTimer.current) clearTimeout(typingTimer.current);
      if (socket.current?.readyState === WebSocket.OPEN)
        socket.current.send(
          JSON.stringify({
            version: 1,
            type: "typing.stop",
            conversation_id: conversation.id,
          }),
        );
    },
    [conversation.id, socket],
  );
  function notifyTyping(value: string) {
    const ws = socket.current;
    if (ws?.readyState !== WebSocket.OPEN) return;
    if (value.trim() && Date.now() - typingLastSent.current > 2000) {
      ws.send(
        JSON.stringify({
          version: 1,
          type: "typing.start",
          conversation_id: conversation.id,
        }),
      );
      typingLastSent.current = Date.now();
    }
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => {
      if (ws.readyState === WebSocket.OPEN)
        ws.send(
          JSON.stringify({
            version: 1,
            type: "typing.stop",
            conversation_id: conversation.id,
          }),
        );
    }, 1500);
  }
  async function send() {
    const text = draft.trim();
    if (!token || !text || sending) return;
    setSending(true);
    setSendError("");
    const clientMessageId = crypto.randomUUID();
    try {
      const created = await chatApi.sendMessage(
        conversation.id,
        text,
        clientMessageId,
        token,
      );
      merge([created]);
      setDraft("");
    } catch (issue) {
      setSendError(
        issue instanceof Error
          ? issue.message
          : "Message was not sent. Try again.",
      );
    } finally {
      setSending(false);
    }
  }

  async function copyMessage(message: ChatMessage) {
    const text = message.text || message.attachment?.filename;
    setActionError("");
    setActionStatus("");
    if (!text) {
      setActionError("This message has no text to copy.");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setActionStatus("Copied to clipboard.");
    } catch {
      setActionError("Could not copy this message. Check clipboard permissions.");
    }
  }

  async function shareMessage(message: ChatMessage) {
    setActionError("");
    setActionStatus("");
    const text = message.text || message.attachment?.filename || "";
    try {
      if (message.attachment) {
        if (!token) throw new Error("Sign in again before sharing attachments.");
        if (!navigator.share || !navigator.canShare)
          throw new Error("This browser cannot share files. Download the attachment to share it.");
        if (message.attachment.size_bytes > 100 * 1024 * 1024)
          throw new Error("This attachment is too large to share here. Download it first.");
        const url = await downloadMedia(message.attachment.media_id, token);
        const response = await fetch(url);
        if (!response.ok) throw new Error("The attachment could not be downloaded for sharing.");
        const file = new File([await response.blob()], message.attachment.filename, {
          type: message.attachment.mime_type,
        });
        if (!navigator.canShare({ files: [file] }))
          throw new Error("This browser cannot share this file type. Download it to share it.");
        await navigator.share({
          title: conversation.title || "GlobalChat message",
          text: message.text || undefined,
          files: [file],
        });
      } else if (navigator.share) {
        await navigator.share({
          title: conversation.title || "GlobalChat message",
          text,
        });
      } else {
        await navigator.clipboard.writeText(text);
        setActionStatus("Sharing is not supported here. Message text copied instead.");
      }
    } catch (issue) {
      if (issue instanceof DOMException && issue.name === "AbortError") return;
      setActionError(
        issue instanceof Error ? issue.message : "Could not share this message.",
      );
    }
  }

  async function forwardMessage(message: ChatMessage, target: Conversation) {
    if (!token || forwarding) return;
    setForwarding(true);
    setActionError("");
    setActionStatus("");
    try {
      await chatApi.forwardMessage(target.id, message.id, token);
      setForwardingMessage(null);
      setActionStatus(`Forwarded to ${target.title || "conversation"}.`);
    } catch (issue) {
      setActionError(
        issue instanceof Error ? issue.message : "Could not forward this message.",
      );
    } finally {
      setForwarding(false);
    }
  }

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }
  useEffect(() => {
    const latest = messages[messages.length - 1]?.sequence || 0;
    if (latest <= previousLatest.current) return;
    previousLatest.current = latest;
    const timer = setTimeout(() => {
      if (nearBottom.current) {
        scroller.current?.scrollTo?.({
          top: scroller.current.scrollHeight,
          behavior: "smooth",
        });
      } else setNewMessages(true);
    }, 0);
    return () => clearTimeout(timer);
  }, [messages]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [messageSearch, setMessageSearch] = useState("");
  const visibleMessages = messages.filter(row => !messageSearch.trim() || (!row.deleted_at && (row.text ?? "").toLowerCase().includes(messageSearch.trim().toLowerCase())));
  const oldest = messages[0]?.sequence;
  const title = conversation.title || "Direct conversation";
  return (
    <div className="flex min-h-0 flex-1 flex-col md:flex-row">
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-aurora-border bg-aurora-surface px-3 py-3 sm:px-4">
        <IconButton
          label="Back to conversations"
          onClick={onBack}
          className="text-aurora-text md:hidden"
        >
          <ChevronLeft className={iconSize} />
        </IconButton>
        <button
          type="button"
          onClick={onOpenProfile}
          disabled={!onOpenProfile}
          className="flex min-w-0 flex-1 items-center gap-3 rounded-lg text-left transition-colors hover:bg-aurora-surface-alt/80 focus-visible:outline-2 focus-visible:outline-aurora-primary disabled:hover:bg-transparent"
        >
          <Avatar name={title} mediaId={conversation.avatar_media_id} size="sm" />
          <span className="min-w-0 flex-1">
            <span className="block truncate font-semibold">{title}</span>
            <span className="block text-xs text-aurora-muted">
              {conversation.type === "DIRECT"
                ? "Tap for contact info"
                : `${conversation.member_count} members`}
            </span>
          </span>
        </button>
        <div className="ml-auto flex shrink-0 items-center gap-0.5">
          <IconButton label="Search messages" onClick={() => { setSearchOpen(!searchOpen); setMessageSearch(""); }} className="text-aurora-muted">
            <Search className={iconSize} />
          </IconButton>
        </div>
        </header>
        {searchOpen && (
          <div className="border-b border-aurora-border bg-aurora-surface p-3">
            <SearchField
              label="Search loaded messages"
              value={messageSearch}
              onChange={setMessageSearch}
            />
            <p role="status" className="mt-1 text-xs text-aurora-muted">
              {visibleMessages.length} matches in loaded messages. Load older messages to
              search more history.
            </p>
          </div>
        )}
        <div
        ref={scroller}
        onScroll={() => {
          const element = scroller.current;
          if (element) {
            nearBottom.current =
              element.scrollHeight - element.scrollTop - element.clientHeight <
              100;
            if (nearBottom.current) setNewMessages(false);
          }
        }}
        className="flex-1 overflow-y-auto p-3 sm:p-4"
      >
        <button
          disabled={!oldest}
          onClick={() => void load(oldest)}
          className="mx-auto mb-4 block text-xs font-semibold text-cyan-700 disabled:hidden dark:text-cyan-300"
        >
          Load older messages
        </button>
        {loading && (
          <p className="text-center text-sm text-aurora-muted">
            Loading messages…
          </p>
        )}
        <AlertBanner message={error} />
        {visibleMessages.map((row, index) => (
          <div key={messageKey(row)}>
            {index === 0 ||
            new Date(row.created_at).toDateString() !==
              new Date(visibleMessages[index - 1].created_at).toDateString() ? (
              <p className="my-4 text-center text-xs text-aurora-muted">
                {new Intl.DateTimeFormat(undefined, {
                  dateStyle: "medium",
                }).format(new Date(row.created_at))}
              </p>
            ) : null}
            <div
              className={`mb-2 flex ${row.sender_member_id === memberId ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm sm:max-w-[80%] ${row.sender_member_id === memberId ? "bg-cyan-700 text-white dark:bg-cyan-800" : "bg-aurora-surface shadow-sm"}`}
              >
                {!row.deleted_at && row.attachment && token && (
                  <MediaContent
                    attachment={row.attachment}
                    token={token}
                    images={messages.flatMap((message) =>
                      message.attachment?.media_type === "image" &&
                      !message.deleted_at
                        ? [message.attachment]
                        : [],
                    )}
                  />
                )}
                <p>{row.deleted_at ? "Message deleted" : row.text}</p>
                <p
                  className={`mt-1 text-right text-[10px] ${row.sender_member_id === memberId ? "text-cyan-100" : "text-aurora-muted"}`}
                >
                  {formatMessageTime(row.created_at)}{" "}
                  {row.status === "READ"
                    ? "· Read"
                    : row.status === "DELIVERED"
                      ? "· Delivered"
                      : ""}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
      {newMessages && (
        <button
          type="button"
          className="mx-auto inline-flex items-center gap-1.5 rounded-full bg-cyan-700 px-4 py-2 text-white dark:bg-cyan-800"
          onClick={() => {
            nearBottom.current = true;
            scroller.current?.scrollTo?.({
              top: scroller.current.scrollHeight,
              behavior: "smooth",
            });
            setNewMessages(false);
          }}
        >
          New messages
          <ArrowDown className="size-4 shrink-0" aria-hidden />
        </button>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void send();
        }}
        className="border-t border-aurora-border bg-aurora-surface p-3"
      >
        {Object.keys(typers).length > 0 && (
          <p role="status" className="text-xs text-aurora-muted">
            Someone is typing…
          </p>
        )}
        <AlertBanner message={sendError} />
        {token && (
          <AttachmentComposer
            conversationId={conversation.id}
            token={token}
            onSent={(message) => merge([message])}
          />
        )}
        <div className="mt-2 flex gap-2">
          <textarea
            value={draft}
            onChange={(event) => {
              setDraft(event.target.value);
              notifyTyping(event.target.value);
            }}
            onKeyDown={keyDown}
            maxLength={10000}
            aria-label="Write a message"
            placeholder="Write a message"
            className="min-h-11 min-w-0 flex-1 resize-none rounded-xl border border-aurora-border bg-aurora-background px-3 py-2 text-sm"
          />
          {sending ? (
            <span
              role="status"
              className="grid min-w-11 place-items-center rounded-xl bg-cyan-700 px-3 py-2 text-xs font-semibold text-white"
            >
              Sending
            </span>
          ) : (
            <IconButton
              label="Send"
              type="submit"
              disabled={!draft.trim()}
              className="min-w-11 bg-cyan-700 text-white hover:bg-cyan-800 disabled:bg-cyan-700/50"
            >
              <Send className={iconSize} />
            </IconButton>
          )}
        </div>
      </form>
      </div>
      {profileAside}
    </div>
  );
}
