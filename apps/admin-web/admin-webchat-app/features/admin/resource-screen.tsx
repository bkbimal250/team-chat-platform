"use client";

import { useState } from "react";

import { apiRequest, gatewayPath } from "@/lib/api/client";

import type { CursorPage, Role } from "@/lib/api/contracts";

import { useResource } from "@/lib/api/use-resource";

import { useAuth } from "@/features/auth/auth-provider";

import { DataTable } from "@/components/data-table/data-table";

import { TableToolbar } from "@/components/data-table/table-toolbar";

import { TableEmpty } from "@/components/data-table/table-empty";

import { TablePagination } from "@/components/data-table/table-pagination";

import { Modal } from "@/components/ui/modal";

import { Button } from "@/components/ui/button";

import { Card } from "@/components/ui/card";

import { StatusBadge } from "@/components/ui/status-badge";

import { ErrorState } from "@/components/feedback/error-state";

import { configs, formPayload, type ResourceConfig } from "./resource-config";

function displayValue(value: string | number | boolean | null | string[]) {
  return Array.isArray(value) ? value.join(", ") : String(value ?? "—");
}

type Row = {
  id: string;
  [key: string]: string | number | boolean | null | string[];
};

export function ResourceScreen({
  resource,
  compact = false,
}: {
  resource: string;
  compact?: boolean;
}) {
  const config: ResourceConfig = configs[resource];
  const auth = useAuth();

  const [search, setSearch] = useState(""),
    [draft, setDraft] = useState(""),
    [status, setStatus] = useState(""),
    [size, setSize] = useState(20),
    [cursor, setCursor] = useState<string | null>(null),
    [page, setPage] = useState(1);

  const query = new URLSearchParams({ page_size: String(size) });
  if (search) query.set("search", search);
  if (status) query.set("status", status);

  const path = cursor ?? `/api/v1/${config.resource}/?${query}`;

  const response = useResource<CursorPage<Row>>(path);
  const roles = useResource<CursorPage<Role>>("/api/v1/roles/");

  const [selected, setSelected] = useState<Row | null>(null),
    [mode, setMode] = useState<
      "create" | "edit" | "view" | "lifecycle" | "role" | null
    >(null),
    [values, setValues] = useState<Record<string, string>>({}),
    [target, setTarget] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");

  const can = (action: string) =>
    auth.permissions.has(`${config.permission}.${action}`);

  function reset() {
    setCursor(null);
    setPage(1);
  }

  function open(action: typeof mode, row: Row | null = null, next = "") {
    setSelected(row);
    setMode(action);
    setError("");
    setTarget(next);
    setValues(
      Object.fromEntries(
        config.fields.map((f) => [
          f.name,
          typeof row?.[f.name] === "string"
            ? String(row[f.name])
            : (f.options?.[0] ?? ""),
        ]),
      ),
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      if (mode === "role")
        await apiRequest(`/api/v1/members/${selected?.id}/roles/`, {
          method: "POST",
          body: JSON.stringify({ role_id: values.role_id }),
        });
      else if (mode === "lifecycle")
        await apiRequest(
          `/api/v1/${config.resource}/${selected?.id}/${config.lifecycle === "invitation" ? "revoke" : "lifecycle"}/`,
          {
            method: "POST",
            body:
              config.lifecycle === "invitation"
                ? "{}"
                : JSON.stringify({ status: target }),
          },
        );
      else
        await apiRequest(
          `/api/v1/${config.resource}/${mode === "edit" ? selected?.id + "/" : ""}`,
          {
            method: mode === "edit" ? "PATCH" : "POST",
            body: JSON.stringify(formPayload(config.fields, values)),
          },
        );

      setMode(null);
      setNotice("Saved by Organization service.");
      response.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  if (!auth.permissions.has(config.readPermission))
    return (
      <ErrorState
        title="Access restricted"
        description="Your backend role does not grant access to this resource."
      />
    );

  return (
    <section className="space-y-4">
      {!compact && (
        <header>
          <h1 className="text-2xl font-semibold">{config.title}</h1>
          <p className="text-sm text-slate-500">
            Current organization only. Data and permissions are enforced by the
            backend.
          </p>
        </header>
      )}
      <Card className="p-4">
        <TableToolbar>
          {config.search && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                setSearch(draft);
                reset();
              }}
              className="flex gap-2"
            >
              <label className="sr-only" htmlFor={`${resource}-search`}>
                Search {config.title}
              </label>
              <input
                id={`${resource}-search`}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="rounded border p-2"
              />
              <Button variant="outline" type="submit">
                Search
              </Button>
            </form>
          )}
          {config.statuses && (
            <label>
              Status{" "}
              <select
                aria-label="Status filter"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  reset();
                }}
                className="rounded border p-2"
              >
                <option value="">All statuses</option>
                {config.statuses.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          )}
          <span className="text-sm text-slate-500">
            Newest first (server ordering)
          </span>
          <label>
            Page size{" "}
            <select
              value={size}
              onChange={(e) => {
                setSize(Number(e.target.value));
                reset();
              }}
              className="rounded border p-2"
            >
              {[10, 20, 50].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
          {config.create && can("create") && (
            <Button onClick={() => open("create")}>
              Add{" "}
              {resource === "members"
                ? "member"
                : resource === "invitations"
                  ? "invitation"
                  : resource === "teams"
                    ? "team"
                    : "branch"}
            </Button>
          )}
          <Button variant="outline" onClick={response.reload}>
            Refresh
          </Button>
        </TableToolbar>
        {notice && (
          <p role="status" className="my-3 text-emerald-700">
            {notice}
          </p>
        )}
        {response.loading ? (
          <p role="status" className="animate-pulse p-8">
            Loading {config.title.toLowerCase()}…
          </p>
        ) : response.error ? (
          <ErrorState description={response.error} retry={response.reload} />
        ) : !response.data?.results.length ? (
          <TableEmpty />
        ) : (
          <DataTable
            rows={response.data.results}
            getRowKey={(r) => r.id}
            columns={[
              ...config.columns.map((c) => ({
                header: c.label,
                cell: (row: Row) =>
                  c.key === "status" ? (
                    <StatusBadge status={String(row[c.key])} />
                  ) : (
                    displayValue(row[c.key])
                  ),
              })),
              {
                header: "Actions",
                cell: (row) => (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => open("view", row)}
                    >
                      View
                    </Button>
                    {config.edit && can("update") && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => open("edit", row)}
                      >
                        Edit
                      </Button>
                    )}
                    {config.lifecycle === "resource" &&
                      can("update") &&
                      ["ACTIVE", "DISABLED"].includes(String(row.status)) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            open(
                              "lifecycle",
                              row,
                              row.status === "ACTIVE" ? "DISABLED" : "ACTIVE",
                            )
                          }
                        >
                          {row.status === "ACTIVE" ? "Disable" : "Activate"}
                        </Button>
                      )}
                    {config.lifecycle === "member" &&
                      can("update") &&
                      ["ACTIVE", "SUSPENDED"].includes(String(row.status)) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            open(
                              "lifecycle",
                              row,
                              row.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE",
                            )
                          }
                        >
                          {row.status === "ACTIVE" ? "Suspend" : "Activate"}
                        </Button>
                      )}
                    {config.lifecycle === "member" &&
                      can("remove") &&
                      ["ACTIVE", "INVITED", "SUSPENDED"].includes(
                        String(row.status),
                      ) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => open("lifecycle", row, "REMOVED")}
                        >
                          Remove
                        </Button>
                      )}
                    {resource === "members" &&
                      auth.permissions.has("role.manage") && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => open("role", row)}
                        >
                          Assign role
                        </Button>
                      )}
                    {config.lifecycle === "invitation" &&
                      can("revoke") &&
                      row.status === "PENDING" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => open("lifecycle", row)}
                        >
                          Revoke
                        </Button>
                      )}
                  </div>
                ),
              },
            ]}
          />
        )}
        <TablePagination
          page={page}
          total={response.data?.next ? page + 1 : page}
          onPageChange={(n) => {
            const next =
              n > page ? response.data?.next : response.data?.previous;
            if (next) {
              setCursor(gatewayPath(next));
              setPage(n);
            }
          }}
        />
        <p className="mt-2 text-xs text-slate-500">
          Cursor pagination; no global total is exposed.
        </p>
      </Card>
      <Modal
        open={mode !== null}
        onClose={() => {
          if (!busy) setMode(null);
        }}
        title={
          mode === "create"
            ? `Add ${config.title.toLowerCase()}`
            : mode === "lifecycle"
              ? "Confirm change"
              : mode === "role"
                ? "Assign member role"
                : mode === "view"
                  ? "Details"
                  : "Edit details"
        }
      >
        {mode === "view" ? (
          <dl className="mt-4 max-h-96 space-y-2 overflow-auto">
            {selected &&
              Object.entries(selected).map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs font-medium text-slate-500">{k}</dt>
                  <dd className="break-words text-sm">
                    {Array.isArray(v) ? v.join(", ") : String(v ?? "—")}
                  </dd>
                </div>
              ))}
          </dl>
        ) : (
          <form onSubmit={submit} className="mt-4 space-y-3">
            {mode === "lifecycle" ? (
              <p>
                This will{" "}
                {config.lifecycle === "invitation"
                  ? "revoke the invitation"
                  : `set this ${config.permission} to ${target}`}
                . The backend enforces lifecycle and owner protections.
              </p>
            ) : mode === "role" ? (
              <label className="block">
                Role
                <select
                  required
                  value={values.role_id ?? ""}
                  onChange={(e) => setValues({ role_id: e.target.value })}
                  className="mt-1 w-full rounded border p-2"
                >
                  <option value="">Choose a role</option>
                  {roles.data?.results.map((r) => (
                    <option value={r.id} key={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              config.fields.map((f) => (
                <label className="block text-sm" key={f.name}>
                  {f.label}
                  {f.options || f.name === "intended_role_id" ? (
                    <select
                      required={f.required}
                      value={values[f.name] ?? ""}
                      onChange={(e) =>
                        setValues({ ...values, [f.name]: e.target.value })
                      }
                      className="mt-1 w-full rounded border p-2"
                    >
                      <option value="">Choose</option>
                      {f.name === "intended_role_id"
                        ? roles.data?.results.map((r) => (
                            <option key={r.id} value={r.id}>
                              {r.name}
                            </option>
                          ))
                        : f.options?.map((o) => <option key={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input
                      required={f.required}
                      maxLength={f.maxLength}
                      pattern={f.pattern}
                      type={f.type ?? "text"}
                      value={values[f.name] ?? ""}
                      onChange={(e) =>
                        setValues({ ...values, [f.name]: e.target.value })
                      }
                      className="mt-1 w-full rounded border p-2"
                    />
                  )}
                </label>
              ))
            )}
            {resource === "members" && mode === "create" && (
              <p className="text-xs text-slate-500">
                Creates an unlinked membership, not a registered identity.
              </p>
            )}
            {error && (
              <p role="alert" className="text-rose-700">
                {error}
              </p>
            )}
            <div className="flex gap-2">
              <Button disabled={busy} type="submit">
                {busy ? "Saving…" : mode === "lifecycle" ? "Confirm" : "Save"}
              </Button>
              <Button
                disabled={busy}
                variant="outline"
                type="button"
                onClick={() => setMode(null)}
              >
                Cancel
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </section>
  );
}
