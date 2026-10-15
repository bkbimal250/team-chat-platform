/** Capabilities returned by Organization roles; never infer them from role names. */
export function workspaceCapabilities(permissions: ReadonlySet<string>) {
  return {
    canViewMembers: permissions.has("member.view"),
    canManageMembers: permissions.has("member.update"),
    canInviteMembers: permissions.has("invitation.create"),
    canViewTeams: permissions.has("team.view"),
    canManageTeams: permissions.has("team.update"),
    canViewBranches: permissions.has("branch.view"),
    canManageBranches: permissions.has("branch.update"),
    canManageCompany: permissions.has("organization.update"),
    canManageRoles: permissions.has("role.manage"),
  };
}
