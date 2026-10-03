"use client";

import { KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";
import {
  clearSession,
  getAccessToken,
  getMemberId,
  hasSession,
} from "@/lib/auth/session";
import { connectRealtime } from "@/lib/websocket/connection";
import {
  chatApi,
  ChatMessage,
  Conversation,
  RealtimeFrame,
} from "@/features/chat/api";

import { AttachmentComposer } from "@/features/media/attachment-composer";
import { MediaContent } from "@/features/media/media-content";
import { Login } from "@/features/auth/login";
import { ApplicationStructure } from "./application-structure";
import { CurrentUser } from "./current-user";
import { NewConversation } from "@/features/chat/new-conversation";
import { ConversationDetails } from "@/features/chat/conversation-details";
const messageKey = (message: ChatMessage) =>
  message.id ||
  message.client_message_id ||
  `${message.conversation_id}:${message.sequence}`;
const realtimeMessage = (
  payload: NonNullable<RealtimeFrame["payload"]>,
): ChatMessage => ({ ...payload, id: payload.message_id ?? payload.id });
const time = (value?: string) =>
  value
    ? new Intl.DateTimeFormat(undefined, {
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(value))
    : "";

export function GlobalChatApp() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [requested, setRequested] = useState<Conversation | null>(null);
  useEffect(() => {
    const timer = setTimeout(() => {
      setAuthenticated(hasSession());
      setLoaded(true);
    }, 0);
    return () => clearTimeout(timer);
  }, []);
  const signOut = useCallback(() => {
    clearSession();
    setRequested(null);
    setAuthenticated(false);
  }, []);
  const signIn = useCallback(() => setAuthenticated(true), []);
  useEffect(() => {
    window.addEventListener("globalchat:session-expired", signOut);
    return () =>
      window.removeEventListener("globalchat:session-expired", signOut);
  }, [signOut]);
  if (!loaded)
    return (
      <main className="grid min-h-dvh place-items-center">
        <p role="status" className="animate-pulse font-semibold text-cyan-800">
          GlobalChat · Loading your workspace…
        </p>
      </main>
    );
  return authenticated ? (
    <ApplicationStructure onSignedOut={signOut} onConversation={setRequested}>
      <ChatShell onSignOut={signOut} requested={requested} />
    </ApplicationStructure>
  ) : (
    <Login onAuthenticated={signIn} />
  );
}
function ChatShell({
  onSignOut,
  requested,
}: {
  onSignOut: () => void;
  requested: Conversation | null;
}) {
  const token = getAccessToken();
  const memberId = getMemberId();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [connection, setConnection] = useState("Connecting…");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const [socketGeneration, setSocketGeneration] = useState(0);
  const selectedRef = useRef<string | null>(null);
  const retryRef = useRef(0);
  const retryTimer = useRef<number | undefined>(undefined);
  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const rows = await chatApi.listConversations(token);
      setConversations(rows);
      if (socketRef.current?.readyState === WebSocket.OPEN)
        for (const row of rows)
          socketRef.current.send(
            JSON.stringify({
              version: 1,
              type: "subscribe",
              conversation_id: row.id,
            }),
          );
      setSelected((current) =>
        current && rows.find((row) => row.id === current.id) ? current : null,
      );
    } catch (issue) {
      if (issue instanceof ApiError && issue.code === "UNAUTHORIZED")
        onSignOut();
      else
        setError(
          issue instanceof Error
            ? issue.message
            : "Unable to load conversations.",
        );
    } finally {
      setLoading(false);
    }
  }, [token, onSignOut]);
  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);
  useEffect(() => {
    if (!token) return;
    let closed = false;
    const reconciliation = setInterval(() => void load(), 15000);
    const heartbeat = setInterval(() => {
      if (socketRef.current?.readyState === WebSocket.OPEN)
        socketRef.current.send(
          JSON.stringify({ version: 1, type: "presence.heartbeat" }),
        );
    }, 30000);
    const open = () => {
      if (closed) return;
      const socket = connectRealtime(token);
      socketRef.current = socket;
      socket.onopen = () => {
        retryRef.current = 0;
        setConnection("Connected");
        void load();
        setSocketGeneration((n) => n + 1);
        if (selectedRef.current)
          socket.send(
            JSON.stringify({
              version: 1,
              type: "subscribe",
              conversation_id: selectedRef.current,
            }),
          );
      };
      socket.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data) as RealtimeFrame;
          if (
            frame.type.startsWith("conversation.") ||
            frame.type.startsWith("message.")
          )
            void load();
        } catch {}
      };
      socket.onerror = () => setConnection("Offline");
      socket.onclose = () => {
        if (closed) return;
        setConnection("Reconnecting…");
        const delay = Math.min(30_000, 1_000 * 2 ** retryRef.current++);
        retryTimer.current = window.setTimeout(open, delay);
      };
    };
    open();
    return () => {
      closed = true;
      clearInterval(heartbeat);
      clearInterval(reconciliation);
      window.clearTimeout(retryTimer.current);
      socketRef.current?.close();
    };
  }, [load, token]);
  useEffect(() => {
    if (!requested) return;
    const timer = setTimeout(() => {
      setSelected(requested);
      setMobileOpen(true);
      selectedRef.current = requested.id;
      if (socketRef.current?.readyState === WebSocket.OPEN)
        socketRef.current.send(
          JSON.stringify({
            version: 1,
            type: "subscribe",
            conversation_id: requested.id,
          }),
        );
    }, 0);
    return () => clearTimeout(timer);
  }, [requested]);
  const choose = (conversation: Conversation) => {
    setSelected(conversation);
    setMobileOpen(true);
    selectedRef.current = conversation.id;
    if (socketRef.current?.readyState === WebSocket.OPEN)
      socketRef.current.send(
        JSON.stringify({
          version: 1,
          type: "subscribe",
          conversation_id: conversation.id,
        }),
      );
  };
  return (
    <main className="flex min-h-0 flex-1 overflow-hidden bg-white">
      <aside
        className={`flex w-full shrink-0 flex-col border-r border-slate-200 bg-slate-50 md:w-[22rem] ${mobileOpen ? "hidden md:flex" : "flex"}`}
      >
        <header className="border-b border-slate-200 px-5 py-4">
          <p className="text-lg font-bold">GlobalChat</p>
          <CurrentUser token={token} />
          <p
            className={
              connection === "Connected"
                ? "text-xs text-emerald-700"
                : "text-xs text-amber-700"
            }
          >
            {connection}
          </p>
        </header>
        <div className="space-y-3 border-b border-slate-200 p-4">
          <input
            aria-label="Search conversations"
            placeholder="Search conversations"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
          />
          <button
            onClick={() => void load()}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-500"
          >
            Refresh conversations
          </button>
          <button
            onClick={() => setCreating(true)}
            className="text-sm font-semibold text-cyan-800"
          >
            + New conversation
          </button>
        </div>
        {loading && (
          <div className="space-y-3 p-4">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className="h-16 animate-pulse rounded-xl bg-slate-200"
              />
            ))}
          </div>
        )}
        {error && (
          <div className="m-4">
            <Notice message={error} />
            <button
              onClick={() => void load()}
              className="mt-2 text-sm font-semibold text-cyan-700"
            >
              Retry
            </button>
          </div>
        )}
        {!loading && !error && conversations.length === 0 && (
          <Empty
            text="No conversations yet"
            detail="Your workspace conversations will appear here."
          />
        )}
        {conversations
          .filter((conversation) =>
            (conversation.title || conversation.type)
              .toLowerCase()
              .includes(search.toLowerCase()),
          )
          .map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => choose(conversation)}
              className={`flex gap-3 border-b border-slate-200 px-4 py-4 text-left hover:bg-white ${selected?.id === conversation.id ? "bg-white" : ""}`}
            >
              <div className="grid size-10 shrink-0 place-items-center rounded-full bg-cyan-100 font-semibold text-cyan-700">
                {(conversation.title || conversation.type).slice(0, 1)}
              </div>
              <span className="min-w-0">
                <span className="block truncate font-semibold">
                  {conversation.title || "Direct conversation"}
                </span>
                <span className="block truncate text-xs text-slate-500">
                  {conversation.last_message_preview || "No messages yet"}
                </span>
                {conversation.last_message_at && (
                  <time className="text-[10px] text-slate-400">
                    {time(conversation.last_message_at)}
                  </time>
                )}
                {!!conversation.unread_count && (
                  <span
                    aria-label={`${conversation.unread_count} unread messages`}
                    className="ml-2 rounded-full bg-cyan-800 px-2 py-0.5 text-xs text-white"
                  >
                    {conversation.unread_count}
                  </span>
                )}
              </span>
            </button>
          ))}
      </aside>
      <section
        className={`flex min-w-0 flex-1 flex-col bg-slate-50 ${mobileOpen ? "flex" : "hidden md:flex"}`}
      >
        {selected ? (
          <ConversationView
            key={selected.id}
            conversation={selected}
            token={token}
            memberId={memberId}
            socket={socketRef}
            socketGeneration={socketGeneration}
            onBack={() => setMobileOpen(false)}
          />
        ) : (
          <Empty
            text="Select a conversation"
            detail="Choose a conversation to read and send messages."
          />
        )}
      </section>
      {creating && token && (
        <NewConversation
          token={token}
          onCancel={() => setCreating(false)}
          onCreated={(row) => {
            setCreating(false);
            choose(row);
            void load();
          }}
        />
      )}
    </main>
  );
}

function ConversationView({
  conversation,
  token,
  memberId,
  socket,
  socketGeneration,
  onBack,
}: {
  conversation: Conversation;
  token: string | null;
  memberId: string | null;
  socket: React.MutableRefObject<WebSocket | null>;
  socketGeneration: number;
  onBack: () => void;
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
  const [typers, setTypers] = useState<Record<string, number>>({});
  const typingLastSent = useRef(0);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const readSequence = useRef(0);
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
    if (!token || !sequence || sequence <= readSequence.current) return;
    let active = true;
    void chatApi
      .markDelivered(conversation.id, sequence, token)
      .then(() => chatApi.markRead(conversation.id, sequence, token))
      .then(() => {
        if (active) readSequence.current = sequence;
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [messages, conversation.id, token]);
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
  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }
  useEffect(() => { const latest=messages[messages.length-1]?.sequence || 0; if(latest <= previousLatest.current)return;previousLatest.current=latest;const timer=setTimeout(()=>{if(nearBottom.current){scroller.current?.scrollTo?.({top:scroller.current.scrollHeight,behavior:"smooth"});}else setNewMessages(true);},0);return()=>clearTimeout(timer);},[messages]);
  const oldest = messages[0]?.sequence;
  return (
    <>
      <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <button
          onClick={onBack}
          className="md:hidden"
          aria-label="Back to conversations"
        >
          ←
        </button>
        <div className="grid size-9 place-items-center rounded-full bg-cyan-100 text-cyan-700">
          {(conversation.title || conversation.type).slice(0, 1)}
        </div>
        <div>
          <p className="font-semibold">
            {conversation.title || "Direct conversation"}
          </p>
          <p className="text-xs text-slate-500">
            {conversation.member_count} members
          </p>
        </div>
        <ConversationDetails conversation={conversation} />
      </header>
      <div ref={scroller} onScroll={()=>{const element=scroller.current;if(element){nearBottom.current=element.scrollHeight-element.scrollTop-element.clientHeight<100;if(nearBottom.current)setNewMessages(false);}}} className="flex-1 overflow-y-auto p-4">
        <button
          disabled={!oldest}
          onClick={() => void load(oldest)}
          className="mx-auto mb-4 block text-xs font-semibold text-cyan-700 disabled:hidden"
        >
          Load older messages
        </button>
        {loading && (
          <p className="text-center text-sm text-slate-500">
            Loading messages…
          </p>
        )}
        {error && <Notice message={error} />}{" "}
        {messages.map((row, index) => (
          <div key={messageKey(row)}>
            {index === 0 ||
            new Date(row.created_at).toDateString() !==
              new Date(messages[index - 1].created_at).toDateString() ? (
              <p className="my-4 text-center text-xs text-slate-400">
                {new Intl.DateTimeFormat(undefined, {
                  dateStyle: "medium",
                }).format(new Date(row.created_at))}
              </p>
            ) : null}
            <div
              className={`mb-2 flex ${row.sender_member_id === memberId ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${row.sender_member_id === memberId ? "bg-cyan-700 text-white" : "bg-white shadow-sm"}`}
              >
                {!row.deleted_at && row.attachment && token && <MediaContent attachment={row.attachment} token={token} images={messages.flatMap(message => message.attachment?.media_type === "image" && !message.deleted_at ? [message.attachment] : [])}/>}
                <p>{row.deleted_at ? "Message deleted" : row.text}</p>
                <p
                  className={`mt-1 text-right text-[10px] ${row.sender_member_id === memberId ? "text-cyan-100" : "text-slate-400"}`}
                >
                  {time(row.created_at)}{" "}
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
      {newMessages && <button type="button" className="mx-auto rounded-full bg-cyan-700 px-4 py-2 text-white" onClick={()=>{nearBottom.current=true;scroller.current?.scrollTo?.({top:scroller.current.scrollHeight,behavior:"smooth"});setNewMessages(false);}}>New messages ↓</button>}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void send();
        }}
        className="border-t border-slate-200 bg-white p-3"
      >
        {Object.keys(typers).length > 0 && (
          <p role="status" className="text-xs text-slate-500">
            Someone is typing…
          </p>
        )}
        <Notice message={sendError} />
        {token && <AttachmentComposer conversationId={conversation.id} token={token} onSent={message => merge([message])}/>}
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
            className="min-h-11 flex-1 resize-none rounded-xl border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            disabled={!draft.trim() || sending}
            className="rounded-xl bg-cyan-700 px-4 text-sm font-semibold text-white disabled:opacity-50"
          >
            {sending ? "Sending" : "Send"}
          </button>
        </div>
      </form>
    </>
  );
}
function Notice({ message }: { message: string }) {
  return message ? (
    <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">
      {message}
    </p>
  ) : null;
}
function Empty({ text, detail }: { text: string; detail: string }) {
  return (
    <div className="m-auto max-w-sm p-8 text-center">
      <div className="mx-auto mb-4 grid size-14 place-items-center rounded-3xl bg-cyan-100 text-xl text-cyan-700">
        ✦
      </div>
      <p className="font-semibold">{text}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p>
    </div>
  );
}
