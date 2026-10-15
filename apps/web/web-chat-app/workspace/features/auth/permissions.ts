import type { Role, RoleAssignment } from "@/workspace/lib/api/contracts";
export function memberPermissions(
  memberId: string,
  roles: Role[],
  assignments: RoleAssignment[],
): Set<string> {
  const assigned = new Set(
    assignments.filter((a) => a.member === memberId).map((a) => a.role),
  );
  return new Set(
    roles.filter((r) => assigned.has(r.id)).flatMap((r) => r.permissions),
  );
}
