"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { DataTable } from "@/components/data-table/data-table";
import { TablePagination } from "@/components/data-table/table-pagination";
import { ErrorState } from "@/components/feedback/error-state";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import type { Organization } from "@/lib/api/contracts";
import { ADMIN_REFRESH, refreshMatches } from "@/lib/realtime/refresh";

import { listOrganizations } from "../repository";

export function OrganizationsClient() {
  const [rows, setRows] = useState<Organization[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const result = await listOrganizations({ limit: 20, offset: (page - 1) * 20, search });
      setRows(result.items);
      setTotal(result.total);
      setError("");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Could not load organizations.",
      );
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    let active = true;
    listOrganizations({ limit: 20, offset: (page - 1) * 20, search })
      .then((result) => {
        if (active) {
          setRows(result.items);
          setTotal(result.total);
          setError("");
          setLoading(false);
        }
      })
      .catch((cause) => {
        if (active) {
          setError(
            cause instanceof Error
              ? cause.message
              : "Could not load organizations.",
          );
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [page, search]);
  useEffect(() => {
    const handler = (event: Event) => {
      if (
        refreshMatches(
          "/api/v1/platform/organizations/",
          (event as CustomEvent).detail,
        )
      ) {
        void reload();
      }
    };
    window.addEventListener(ADMIN_REFRESH, handler);
    return () => window.removeEventListener(ADMIN_REFRESH, handler);
  }, [reload]);

  return (
    <section className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Organizations</h1>
        <p className="text-sm text-slate-500">
          Read-only platform organization directory. Tenant administration
          remains scoped to each workspace.
        </p>
      </header>
      <Card className="p-4">
        <div className="mb-4 flex flex-wrap gap-3">
          <input aria-label="Search organizations" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search organization name" className="min-w-56 rounded border px-3 py-2" />
          <Button variant="outline" onClick={() => void reload()}>Refresh</Button>
        </div>
        {loading ? (
          <p role="status" className="p-8">
            Loading organizations…
          </p>
        ) : error ? (
          <ErrorState description={error} retry={() => void reload()} />
        ) : (
          <DataTable
            rows={rows}
            getRowKey={(row) => row.id}
            columns={[
              {
                header: "Organization",
                cell: (row) => (
                  <Link
                    className="text-indigo-700 underline"
                    href={`/organizations/${row.id}`}
                  >
                    {row.display_name || row.name}
                  </Link>
                ),
              },
              {
                header: "Status",
                cell: (row) => <StatusBadge status={row.status} />,
              },
              {
                header: "Created",
                cell: (row) =>
                  row.created_at
                    ? new Date(row.created_at).toLocaleDateString()
                    : "—",
              },
              {
                header: "Actions",
                cell: (row) => (
                  <Link
                    className="text-indigo-700 underline"
                    href={`/organizations/${row.id}`}
                  >
                    View
                  </Link>
                ),
              },
            ]}
          />
        )}
        {!loading && !error && <TablePagination page={page} total={Math.max(1, Math.ceil(total / 20))} onPageChange={setPage} />}
      </Card>
    </section>
  );
}
