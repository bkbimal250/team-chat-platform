import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InvitationsClient, invitationPayload, maskPhone } from "@/features/admin/invitations-client";
import { json, page } from "./fixtures";
const mocks = vi.hoisted(() => ({ permissions: new Set(["invitation.view", "invitation.create", "invitation.revoke"]) }));
vi.mock("@/features/auth/auth-provider", () => ({ useAuth: () => ({ permissions: mocks.permissions }) }));
const pending = { id: "invite-a", recipient_name: "Employee B", recipient_phone: "+919000000003", recipient_email: "employee@example.test", intended_role_id: "role-member", branch_id: "branch-a", team_id: "team-a", status: "PENDING", expires_at: new Date(Date.now() + 86400000).toISOString() };
beforeEach(() => { mocks.permissions = new Set(["invitation.view", "invitation.create", "invitation.revoke"]); });
function repository() {
  let row = pending;
  return vi.fn().mockImplementation(async (url: string, init: RequestInit) => {
    if (url.includes("/roles/")) return json(page([{ id: "role-member", name: "Staff", kind: "MEMBER", permissions: [] }]));
    if (url.includes("/branches/")) return json(page([{ id: "branch-a", name: "Local Branch", status: "ACTIVE" }]));
    if (url.includes("/teams/")) return json(page([{ id: "team-a", name: "Local Team", status: "ACTIVE" }]));
    if (init.method === "POST") {
      if (url.includes("/revoke/")) { row = { ...row, status: "REVOKED" }; return json(row); }
      return json({ ...row, development_url: "http://localhost:3001/join#invite=" + "a".repeat(43) }, 201);
    }
    return json(page([row]));
  });
}
it("creates a phone-bound invitation with real selected role/branch/team IDs", async () => {
  const fetch = repository(); vi.stubGlobal("fetch", fetch); render(<InvitationsClient />); const user = userEvent.setup({delay:null});
  await screen.findByText("Employee B");
  await user.click(screen.getByRole("button", { name: "Invite Member" }));
  await user.type(screen.getByRole("textbox", { name: "Name" }), "Employee B");
  await user.type(screen.getByRole("textbox", { name: "Phone Number (optional)" }), "+919000000003");
  await user.selectOptions(await screen.findByRole("combobox", { name: "Role" }), "role-member");
  await user.selectOptions(screen.getByRole("combobox", { name: "Branch" }), "branch-a");
  await user.selectOptions(screen.getByRole("combobox", { name: "Team" }), "team-a");
  await user.type(screen.getByRole("textbox", { name: "Email" }), "employee@example.test");
  await user.click(screen.getByRole("button", { name: "Create invitation" }));
  expect(await screen.findByRole("textbox", { name: "Development invitation link" })).toBeTruthy();
  const call = fetch.mock.calls.find((call) => call[1].method === "POST");
  expect(JSON.parse(String(call![1].body))).toEqual({ recipient_name: "Employee B", recipient_phone: "+919000000003", recipient_email: "employee@example.test", intended_role_id: "role-member", branch_id: "branch-a", team_id: "team-a" });
  expect(sessionStorage.length).toBe(0);
});
it("resends through the real endpoint without making a second invitation", async () => {
  const fetch = repository(); vi.stubGlobal("fetch", fetch); render(<InvitationsClient />); const user = userEvent.setup({delay:null});
  await user.click(await screen.findByRole("button", { name: "Regenerate link" }));
  expect(await screen.findByRole("textbox", { name: "Development invitation link" })).toBeTruthy();
  expect(fetch.mock.calls.filter((call) => call[1].method === "POST").map((call) => call[0])).toEqual(["/api/gateway/api/v1/invitations/invite-a/resend/"]);
});
it("requires revoke confirmation and refreshes the server status", async () => {
  const fetch = repository(); vi.stubGlobal("fetch", fetch); render(<InvitationsClient />); const user = userEvent.setup({delay:null});
  await user.click(await screen.findByRole("button", { name: "Revoke" }));
  expect(fetch.mock.calls.filter((call) => call[1].method === "POST")).toHaveLength(0);
  await user.click(screen.getByRole("button", { name: "Confirm revoke" }));
  expect(await screen.findByRole("cell", { name: "REVOKED" })).toBeTruthy(); expect(screen.queryByRole("button", { name: "Regenerate link" })).toBeNull();
});
it("does not expose invite actions to a normal member", async () => {
  mocks.permissions = new Set(["invitation.view"]); vi.stubGlobal("fetch", repository()); render(<InvitationsClient />);
  await screen.findByText("Employee B");
  expect(screen.queryByRole("button", { name: "Invite Member" })).toBeNull(); expect(screen.queryByRole("button", { name: "Regenerate link" })).toBeNull(); expect(screen.queryByRole("button", { name: "Revoke" })).toBeNull();
});
it("surfaces backend conflicts without invented success", async () => {
  const fetch = repository(); fetch.mockImplementationOnce(async () => json({ error: { code: "INVITATION_PENDING", message: "An invitation is already pending." } }, 409)); vi.stubGlobal("fetch", fetch); render(<InvitationsClient />);
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("already pending"));
});
it("validates recipient input and masks full phones", () => {
  expect(() => invitationPayload({ recipient_name: "", recipient_phone: "123", recipient_email: "", intended_role_id: "", branch_id: "", team_id: "" })).toThrow();
  expect(maskPhone(pending.recipient_phone)).not.toContain(pending.recipient_phone);
});

it("honestly omits unsupported email-only regeneration",async()=>{const fetch=repository();fetch.mockImplementationOnce(async()=>json(page([{...pending,recipient_phone:""}])));vi.stubGlobal("fetch",fetch);render(<InvitationsClient/>);await screen.findByText("Email-only link regeneration unavailable");expect(screen.queryByRole("button",{name:"Regenerate link"})).toBeNull();});
