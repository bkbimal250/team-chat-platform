"use client";
import { useCallback, useEffect, useState } from "react";
import { deviceApi, LinkedDevice } from "./api";
import { QRScanner } from "./qr-scanner";
import { LogOut, QrCode, Smartphone } from "lucide-react";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { SectionGroup } from "@/components/workspace/section-group";
import { ActionToolbar } from "@/components/workspace/action-toolbar";
import { EmptyState } from "@/components/ui/empty-state";
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
    <DetailScaffold
      width="narrow"
      title="Linked devices"
      subtitle="Manage devices connected to your GlobalChat account."
    >
      <ActionToolbar className="mb-4 border-0 pt-0">
        <IconButton label="Link a device" onClick={() => setScanner(true)} className="text-aurora-primary">
          <QrCode className={iconSize} />
        </IconButton>
        <IconButton
          label="Log out other devices"
          disabled={!devices.some((d) => !d.is_current && d.status !== "REVOKED")}
          onClick={() => setConfirm("others")}
          className="text-aurora-muted"
        >
          <LogOut className={iconSize} />
        </IconButton>
      </ActionToolbar>
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
        <SectionGroup key={String(current)} title={current ? "This device" : "Other devices"}>
          <ul className="divide-y divide-aurora-border">
            {devices
              .filter((d) => d.is_current === current)
              .map((device) => (
                <li
                  key={device.id}
                  className="flex flex-wrap items-center justify-between gap-3 py-3"
                >
                  <div className="min-w-0">
                    <h3 className="font-semibold">{device.device_name}</h3>
                    <p className="text-sm text-aurora-muted">
                      {device.platform}
                      {device.device_model ? ` · ${device.device_model}` : ""} · {device.status}
                    </p>
                    <p className="mt-1 text-xs text-aurora-muted">
                      Linked {new Date(device.first_seen_at).toLocaleString()} · Last active{" "}
                      {new Date(device.last_seen_at).toLocaleString()}
                    </p>
                  </div>
                  <IconButton
                    label="Log out device"
                    disabled={device.status === "REVOKED"}
                    onClick={() => setConfirm(device)}
                    className="text-rose-600"
                  >
                    <LogOut className={iconSize} />
                  </IconButton>
                </li>
              ))}
          </ul>
        </SectionGroup>
      ))}
      {!loading && devices.length === 0 && (
        <EmptyState icon={Smartphone} title="No linked devices" detail="Link a device with QR to sign in on another screen." />
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
    </DetailScaffold>
  );
}
