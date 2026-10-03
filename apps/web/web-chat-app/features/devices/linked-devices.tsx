"use client";
import { useCallback, useEffect, useState } from "react";
import { deviceApi, LinkedDevice } from "./api";
import { QRScanner } from "./qr-scanner";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
export function LinkedDevices({
  token,
  onSignedOut,
}: {
  token: string;
  onSignedOut: () => void;
}) {
  const [devices, setDevices] = useState<LinkedDevice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [scanner, setScanner] = useState(false);
  const [confirm, setConfirm] = useState<LinkedDevice | "others" | null>(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const load = useCallback(async () => {
    try {
      const result = await deviceApi.list(token);
      setDevices(result);
    } catch (issue) {
      setError(
        issue instanceof Error ? issue.message : "Unable to load devices.",
      );
    } finally {
      setLoading(false);
    }
  }, [token]);
  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);
  async function revoke() {
    if (!confirm || busy) return;
    setBusy(true);
    try {
      const rows =
        confirm === "others"
          ? devices.filter((d) => !d.is_current && d.status !== "REVOKED")
          : [confirm];
      for (const device of rows) await deviceApi.revoke(device.id, token);
      if (rows.some((d) => d.is_current)) {
        onSignedOut();
        return;
      }
      setConfirm(null);
      setToast("Selected devices signed out.");
      await load();
    } catch (issue) {
      setError(
        issue instanceof Error
          ? issue.message
          : "Revocation failed. Refresh to check device status.",
      );
      setConfirm(null);
      await load();
    } finally {
      setBusy(false);
    }
  }
  if (scanner)
    return (
      <QRScanner
        token={token}
        onCancel={() => setScanner(false)}
        onSuccess={() => {
          setScanner(false);
          setToast("Device approved. Complete sign-in on the new device.");
          void load();
        }}
      />
    );
  return (
    <section className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-cyan-700">
          Account security
        </p>
        <h1 className="mt-2 text-3xl font-semibold">Linked devices</h1>
        <p className="mt-2 text-sm text-slate-500">
          Manage devices connected to your GlobalChat account.
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setScanner(true)}
          className="rounded-xl bg-cyan-800 px-4 py-3 text-sm font-semibold text-white"
        >
          Link a device
        </button>
        <button
          disabled={
            !devices.some((d) => !d.is_current && d.status !== "REVOKED")
          }
          onClick={() => setConfirm("others")}
          className="rounded-xl border px-4 py-3 text-sm disabled:opacity-40"
        >
          Log out other devices
        </button>
      </div>
      {toast && (
        <p
          role="status"
          className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800"
        >
          {toast}
        </p>
      )}
      {error && (
        <div
          role="alert"
          className="rounded-xl bg-rose-50 p-4 text-sm text-rose-800"
        >
          {error}
          <button onClick={() => void load()} className="ml-4 underline">
            Retry
          </button>
        </div>
      )}
      {loading && (
        <div className="h-36 animate-pulse rounded-2xl bg-slate-200" />
      )}
      {[true, false].map((current) => (
        <div key={String(current)}>
          <h2 className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-500">
            {current ? "This device" : "Other devices"}
          </h2>
          <div className="space-y-3">
            {devices
              .filter((d) => d.is_current === current)
              .map((device) => (
                <article
                  key={device.id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5"
                >
                  <div>
                    <h3 className="font-semibold">{device.device_name}</h3>
                    <p className="text-sm text-slate-500">
                      {device.platform}
                      {device.device_model
                        ? ` · ${device.device_model}`
                        : ""} · {device.status}
                    </p>
                    <p className="mt-2 text-xs text-slate-500">
                      Linked {new Date(device.first_seen_at).toLocaleString()}
                      <br />
                      Last active{" "}
                      {new Date(device.last_seen_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    disabled={device.status === "REVOKED"}
                    onClick={() => setConfirm(device)}
                    className="rounded-xl border px-4 py-2 text-sm text-rose-700 disabled:opacity-40"
                  >
                    Log out device
                  </button>
                </article>
              ))}
          </div>
        </div>
      ))}
      {!loading && devices.length === 0 && (
        <p className="text-sm text-slate-500">No linked devices found.</p>
      )}
      {confirm && (
        <ConfirmDialog
          title="Log out device?"
          busy={busy}
          onCancel={() => setConfirm(null)}
          onConfirm={() => void revoke()}
        >
          This revokes the selected device’s sessions.{" "}
          {confirm !== "others" && confirm.is_current
            ? "You will also be signed out here."
            : "It will need to authenticate again."}
        </ConfirmDialog>
      )}
    </section>
  );
}
