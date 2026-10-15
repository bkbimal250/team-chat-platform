"use client";

import { Bell } from "lucide-react";
import { SecondaryPanel } from "@/components/layout/secondary-panel";
import { ListRow } from "@/components/ui/list-row";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Avatar } from "@/components/ui/avatar";
import { EmptyState } from "@/components/ui/empty-state";
import { PanelPagination } from "@/components/ui/panel-pagination";
import { noticeDescription, noticeTime, noticeTitle } from "./notification-present";
import type { Notice } from "./types";

export function NotificationsListPanel({
  rows,
  loading,
  error,
  page,
  hasPrev,
  hasNext,
  selectedId,
  onSelect,
  onPageChange,
  onRetry,
  embedded = false,
}: {
  rows: Notice[];
  loading: boolean;
  error: string;
  page: number;
  hasPrev: boolean;
  hasNext: boolean;
  selectedId: string | null;
  onSelect: (row: Notice) => void;
  onPageChange: (page: number) => void;
  onRetry: () => void;
  embedded?: boolean;
}) {
  const body = (
    <>
      {loading && rows.length === 0 && (
        <div className="space-y-2 p-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-xl bg-aurora-surface-alt" />
          ))}
        </div>
      )}
      {error && (
        <div className="p-3">
          <AlertBanner message={error} />
          <button type="button" onClick={onRetry} className="mt-2 text-xs font-medium text-aurora-primary underline">
            Retry
          </button>
        </div>
      )}
      {!loading && !error && rows.length === 0 && (
        <div className="p-6">
          <EmptyState
            icon={Bell}
            title="No notifications"
            detail="Workspace alerts will show here when something needs your attention."
          />
        </div>
      )}
      <ul className="divide-y divide-aurora-border">
        {rows.map((row) => {
          const time = noticeTime(row);
          return (
            <li key={row.id}>
              <ListRow
                active={selectedId === row.id}
                onClick={() => onSelect(row)}
                leading={<Avatar name={noticeTitle(row)} />}
                title={noticeTitle(row)}
                subtitle={noticeDescription(row)}
                trailing={
                  time ? (
                    <span className="shrink-0 text-[11px] text-aurora-muted">{time}</span>
                  ) : undefined
                }
              />
            </li>
          );
        })}
      </ul>
      {(hasPrev || hasNext) && (
        <PanelPagination
          page={page}
          hasPrev={hasPrev}
          hasNext={hasNext}
          disabled={loading}
          onPrev={() => onPageChange(page - 1)}
          onNext={() => onPageChange(page + 1)}
        />
      )}
    </>
  );
  if (embedded) return <div className="flex h-full min-h-0 flex-col">{body}</div>;
  return <SecondaryPanel title="Notifications">{body}</SecondaryPanel>;
}
