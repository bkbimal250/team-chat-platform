"use client";

import { Pencil, Shield, Trash2, UserCog, Users } from "lucide-react";
import { useAuth } from "@/workspace/features/auth/auth-provider";
import { configs } from "@/workspace/features/admin/resource-config";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { EmptyState } from "@/components/ui/empty-state";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { Section } from "@/components/content/section";
import { DetailRow } from "@/components/content/detail-row";
import { humanStatus } from "@/components/content/format";
import { StatusPill } from "@/components/workspace/status-pill";
import { ActionToolbar } from "@/components/workspace/action-toolbar";
import type { ResourceRemoteAction } from "@/workspace/features/admin/resource-screen";
import type { WorkspaceRow } from "./workspace-list-panel";

function fmt(value: unknown) {
  if (Array.isArray(value)) return value.join(", ") || "—";
  return String(value ?? "—");
}

export function WorkspaceDetailPane({
  resource,
  selected,
  onAction,
}: {
  resource: string;
  selected: WorkspaceRow | null;
  onAction: (action: ResourceRemoteAction) => void;
}) {
  const config = configs[resource];
  const auth = useAuth();
  const can = (action: string) => auth.permissions.has(`${config.permission}.${action}`);

  if (!selected) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <EmptyState
          icon={Users}
          title={`Select ${config.title.toLowerCase()}`}
          detail={`Choose an entry from the list to view details.`}
        />
      </div>
    );
  }

  const title = String(
    selected.display_name ?? selected.name ?? selected.recipient_name ?? selected.id,
  );
  const status = String(selected.status ?? "");
  const roles = Array.isArray(selected.roles) ? selected.roles : [];

  return (
    <DetailScaffold
      width="medium"
      title={title}
      subtitle={resource === "members" ? String(selected.designation ?? selected.department ?? "") : config.title}
      avatarName={title}
      actions={
        <>
          {config.edit && can("update") && (
            <IconButton label="Edit" onClick={() => onAction({ mode: "edit", row: selected })}>
              <Pencil className={iconSize} />
            </IconButton>
          )}
          {resource === "members" && auth.permissions.has("role.manage") && (
            <IconButton label="Assign role" onClick={() => onAction({ mode: "role", row: selected })}>
              <Shield className={iconSize} />
            </IconButton>
          )}
          {resource === "members" &&
            (auth.permissions.has("branch.update") || auth.permissions.has("team.update")) && (
              <IconButton label="Assign branch or team" onClick={() => onAction({ mode: "assignment", row: selected })}>
                <UserCog className={iconSize} />
              </IconButton>
            )}
        </>
      }
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {status && (
          <StatusPill tone={status === "ACTIVE" ? "success" : status === "SUSPENDED" ? "warning" : "neutral"}>
            {humanStatus(status)}
          </StatusPill>
        )}
        {roles.map((r) => (
          <StatusPill key={r}>{humanStatus(r)}</StatusPill>
        ))}
      </div>

      {resource === "members" && (
        <>
          <Section title="Profile">
            <dl>
              <DetailRow label="Employee code" value={fmt(selected.employee_code)} />
              <DetailRow label="Department" value={fmt(selected.department)} />
              <DetailRow label="Designation" value={fmt(selected.designation)} />
              <DetailRow label="Phone" value={fmt(selected.recipient_phone_masked)} />
            </dl>
          </Section>
          <Section title="Assignments">
            <dl>
              <DetailRow label="Branches" value={fmt(selected.branches)} />
              <DetailRow label="Teams" value={fmt(selected.teams)} />
            </dl>
          </Section>
        </>
      )}

      {resource === "invitations" && (
        <Section title="Recipient">
          <dl>
            <DetailRow label="Name" value={fmt(selected.recipient_name)} />
            <DetailRow label="Email" value={fmt(selected.recipient_email)} />
            <DetailRow label="Expires" value={fmt(selected.expires_at)} />
          </dl>
        </Section>
      )}

      {resource !== "members" && resource !== "invitations" && (
        <Section title="Details">
          <dl>
            {config.columns.map((col) => (
              <DetailRow
                key={col.key}
                label={col.label}
                value={col.key === "status" ? humanStatus(fmt(selected[col.key])) : fmt(selected[col.key])}
              />
            ))}
          </dl>
        </Section>
      )}

      {resource === "invitations" && (
        <Section title="Invitation">
          <dl>
            {config.columns.map((col) => (
              <DetailRow
                key={col.key}
                label={col.label}
                value={col.key === "status" ? humanStatus(fmt(selected[col.key])) : fmt(selected[col.key])}
              />
            ))}
          </dl>
        </Section>
      )}

      <ActionToolbar>
        {config.lifecycle === "member" && can("update") && status === "ACTIVE" && (
          <IconButton label="Suspend member" className="text-amber-700" onClick={() => onAction({ mode: "lifecycle", row: selected, target: "SUSPENDED" })}>
            <UserCog className={iconSize} />
          </IconButton>
        )}
        {config.lifecycle === "member" && can("update") && status === "SUSPENDED" && (
          <IconButton label="Activate member" onClick={() => onAction({ mode: "lifecycle", row: selected, target: "ACTIVE" })}>
            <UserCog className={iconSize} />
          </IconButton>
        )}
        {config.lifecycle === "member" && can("remove") && ["ACTIVE", "INVITED", "SUSPENDED"].includes(status) && (
          <IconButton label="Remove member" className="text-rose-600" onClick={() => onAction({ mode: "lifecycle", row: selected, target: "REMOVED" })}>
            <Trash2 className={iconSize} />
          </IconButton>
        )}
        {config.lifecycle === "resource" && can("update") && ["ACTIVE", "DISABLED"].includes(status) && (
          <IconButton
            label={status === "ACTIVE" ? "Disable" : "Activate"}
            onClick={() => onAction({ mode: "lifecycle", row: selected, target: status === "ACTIVE" ? "DISABLED" : "ACTIVE" })}
          >
            <UserCog className={iconSize} />
          </IconButton>
        )}
        {config.lifecycle === "invitation" && can("revoke") && status === "PENDING" && (
          <IconButton label="Revoke invitation" className="text-rose-600" onClick={() => onAction({ mode: "lifecycle", row: selected })}>
            <Trash2 className={iconSize} />
          </IconButton>
        )}
      </ActionToolbar>
    </DetailScaffold>
  );
}
