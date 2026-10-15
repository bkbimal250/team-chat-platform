"use client";

import Link from "next/link";
import { useState } from "react";

import { apiRequest, gatewayPath } from "@/lib/api/client";

import type { CursorPage } from "@/lib/api/contracts";

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

import { IdentityDisplay } from "@/components/ui/identity-display";
import { Selection } from "./invitations-client";
import { refreshAdmin } from "@/lib/realtime/refresh";
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

  const [filters, setFilters] = useState<Record<string,string>>({});
  const query = new URLSearchParams({ page_size: String(size) });
  if (search) query.set("search", search);
  Object.entries(filters).forEach(([key,value])=>{ if(value) query.set(key,value); });
  if (status) query.set("status", status);

  const path = cursor ?? `/api/v1/${config.resource}/?${query}`;

  const response = useResource<CursorPage<Row>>(path, auth.permissions.has(config.readPermission));


  const [selected, setSelected] = useState<Row | null>(null),
    [mode, setMode] = useState<
      "create" | "edit" | "view" | "lifecycle" | "role" | "assignment" | null
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
      if (mode === "assignment")
        await apiRequest(`/api/v1/${values.assignment_kind}/${values.assignment_id}/members/`, {method:"POST", body:JSON.stringify({member_id:selected?.id})});
      else if (mode === "role")
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
      setNotice(mode === "create" ? `${config.title} created.` : mode === "assignment" ? "Member assignment saved." : mode === "lifecycle" ? "Access updated." : "Changes saved.");
      refreshAdmin([config.resource, "branches", "teams", "audit-logs"]);
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
              className="flex min-w-0 flex-wrap gap-2"
            >
              <label className="sr-only" htmlFor={`${resource}-search`}>
                Search {config.title}
              </label>
              <input
                id={`${resource}-search`}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="min-w-0 rounded border p-2"
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
                className="min-w-0 rounded border p-2"
              >
                <option value="">All statuses</option>
                {config.statuses.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
          )}
          {resource === "members" && <div className="grid w-full gap-3 sm:grid-cols-3">{(["branch","team","role"] as const).filter(kind=>auth.permissions.has(`${kind}.view`) || (kind === "role" && auth.permissions.has("role.manage"))).map(kind=><Selection key={kind} resource={kind === "branch" ? "branches" : kind === "team" ? "teams" : "roles"} label={`${kind[0].toUpperCase()+kind.slice(1)} filter`} value={filters[kind] ?? ""} onChange={value=>{setFilters({...filters,[kind]:value});reset();}}/>)}</div>}
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
              className="min-w-0 rounded border p-2"
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
          <div className="py-6 text-center"><TableEmpty/><p className="text-sm text-slate-500">{search || status ? "Try adjusting your search or filters." : `No ${config.title.toLowerCase()} yet.`}</p>{resource === "members" && auth.permissions.has("invitation.create") && <Link href="/invitations" className="mt-3 inline-block text-sm text-indigo-700 underline">Invite an employee</Link>}</div>
        ) : (
          <DataTable
            rows={response.data.results}
            getRowKey={(r) => r.id}
            columns={[
              ...config.columns.map((c) => ({
                header: c.label,
                cell: (row: Row) =>
                  c.key === "display_name" ? <IdentityDisplay name={String(row.display_name ?? "")} subtitle={String(row.designation ?? row.department ?? "")}/> : c.key === "status" ? (
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
                    {resource === "members" && (auth.permissions.has("branch.update") || auth.permissions.has("team.update")) && <Button variant="ghost" size="sm" onClick={()=>{open("assignment",row);setValues({assignment_kind:auth.permissions.has("branch.update") ? "branches" : "teams",assignment_id:""});}}>Assign location/team</Button>}
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
                  <dt className="text-xs font-medium text-slate-500">{k.replaceAll("_", " ")}</dt>
                  <dd className="break-words text-sm">
                    {Array.isArray(v) ? v.join(", ") : String(v ?? "—")}
                  </dd>
                </div>
              ))}
          </dl>
        ) : (
          <form onSubmit={submit} className="mt-4 space-y-3">
            {mode === "assignment" ? <><label className="block text-sm">Assignment type<select className="mt-1 w-full rounded border p-2" value={values.assignment_kind} onChange={e=>setValues({assignment_kind:e.target.value,assignment_id:""})}>{auth.permissions.has("branch.update") && <option value="branches">Branch</option>}{auth.permissions.has("team.update") && <option value="teams">Team</option>}</select></label><Selection resource={values.assignment_kind === "branches" ? "branches" : "teams"} label="Assignment" required value={values.assignment_id ?? ""} onChange={value=>setValues({...values,assignment_id:value})}/></> : mode === "lifecycle" ? (
              <p>
                This will{" "}
                {config.lifecycle === "invitation"
                  ? "revoke the invitation"
                  : `set this ${config.permission} to ${target}`}
                . The backend enforces lifecycle and owner protections.
              </p>
            ) : mode === "role" ? (
              <Selection resource="roles" label="Role" required value={values.role_id ?? ""} onChange={value=>setValues({role_id:value})}/>
            ) : (
              config.fields.map((f) => (
                <div className="text-sm" key={f.name}>
                  {!["branch_id", "intended_role_id"].includes(f.name) && <label htmlFor={`${resource}-${f.name}`}>{f.label}</label>}
                  {f.name === "branch_id" ? <Selection resource="branches" label="Branch location" value={values.branch_id ?? ""} onChange={value=>setValues({...values,branch_id:value})}/> : f.name === "intended_role_id" ? <Selection resource="roles" label="Intended role" required={f.required} value={values[f.name] ?? ""} onChange={value=>setValues({...values,[f.name]:value})}/> : f.options ? (
                    <select
                      id={`${resource}-${f.name}`}
                      required={f.required}
                      value={values[f.name] ?? ""}
                      onChange={(e) =>
                        setValues({ ...values, [f.name]: e.target.value })
                      }
                      className="mt-1 w-full rounded border p-2"
                    >
                      <option value="">Choose</option>
                      {f.options.map((o) => <option key={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input
                      id={`${resource}-${f.name}`}
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
                </div>
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
            <div className="flex min-w-0 flex-wrap gap-2">
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
