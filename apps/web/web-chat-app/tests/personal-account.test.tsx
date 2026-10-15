import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "@/workspace/features/auth/auth-provider";
import { PasswordAuth } from "@/workspace/features/auth/password-auth";
import { WorkspaceFrame } from "@/workspace/shell";
import { saveSession } from "@/lib/auth/session";

const navigation = vi.hoisted(() => ({ replace: vi.fn(), push: vi.fn(), path: "/" }));
vi.mock("next/navigation", () => ({ useRouter: () => navigation, usePathname: () => navigation.path }));
const tokens = {
  access_token: `header.${btoa(JSON.stringify({ sub: "personal", sid: "session", did: "device" }))}.signature`,
  refresh_token: "test-refresh", organization_id: null, member_id: null,
};
function respond(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } });
}
function Probe() { const auth = useAuth(); return <p>{auth.status}:{auth.permissions.size}:{auth.profile?.display_name}</p>; }

it("registers a personal account without company fields through Gateway", async () => {
  const fetch = vi.fn(async (url: string) => respond(url.includes("registration/personal") ? tokens : url.includes("auth/me") ? { context: { organization_id: null, member_id: null } } : { display_name: "Personal User" }));
  vi.stubGlobal("fetch", fetch);
  render(<AuthProvider><PasswordAuth registration /></AuthProvider>);
  expect(screen.queryByLabelText("Company name")).toBeNull();
  const user = userEvent.setup({ delay: null });
  await user.click(screen.getByLabelText("Your name")); await user.paste("Personal User");
  await user.click(screen.getByLabelText("Email")); await user.paste("person@example.test");
  await user.click(screen.getByLabelText("Phone number")); await user.paste("9876543210");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  await user.click(screen.getByLabelText("Password")); await user.paste("Secure personal password!");
  await user.click(screen.getByLabelText("Confirm password")); await user.paste("Secure personal password!");
  await user.click(screen.getByRole("button", { name: "Create account" }));
  await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith("/"));
  const request = fetch.mock.calls.find(([url]) => url.includes("registration/personal"));
  expect(request).toBeTruthy();
  // Inspect the real browser request rather than calling the controller directly.
  const call = (fetch.mock.calls as unknown as [string, RequestInit][]).find(([url]) => url.includes("registration/personal"))!;
  const payload = JSON.parse(String(call[1].body));
  expect(payload.display_name).toBe("Personal User");
  expect(payload.phone).toBe("+919876543210");
  expect(payload).not.toHaveProperty("company_name");
  expect(payload).not.toHaveProperty("organization_id");
});

it("loads personal profile without querying tenant roles or permissions", async () => {
  saveSession(tokens);
  const fetch = vi.fn(async (url: string) => respond(url.includes("auth/me") ? { context: { organization_id: null, member_id: null } } : { display_name: "Personal User" }));
  vi.stubGlobal("fetch", fetch);
  render(<AuthProvider><Probe /></AuthProvider>);
  expect(await screen.findByText("ready:0:Personal User")).toBeTruthy();
  expect(fetch.mock.calls.map(([url]) => url)).toEqual(["/api/gateway/api/v1/auth/me", "/api/gateway/api/v1/users/me"]);
});

it("keeps a personal account out of company resource screens", async () => {
  navigation.path = "/workspace/members";
  saveSession(tokens);
  const fetch = vi.fn(async (url: string) => respond(url.includes("auth/me") ? { context: { organization_id: null, member_id: null } } : { display_name: "Personal User" }));
  vi.stubGlobal("fetch", fetch);
  render(<AuthProvider><WorkspaceFrame><p>Tenant member data</p></WorkspaceFrame></AuthProvider>);
  expect(await screen.findByText("Company membership required")).toBeTruthy();
  expect(screen.queryByText("Tenant member data")).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url.includes("organizations") || url.includes("members"))).toBe(false);
  navigation.path = "/";
});

it("personal navigation exposes Contacts independently of company membership", async () => {
  navigation.path = "/contacts";
  saveSession(tokens);
  const fetch = vi.fn(async (url: string) => respond(url.includes("auth/me") ? {context:{organization_id:null,member_id:null}} : {display_name:"Personal User"}));
  vi.stubGlobal("fetch",fetch);
  render(<AuthProvider><WorkspaceFrame><p>Private contacts screen</p></WorkspaceFrame></AuthProvider>);
  await screen.findByText("Private contacts screen");
  expect(screen.getByRole("link",{name:"Contacts"}).getAttribute("href")).toBe("/contacts");
  expect(fetch.mock.calls.some(([url])=>url.includes("organizations")||url.includes("roles"))).toBe(false);
  navigation.path = "/";
});
