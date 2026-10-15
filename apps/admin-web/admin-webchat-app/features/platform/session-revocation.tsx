"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { ApiError, apiRequest } from "@/lib/api/client";

export type RevocableSession = { id: string; status: string };

export function SessionRevocationButton({
  identityId,
  session,
  revokeAll = false,
  onComplete,
}: {
  identityId: string;
  session?: RevocableSession;
  revokeAll?: boolean;
  onComplete: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const active = revokeAll || session?.status === "ACTIVE";
  const action = revokeAll ? "Revoke all sessions" : "Revoke session";

  async function revoke() {
    setBusy(true);
    setError("");
    try {
      await apiRequest(
        revokeAll
          ? `/api/v1/platform/identities/${identityId}/sessions/revoke`
          : `/api/v1/platform/sessions/${session?.id}/revoke`,
        { method: "POST", body: "{}" },
      );
      setOpen(false);
      setNotice(revokeAll ? "Sessions revoked." : "Session revoked.");
      onComplete();
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Identity service temporarily unavailable. Please retry.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (!active) return null;
  return (
    <>
      <Button
        type="button"
        variant="danger"
        size="sm"
        disabled={busy}
        onClick={() => {
          setError("");
          setOpen(true);
        }}
      >
        {action}
      </Button>
      {notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}
      <Modal
        open={open}
        title={action}
        onClose={() => {
          if (!busy) setOpen(false);
        }}
      >
        <p className="mt-4 text-sm text-slate-700">
          {revokeAll
            ? "All active sessions for this account will have their refresh credentials invalidated."
            : "This session’s refresh credentials will be invalidated."}
        </p>
        <p className="mt-2 text-sm text-slate-500">
          Existing access tokens are stateless and can remain valid until their short expiry.
        </p>
        {error && <p role="alert" className="mt-3 text-sm text-rose-700">{error}</p>}
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="outline" disabled={busy} onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button type="button" variant="danger" disabled={busy} onClick={() => void revoke()}>
            {busy ? "Revoking…" : action}
          </Button>
        </div>
      </Modal>
    </>
  );
}
