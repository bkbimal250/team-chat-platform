"use client";

import { useState } from "react";

import type { Notification } from "@/lib/api/contracts";

import { useResource } from "@/lib/api/use-resource";

import { Card } from "@/components/ui/card";

import { ErrorState } from "@/components/feedback/error-state";

import { TableEmpty } from "@/components/data-table/table-empty";

import { Button } from "@/components/ui/button";

export function NotificationsClient() {
  const [page, setPage] = useState(0);
  const response = useResource<Notification[]>(
    `/api/v1/notifications?limit=20&offset=${page * 20}`,
  );
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Your notifications</h1>
      <p className="text-sm text-slate-500">
        Own-account inbox only. Admin-wide notifications, unread counts,
        mark-read and browser push are unavailable. Conversation/message IDs are
        references, not permission to inspect private content.
      </p>
      {response.loading ? (
        <p role="status">Loading notifications…</p>
      ) : response.error ? (
        <ErrorState description={response.error} retry={response.reload} />
      ) : !response.data?.length ? (
        <TableEmpty />
      ) : (
        <ul className="space-y-3">
          {response.data.map((row) => (
            <li key={row.id}>
              <Card className="p-4">
                <h2 className="font-semibold">
                  {row.preview_mode === "NONE" ? "New notification" : row.title}
                </h2>
                {row.preview_mode === "FULL" && (
                  <p className="mt-1 text-sm">{row.body}</p>
                )}
              </Card>
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-3">
        <Button
          variant="outline"
          disabled={page === 0 || response.loading}
          onClick={() => setPage((p) => p - 1)}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          disabled={response.loading || (response.data?.length ?? 0) < 20}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
        <Button variant="outline" onClick={response.reload}>
          Refresh
        </Button>
      </div>
    </section>
  );
}
