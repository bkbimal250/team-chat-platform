"use client";
import { FormEvent, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import { Conversation } from "./api";
export function WorkspacePeople({
  token,
  onConversation,
}: {
  token: string;
  onConversation: (row: Conversation) => void;
}) {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<
    {
      user_id: string;
      member_id: string;
      display_name: string;
      status: string;
    }[]
  >([]);
  const [message, setMessage] = useState(
    "Search people in your workspace to start a direct chat.",
  );
  const [busy, setBusy] = useState(false);
  async function search(event: FormEvent) {
    event.preventDefault();
    if (busy || query.trim().length < 2) return;
    setBusy(true);
    try {
      const result = await apiRequest<{ users: typeof rows }>(
        `/api/v1/users/search?q=${encodeURIComponent(query.trim())}`,
        {},
        token,
      );
      setRows(result.users);
      setMessage(result.users.length ? "" : "No matching workspace people.");
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "People search unavailable.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function open(memberId: string) {
    if (busy) return;
    setBusy(true);
    try {
      const row = await apiRequest<Conversation>(
        "/api/v1/conversations/direct",
        { method: "POST", body: JSON.stringify({ member_id: memberId }) },
        token,
      );
      onConversation(row);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Unable to open direct chat.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <form onSubmit={search} className="my-6 flex gap-3">
        <input
          aria-label="Search people"
          required
          minLength={2}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name"
          className="min-w-0 flex-1 rounded-xl border bg-white px-4 py-3"
        />
        <button
          disabled={busy}
          className="rounded-xl bg-cyan-800 px-4 py-3 text-white"
        >
          {busy ? "Working…" : "Search"}
        </button>
      </form>
      <p role="status" className="text-sm text-slate-500">
        {message}
      </p>
      <div className="space-y-3">
        {rows.map((row) => (
          <article
            key={row.member_id}
            className="flex items-center justify-between gap-3 rounded-2xl border bg-white p-5"
          >
            <div>
              <h2 className="font-semibold">{row.display_name}</h2>
              <p className="mt-2 text-sm text-slate-500">{row.status}</p>
            </div>
            <button
              disabled={busy || !row.member_id}
              onClick={() => void open(row.member_id)}
              className="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
            >
              Chat
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
