import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { GlobalChatApp } from "../components/globalchat-app";
import { chatApi } from "../features/chat/api";
import { saveSession, clearSession } from "../lib/auth/session";
import * as api from "../lib/api/client";
it("real chat UI renders server summaries, sends read receipts and displays typing", async () => {
 const frames: unknown[] = [];
 class Socket extends EventTarget {
  static OPEN = 1; readyState = 1; onopen: (() => void) | null = null; onmessage: ((event: MessageEvent) => void) | null = null; onclose: (() => void) | null = null; onerror: (() => void) | null = null;
  constructor() { super(); sockets.push(this); setTimeout(() => this.onopen?.(), 0); }
  send(value: string) { frames.push(JSON.parse(value)); }
  close() { this.readyState = 3; }
 }
 const sockets: Socket[] = [];
 vi.stubGlobal("WebSocket", Socket);
 const conversation = { id: "conversation", type: "GROUP", title: "Team", description: null, avatar_media_id: null, status: "ACTIVE", member_count: 2, unread_count: 2, last_message_preview: "Server preview", last_message_at: "2026-01-01T12:00:00Z" };
 vi.spyOn(chatApi, "listConversations").mockResolvedValue([conversation]);
 vi.spyOn(chatApi, "listMessages").mockResolvedValue([{ id: "message", conversation_id: "conversation", sender_member_id: "peer", type: "TEXT", text: "Real history", sequence: 5, status: "ACTIVE", created_at: "2026-01-01T12:00:00Z" }]);
 const delivered = vi.spyOn(chatApi, "markDelivered").mockResolvedValue({}); const read = vi.spyOn(chatApi, "markRead").mockResolvedValue({});
 vi.spyOn(api, "apiRequest").mockResolvedValue({ display_name: "Member" });
 saveSession({ access_token: `header.${btoa(JSON.stringify({ mid: "self" }))}.signature`, refresh_token: null });
 const { unmount } = render(<GlobalChatApp/>);
 await screen.findByText("Server preview"); expect(screen.getByLabelText("2 unread messages")).toBeTruthy();
 fireEvent.click(screen.getByRole("button", { name: /Team.*Server preview/ })); await screen.findByText("Real history"); await waitFor(() => expect(read).toHaveBeenCalled()); expect(delivered).toHaveBeenCalled();
 await waitFor(() => expect(sockets.length).toBeGreaterThan(0)); const socket = sockets[sockets.length - 1];
 act(() => { socket.dispatchEvent(new MessageEvent("message", { data: JSON.stringify({ version: 1, type: "typing.updated.v1", payload: { conversation_id: "conversation", member_id: "peer", active: true, expires_at: new Date(Date.now() + 5000).toISOString() } }) })); });
 expect(screen.getByText("Someone is typing…")).toBeTruthy();
 fireEvent.change(screen.getByPlaceholderText("Write a message"), { target: { value: "Hello" } }); expect(frames).toContainEqual({ version: 1, type: "typing.start", conversation_id: "conversation" });
 act(() => { socket.dispatchEvent(new MessageEvent("message", { data: JSON.stringify({ version: 1, type: "typing.updated.v1", payload: { conversation_id: "conversation", member_id: "peer", active: false } }) })); });
 expect(screen.queryByText("Someone is typing…")).toBeNull(); unmount(); clearSession(); vi.unstubAllGlobals();
});
