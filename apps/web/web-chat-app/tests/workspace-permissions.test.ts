import { expect, it } from "vitest";
import { workspaceCapabilities } from "@/lib/auth/workspace-permissions";
it("derives management from actual capabilities, never a role label", () => {
 const member = workspaceCapabilities(new Set(["member.view", "team.view"]));
 expect(member.canViewMembers).toBe(true);
 expect(member.canManageMembers).toBe(false);
 expect(member.canInviteMembers).toBe(false);
 for (const owner of ["first", "second"]) {
   void owner;
   expect(workspaceCapabilities(new Set(["member.update", "invitation.create"])).canInviteMembers).toBe(true);
 }
});
