"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";
import { isAbortError, safeAbort } from "@/workspace/lib/api/abort";
import { getAccessToken, getMemberId } from "@/lib/auth/session";
import { connectRealtime } from "@/lib/websocket/connection";
import { refreshAdmin } from "@/workspace/lib/realtime/refresh";
import { chatApi, Conversation, RealtimeFrame } from "./api";

export function useChatController({
  personal,
  onSignOut,
  requested,
}: {
  personal: boolean;
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
  const [filter, setFilter] = useState<"all" | "unread" | "groups">("all");
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const [socketGeneration, setSocketGeneration] = useState(0);
  const selectedRef = useRef<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const loadSeq = useRef(0);
  const loaded = useRef(false);
  const signOutRef = useRef(onSignOut);
  useEffect(() => { signOutRef.current = onSignOut; }, [onSignOut]);
  const retryRef = useRef(0);
  const retryTimer = useRef<number | undefined>(undefined);

  const load = useCallback(async () => {
    if (!token) return;
    const seq = ++loadSeq.current;
    const request = new AbortController();
    requestRef.current = request;
    if (!loaded.current) setLoading(true);
    setError("");
    try {
      const rows = await chatApi.listConversations(token, request.signal);
      if (seq !== loadSeq.current || request.signal.aborted) return;
      loaded.current = true;
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
      const requestedId = new URLSearchParams(window.location.search).get(
        "conversation",
      );
      if (requestedId && rows.some((row) => row.id === requestedId))
        setMobileOpen(true);
      setSelected((current) => {
        const next =
          rows.find((row) => row.id === (current?.id ?? requestedId)) ?? null;
        selectedRef.current = next?.id ?? null;
        return next;
      });
    } catch (issue) {
      if (seq !== loadSeq.current || isAbortError(issue) || request.signal.aborted)
        return;
      if (issue instanceof ApiError && (issue.status === 401 || issue.code === "UNAUTHORIZED"))
        signOutRef.current();
      else
        setError(
          issue instanceof Error
            ? issue.message
            : "Unable to load conversations.",
        );
    } finally {
      if (seq === loadSeq.current && !request.signal.aborted) setLoading(false);
    }
  }, [token]);

  const scheduleLoad = useCallback(() => {
    void load().catch((issue) => {
      if (!isAbortError(issue)) return;
    });
  }, [load]);

  useEffect(() => {
    const timer = window.setTimeout(() => scheduleLoad(), 0);
    return () => {
      window.clearTimeout(timer);
      loadSeq.current += 1;
      safeAbort(requestRef.current);
      requestRef.current = null;
      loaded.current = false;
    };
  }, [scheduleLoad]);

  useEffect(() => {
    if (!token) return;
    let closed = false;
    const reconciliation = setInterval(() => scheduleLoad(), 15000);
    const heartbeat = setInterval(() => {
      if (socketRef.current?.readyState === WebSocket.OPEN)
        socketRef.current.send(
          JSON.stringify({ version: 1, type: "presence.heartbeat" }),
        );
    }, 30000);
    const open = () => {
      if (closed) return;
      if (!navigator.onLine) { setConnection("Offline"); return; }
      const socket = connectRealtime(token);
      socketRef.current = socket;
      socket.onopen = () => {
        if (closed) return;
        retryRef.current = 0;
        setConnection("Connected");
        refreshAdmin();
        scheduleLoad();
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
        if (closed) return;
        try {
          const frame = JSON.parse(event.data) as RealtimeFrame;
          if (
            frame.type.startsWith("conversation.") ||
            frame.type.startsWith("message.")
          )
            scheduleLoad();
        } catch {}
      };
      socket.onerror = () => { if (!closed) setConnection("Offline"); };
      socket.onclose = () => {
        if (closed) return;
        setConnection("Reconnecting…");
        const delay = Math.min(30_000, 1_000 * 2 ** retryRef.current++);
        retryTimer.current = window.setTimeout(open, delay);
      };
    };
    // Defer connection creation so StrictMode's discarded setup never opens a socket.
    const initial = window.setTimeout(open, 0);
    const online = () => {
      window.clearTimeout(retryTimer.current);
      if (!socketRef.current || socketRef.current.readyState === WebSocket.CLOSED) open();
      scheduleLoad();
    };
    const offline = () => setConnection("Offline");
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.clearTimeout(initial);
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
      closed = true;
      clearInterval(heartbeat);
      clearInterval(reconciliation);
      window.clearTimeout(retryTimer.current);
      const socket = socketRef.current;
      socketRef.current = null;
      if (socket) {
        socket.onmessage = null; socket.onerror = null; socket.onclose = null;
        if (socket.readyState === WebSocket.CONNECTING) socket.onopen = () => socket.close();
        else { socket.onopen = null; socket.close(); }
      }
    };
  }, [scheduleLoad, token]);

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

  const choose = useCallback(
    (conversation: Conversation) => {
      setSelected(conversation);
      setConversations((rows) =>
        rows.map((row) =>
          row.id === conversation.id ? { ...row, unread_count: 0 } : row,
        ),
      );
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
    },
    [],
  );

  const filtered = conversations.filter((conversation) =>
    (filter !== "unread" || (conversation.unread_count ?? 0) > 0) &&
    (filter !== "groups" || conversation.type === "GROUP") &&
    [conversation.title || conversation.type, conversation.last_message_preview ?? ""]
      .join(" ").toLowerCase()
      .includes(search.trim().toLowerCase()),
  );

  const unreadTotal = conversations.reduce(
    (sum, c) => sum + (c.unread_count || 0),
    0,
  );

  return {
    token,
    memberId,
    personal,
    conversations: filtered,
    allConversations: conversations,
    selected,
    loading,
    error,
    connection,
    mobileOpen,
    setMobileOpen,
    search,
    setSearch,
    filter,
    setFilter,
    creating,
    setCreating,
    socketRef,
    socketGeneration,
    load: scheduleLoad,
    choose,
    unreadTotal,
  };
}
