"use client";

import { useState } from "react";
import { Filter, Plus } from "lucide-react";
import { useAuth } from "@/workspace/features/auth/auth-provider";
import { useResource } from "@/workspace/lib/api/use-resource";
import type { CursorPage } from "@/workspace/lib/api/contracts";
import { configs } from "@/workspace/features/admin/resource-config";
import { SecondaryPanel } from "@/components/layout/secondary-panel";
import { SearchField } from "@/components/ui/search-field";
import { ListRow } from "@/components/ui/list-row";
import { Avatar } from "@/components/ui/avatar";
import { AlertBanner } from "@/components/ui/alert-banner";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { StatusPill } from "@/components/workspace/status-pill";
import { humanStatus } from "@/components/content/format";
import { FilterBar } from "@/components/workspace/filter-bar";
import { Selection } from "@/workspace/features/admin/invitations-client";

export type WorkspaceRow = {
  id: string;
  [key: string]: string | number | boolean | null | string[];
};

export function WorkspaceListPanel({
  resource,
  selectedId,
  onSelect,
  onAdd,
}: {
  resource: string;
  selectedId: string | null;
  onSelect: (row: WorkspaceRow) => void;
  onAdd?: () => void;
}) {
  const config = configs[resource];
  const auth = useAuth();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});
  const query = new URLSearchParams({ page_size: "50" });
  if (search) query.set("search", search);
  if (status) query.set("status", status);
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const response = useResource<CursorPage<WorkspaceRow>>(
    `/api/v1/${config.resource}/?${query}`,
    auth.permissions.has(config.readPermission),
  );
  const canCreate = config.create && auth.permissions.has(`${config.permission}.create`);
  const labelKey = config.columns[0]?.key ?? "name";

  function subtitle(row: WorkspaceRow) {
    if (resource === "members") {
      const roles = Array.isArray(row.roles) ? row.roles.join(", ") : "";
      const st = String(row.status ?? "");
      return [roles, st].filter(Boolean).join(" · ");
    }
    if (resource === "invitations") {
      return String(row.recipient_email ?? row.status ?? "");
    }
    const col = config.columns.find((c) => c.key === "status");
    return col ? String(row[col.key] ?? "") : "";
  }

  return (
    <SecondaryPanel
      title={config.title}
      actions={
        <>
          {canCreate && onAdd && (
            <IconButton label={`Add ${config.title.toLowerCase()}`} onClick={onAdd} className="text-aurora-primary">
              <Plus className={iconSize} />
            </IconButton>
          )}
          {config.statuses && (
            <IconButton label="Filter by status" className="text-aurora-muted">
              <Filter className={iconSize} />
            </IconButton>
          )}
        </>
      }
    >
      <FilterBar>
        {config.search && (
          <SearchField label={`Search ${config.title}`} value={search} onChange={setSearch} />
        )}
        {config.statuses && (
          <select
            aria-label="Status filter"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full rounded-xl border border-aurora-border bg-aurora-background px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            {config.statuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        )}
        {resource === "members" &&
          (["branch", "team", "role"] as const)
            .filter(
              (kind) =>
                auth.permissions.has(`${kind}.view`) ||
                (kind === "role" && auth.permissions.has("role.manage")),
            )
            .map((kind) => (
              <Selection
                key={kind}
                resource={kind === "branch" ? "branches" : kind === "team" ? "teams" : "roles"}
                label={`${kind} filter`}
                value={filters[kind] ?? ""}
                onChange={(value) => setFilters({ ...filters, [kind]: value })}
              />
            ))}
      </FilterBar>
      {response.loading && <p role="status" className="p-4 text-sm text-aurora-muted animate-pulse">Loading…</p>}
      {response.error && <div className="p-3"><AlertBanner message={response.error} /></div>}
      <ul className="divide-y divide-aurora-border">
        {response.data?.results.map((row) => {
          const title = String(row[labelKey] ?? row.recipient_name ?? row.id);
          return (
            <li key={row.id}>
              <ListRow
                active={selectedId === row.id}
                onClick={() => onSelect(row)}
                leading={<Avatar name={title} />}
                title={title}
                subtitle={subtitle(row)}
                trailing={
                  row.status ? (
                    <StatusPill tone={String(row.status) === "ACTIVE" ? "success" : "neutral"}>
                      {humanStatus(String(row.status))}
                    </StatusPill>
                  ) : undefined
                }
              />
            </li>
          );
        })}
      </ul>
    </SecondaryPanel>
  );
}
