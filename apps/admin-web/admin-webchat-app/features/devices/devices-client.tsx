"use client";

import { useState } from "react";

import { apiRequest } from "@/lib/api/client";

import { useResource } from "@/lib/api/use-resource";

import type { Device, IdentitySession } from "@/lib/api/contracts";

import { clearSession } from "@/lib/auth/session";

import { DataTable } from "@/components/data-table/data-table";

import { Button } from "@/components/ui/button";

import { Card } from "@/components/ui/card";

import { Modal } from "@/components/ui/modal";

import { ErrorState } from "@/components/feedback/error-state";

import { TableEmpty } from "@/components/data-table/table-empty";

export function DevicesClient() {
  const devices = useResource<Device[]>("/api/v1/devices"),
    sessions = useResource<IdentitySession[]>("/api/v1/auth/sessions");
  const [selected, setSelected] = useState<{
      kind: "devices" | "sessions";
      id: string;
      current: boolean;
    } | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");

  async function revoke() {
    if (!selected || busy) return;
    setBusy(true);
    setError("");
    try {
      await apiRequest(
        selected.kind === "devices"
          ? `/api/v1/devices/${selected.id}/revoke`
          : `/api/v1/auth/sessions/${selected.id}/revoke`,
        { method: "POST", body: "{}" },
      );
      if (selected.current) clearSession();
      setSelected(null);
      devices.reload();
      sessions.reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Revocation failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">Your devices and sessions</h1>
      <p className="text-sm text-slate-500">
        Only your own account is exposed by Identity. Organization-wide device
        administration is unavailable.
      </p>
      {error && (
        <p role="alert" className="text-rose-700">
          {error}
        </p>
      )}
      <Card className="p-5">
        <h2 className="mb-3 font-semibold">Linked devices</h2>
        {devices.loading ? (
          <p role="status">Loading…</p>
        ) : devices.error ? (
          <ErrorState description={devices.error} retry={devices.reload} />
        ) : !devices.data?.length ? (
          <TableEmpty />
        ) : (
          <DataTable
            rows={devices.data}
            getRowKey={(r) => r.id}
            columns={[
              { header: "Device", cell: (r) => r.device_name },
              { header: "Platform", cell: (r) => r.platform },
              { header: "Status", cell: (r) => r.status },
              {
                header: "Actions",
                cell: (r) => (
                  <Button
                    variant="outline"
                    disabled={r.status !== "ACTIVE"}
                    onClick={() =>
                      setSelected({
                        kind: "devices",
                        id: r.id,
                        current: r.is_current,
                      })
                    }
                  >
                    Revoke{r.is_current ? " current" : ""}
                  </Button>
                ),
              },
            ]}
          />
        )}
      </Card>
      <Card className="p-5">
        <h2 className="mb-3 font-semibold">Your sessions</h2>
        {sessions.loading ? (
          <p role="status">Loading…</p>
        ) : sessions.error ? (
          <ErrorState description={sessions.error} retry={sessions.reload} />
        ) : !sessions.data?.length ? (
          <TableEmpty />
        ) : (
          <DataTable
            rows={sessions.data}
            getRowKey={(r) => r.id}
            columns={[
              { header: "Device", cell: (r) => r.device_name },
              { header: "Status", cell: (r) => r.status },
              {
                header: "Last activity",
                cell: (r) => new Date(r.last_activity_at).toLocaleString(),
              },
              {
                header: "Actions",
                cell: (r) => (
                  <Button
                    variant="outline"
                    disabled={r.status !== "ACTIVE"}
                    onClick={() =>
                      setSelected({
                        kind: "sessions",
                        id: r.id,
                        current: r.is_current,
                      })
                    }
                  >
                    Revoke{r.is_current ? " current" : ""}
                  </Button>
                ),
              },
            ]}
          />
        )}
      </Card>
      <Modal
        open={!!selected}
        title="Confirm revocation"
        onClose={() => {
          if (!busy) setSelected(null);
        }}
      >
        <p className="my-4">
          This invalidates the selected {selected?.kind}. Revoking the current
          device/session signs you out.
        </p>
        <Button variant="danger" disabled={busy} onClick={() => void revoke()}>
          Confirm revoke
        </Button>
        <Button
          variant="outline"
          disabled={busy}
          onClick={() => setSelected(null)}
        >
          Cancel
        </Button>
      </Modal>
    </section>
  );
}
