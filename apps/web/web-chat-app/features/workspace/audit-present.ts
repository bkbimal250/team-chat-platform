import type { LucideIcon } from "lucide-react";
import { GitBranch, Mail, Shield, UserMinus, UserPlus, Users, UsersRound } from "lucide-react";

const ACTION_PHRASES: Record<string, string> = {
  MEMBER_REMOVED: "Member removed",
  MEMBER_CREATED: "Member added",
  MEMBER_UPDATED: "Member updated",
  MEMBER_SUSPENDED: "Member suspended",
  MEMBER_ACTIVATED: "Member activated",
  INVITATION_CREATED: "Invitation sent",
  INVITATION_REVOKED: "Invitation revoked",
  TEAM_CREATED: "Team created",
  TEAM_UPDATED: "Team updated",
  BRANCH_CREATED: "Branch created",
  BRANCH_UPDATED: "Branch updated",
  ROLE_ASSIGNED: "Role assigned",
};

const RESOURCE_LABELS: Record<string, string> = {
  member: "member",
  invitation: "invitation",
  team: "team",
  branch: "branch",
  role: "role",
  organization: "organization",
};

export function formatAuditEvent(action: string, resourceType: string) {
  const phrase =
    ACTION_PHRASES[action] ??
    action
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/^\w/, (c) => c.toUpperCase());
  const resource = RESOURCE_LABELS[resourceType] ?? resourceType.replaceAll("_", " ");
  if (phrase.toLowerCase().includes(resource.toLowerCase())) return phrase;
  return `${phrase} · ${resource}`;
}

export function auditIcon(resourceType: string): LucideIcon {
  switch (resourceType) {
    case "team":
      return UsersRound;
    case "branch":
      return GitBranch;
    case "invitation":
      return Mail;
    case "role":
      return Shield;
    case "member":
      if (resourceType.includes("remove")) return UserMinus;
      return UserPlus;
    default:
      return Users;
  }
}

export function auditIconForAction(action: string, resourceType: string): LucideIcon {
  if (action.includes("REMOVED")) return UserMinus;
  if (action.includes("CREATED") || action.includes("ACTIVATED")) return UserPlus;
  return auditIcon(resourceType);
}
