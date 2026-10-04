"use client";

import Link from "next/link";

import { useCallback, useEffect, useState } from "react";

import type { Organization } from "@/lib/api/contracts";

import { listOrganizations, updateOrganization } from "../repository";

import { useAuth } from "@/features/auth/auth-provider";

import { DataTable } from "@/components/data-table/data-table";

import { StatusBadge } from "@/components/ui/status-badge";

import { Button } from "@/components/ui/button";

import { Card } from "@/components/ui/card";

import { Modal } from "@/components/ui/modal";

import { ErrorState } from "@/components/feedback/error-state";

export function OrganizationsClient() {
  const [rows, setRows] = useState<Organization[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [editing, setEditing] = useState(false),
    [busy, setBusy] = useState(false),
    [form, setForm] = useState({
      name: "",
      display_name: "",
      slug: "",
      timezone: "",
      country_code: "",
    });
  const auth = useAuth();

  const reload = useCallback(async () => {
    try {
      setRows(await listOrganizations());
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load organization.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    listOrganizations()
      .then((rows) => {
        if (active) {
          setRows(rows);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (active) {
          setError(
            e instanceof Error ? e.message : "Could not load organization.",
          );
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await updateOrganization(form);
      setEditing(false);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Organizations</h1>
        <p className="text-sm text-slate-500">
          This session can access only its current organization. Platform-wide
          listing, creation and billing plans are unavailable.
        </p>
      </header>
      <Card className="p-4">
        <Button variant="outline" onClick={() => void reload()}>
          Refresh
        </Button>
        {loading ? (
          <p role="status" className="p-8">
            Loading organization…
          </p>
        ) : error && !editing ? (
          <ErrorState description={error} retry={() => void reload()} />
        ) : (
          <DataTable
            rows={rows}
            getRowKey={(r) => r.id}
            columns={[
              {
                header: "Organization",
                cell: (r) => (
                  <Link
                    className="text-indigo-700 underline"
                    href={`/organizations/${r.id}`}
                  >
                    {r.display_name || r.name}
                  </Link>
                ),
              },
              { header: "Slug", cell: (r) => r.slug },
              {
                header: "Status",
                cell: (r) => <StatusBadge status={r.status} />,
              },
              {
                header: "Actions",
                cell: (r) => (
                  <div className="flex gap-2">
                    <Link href={`/organizations/${r.id}`}>View</Link>
                    {auth.permissions.has("organization.update") && (
                      <Button
                        variant="ghost"
                        onClick={() => {
                          setForm({
                            name: r.name,
                            display_name: r.display_name,
                            slug: r.slug,
                            timezone: r.timezone,
                            country_code: r.country_code,
                          });
                          setEditing(true);
                          setError("");
                        }}
                      >
                        Edit
                      </Button>
                    )}
                    <Link href="/settings">Settings</Link>
                  </div>
                ),
              },
            ]}
          />
        )}
      </Card>
      <Modal
        open={editing}
        title="Edit current organization"
        onClose={() => {
          if (!busy) setEditing(false);
        }}
      >
        <form onSubmit={submit} className="mt-4 space-y-3">
          {Object.entries(form).map(([key, value]) => (
            <label key={key} className="block text-sm">
              {key.replaceAll("_", " ")}
              <input
                required={key !== "country_code"}
                maxLength={
                  key === "slug"
                    ? 100
                    : key === "timezone"
                      ? 64
                      : key === "country_code"
                        ? 2
                        : 200
                }
                pattern={key === "slug" ? "[-a-zA-Z0-9_]+" : undefined}
                value={value}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="mt-1 w-full rounded border p-2"
              />
            </label>
          ))}
          {error && (
            <p role="alert" className="text-rose-700">
              {error}
            </p>
          )}
          <Button disabled={busy} type="submit">
            {busy ? "Saving…" : "Save"}
          </Button>
          <Button
            variant="outline"
            type="button"
            disabled={busy}
            onClick={() => setEditing(false)}
          >
            Cancel
          </Button>
        </form>
      </Modal>
    </section>
  );
}
