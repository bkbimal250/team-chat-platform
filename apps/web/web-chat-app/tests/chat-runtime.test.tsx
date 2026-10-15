import { StrictMode } from "react";
import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useContacts } from "../features/contacts/use-contacts";
import { useNotifications } from "../features/notifications/use-notifications";
import { useChatController } from "../features/chat/use-chat-controller";
import { chatApi } from "../features/chat/api";
import { SearchField } from "../components/ui/search-field";
import { saveSession, clearSession } from "../lib/auth/session";

afterEach(() => { clearSession(); vi.unstubAllGlobals(); });

it("StrictMode contacts and notifications cancel fetches without unhandled rejections", async () => {
  const signals: AbortSignal[] = [];
  vi.stubGlobal("fetch", vi.fn((_url, options: RequestInit) => new Promise((_resolve, reject) => {
    const signal = options.signal!; signals.push(signal);
    signal.addEventListener("abort", () => reject(new DOMException("Cancelled", "AbortError")), { once: true });
  })));
  const { unmount } = renderHook(() => { useContacts(); useNotifications(0); }, { wrapper: StrictMode });
  await waitFor(() => expect(signals).toHaveLength(2));
  unmount();
  await act(async () => { await Promise.resolve(); });
  expect(signals.every(signal => signal.aborted)).toBe(true);
});

it("search has an accessible clear action and Escape clears the query", () => {
  const change = vi.fn();
  render(<SearchField label="Search conversations" value="Alex" onChange={change}/>);
  fireEvent.click(screen.getByRole("button", { name: "Clear search conversations" }));
  expect(change).toHaveBeenCalledWith("");
  fireEvent.keyDown(screen.getByRole("searchbox"), { key: "Escape" });
  expect(change).toHaveBeenCalledTimes(2);
});

it("StrictMode opens only one realtime connection and ignores stale conversation responses", async () => {
  const sockets: Socket[] = [];
  class Socket {
    static OPEN = 1; static CONNECTING = 0; static CLOSED = 3;
    readyState = 1;
    onopen: (() => void) | null = null; onclose: (() => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null; onerror = null;
    send = vi.fn(); close = vi.fn(() => { this.readyState = 3; });
    constructor() { sockets.push(this); }
  }
  vi.stubGlobal("WebSocket", Socket);
  saveSession({ access_token: `header.${btoa(JSON.stringify({ sub: "self" }))}.signature`, refresh_token: null });
  let resolveOld!: (rows: Awaited<ReturnType<typeof chatApi.listConversations>>) => void;
  const api = vi.spyOn(chatApi, "listConversations").mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; })).mockResolvedValue([]);
  const { result, unmount } = renderHook(() => useChatController({ personal: true, onSignOut: vi.fn(), requested: null }), { wrapper: StrictMode });
  await waitFor(() => { expect(sockets).toHaveLength(1); expect(api).toHaveBeenCalledOnce(); });
  await act(async () => { await result.current.load(); });
  await act(async () => { resolveOld([{ id: "stale", title: "Stale", type: "DIRECT", description: null, avatar_media_id: null, member_count: 2, status: "ACTIVE" }]); });
  expect(result.current.conversations).toEqual([]);
  unmount(); expect(sockets[0].close).toHaveBeenCalledOnce();
});
