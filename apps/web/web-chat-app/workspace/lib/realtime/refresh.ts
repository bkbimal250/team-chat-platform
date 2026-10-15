import { readSession } from "@/workspace/lib/auth/session";
export const ADMIN_REFRESH = "globalchat:admin-refresh";
export const managedResources = ["members", "invitations", "branches", "teams", "audit-logs", "organizations", "devices", "auth/sessions", "notifications"];
export function refreshAdmin(resources = managedResources) {
 const session = readSession();
 if (session) window.dispatchEvent(new CustomEvent(ADMIN_REFRESH, {detail: {organizationId: session.organization_id, resources}}));
}
export function refreshMatches(path: string, detail: {organizationId?: string; resources?: string[]} | undefined) {
 return !!detail && detail.organizationId === readSession()?.organization_id && !!detail.resources?.some(resource => path.startsWith(`/api/v1/${resource}/`) || path.split("?")[0] === `/api/v1/${resource}`);
}
