import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider } from "@/features/auth/auth-provider";
import { AdminGuard } from "@/features/auth/admin-guard";
import { memberPermissions, canUseAdmin } from "@/features/auth/permissions";
import { saveSession } from "@/lib/auth/session";
import { tokens, json, page } from "./fixtures";
const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
export function adminFetch(
  permissions = [
    "organization.update",
    "organization.view",
    "branch.view",
    "branch.create",
    "branch.update",
    "member.view",
    "team.view",
    "audit.view",
    "role.view",
  ],
) {
  return vi.fn(async (url: string) => {
    if (url.includes("role-assignments"))
      return json(
        page([{ id: "assignment", member: "member-a", role: "role-a" }]),
      );
    if (url.includes("/roles/"))
      return json(
        page([{ id: "role-a", name: "Owner", kind: "OWNER", permissions }]),
      );
    if (url.includes("/users/me"))
      return json({
        user_id: "user-a",
        display_name: "Alice",
        status: "ACTIVE",
      });
    return json({ identity: {}, session: {}, context: {} });
  });
}
describe("admin authorization", () => {
  it("uses only roles assigned to the current member", () => {
    const value = memberPermissions(
      "a",
      [
        {
          id: "owner",
          name: "Owner",
          kind: "OWNER",
          permissions: ["organization.update"],
        },
        {
          id: "member",
          name: "Member",
          kind: "MEMBER",
          permissions: ["organization.view"],
        },
      ],
      [
        { id: "1", member: "other", role: "owner" },
        { id: "2", member: "a", role: "member" },
      ],
    );
    expect(canUseAdmin(value)).toBe(false);
  });
  it("does not render admin routes without a session", async () => {
    replace.mockClear();
    render(
      <AuthProvider>
        <AdminGuard>
          <p>Protected data</p>
        </AdminGuard>
      </AuthProvider>,
    );
    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"));
    expect(screen.queryByText("Protected data")).toBeNull();
  });
  it("rejects normal read-only members", async () => {
    saveSession(tokens);
    vi.stubGlobal(
      "fetch",
      adminFetch(["organization.view", "member.view", "role.view"]),
    );
    render(
      <AuthProvider>
        <AdminGuard>
          <p>Protected data</p>
        </AdminGuard>
      </AuthProvider>,
    );
    expect(
      await screen.findByText("Organization admin access required"),
    ).toBeTruthy();
    expect(screen.queryByText("Protected data")).toBeNull();
  });
  it("allows a verified organization administrator", async () => {
    saveSession(tokens);
    vi.stubGlobal("fetch", adminFetch());
    render(
      <AuthProvider>
        <AdminGuard>
          <p>Protected data</p>
        </AdminGuard>
      </AuthProvider>,
    );
    expect(await screen.findByText("Protected data")).toBeTruthy();
  });
  it("fails closed if role lookup cannot be authorized", async () => {
    saveSession(tokens);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(json({ detail: "Forbidden" }, 403)),
    );
    render(
      <AuthProvider>
        <AdminGuard>
          <p>Protected data</p>
        </AdminGuard>
      </AuthProvider>,
    );
    expect(
      await screen.findByText("Session validation unavailable"),
    ).toBeTruthy();
    expect(screen.queryByText("Protected data")).toBeNull();
  });
});
