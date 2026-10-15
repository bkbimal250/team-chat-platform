import { expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PasswordLogin } from "@/features/auth/password-login";
import { PasswordInvitation } from "@/features/auth/password-invitation";
const mocks = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
const tokens = { access_token: "test-access", refresh_token: "test-refresh" };
it("logs in with email through Gateway without requesting OTP", async () => {
  const fetch = vi.fn<typeof globalThis.fetch>(async () => new Response(JSON.stringify(tokens), { status: 200 })); vi.stubGlobal("fetch", fetch);
  const success = vi.fn(); render(<PasswordLogin onAuthenticated={success} />); const user = userEvent.setup({delay:null});
  await user.click(screen.getByLabelText("Email")); await user.paste("employee@example.test"); await user.click(screen.getByLabelText("Password")); await user.paste("Long password 123!"); await user.click(screen.getByRole("button", { name: "Sign In" }));
  await waitFor(() => expect(success).toHaveBeenCalledOnce()); expect(fetch.mock.calls[0][0]).toBe("/api/gateway/api/v1/auth/login");
});
it("keeps wrong-password failure visible without authentication", async () => {
  vi.stubGlobal("fetch", vi.fn<typeof globalThis.fetch>(async () => new Response(JSON.stringify({ error: { code: "INVALID_CREDENTIALS", message: "Invalid email or password." } }), { status: 401 })));
  const success = vi.fn(); render(<PasswordLogin onAuthenticated={success} />); const user = userEvent.setup({delay:null});
  await user.click(screen.getByLabelText("Email")); await user.paste("employee@example.test"); await user.click(screen.getByLabelText("Password")); await user.paste("wrong password"); await user.click(screen.getByRole("button", { name: "Sign In" }));
  expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Invalid email or password."); expect(success).not.toHaveBeenCalled();
});
it("accepts a private invitation with password and removes the URL token", async () => {
  window.history.replaceState(null, "", "/join#invite=" + "a".repeat(43));
  const fetch = vi.fn<typeof globalThis.fetch>(async () => new Response(JSON.stringify(tokens), { status: 200 })); vi.stubGlobal("fetch", fetch);
  render(<PasswordInvitation />); const user = userEvent.setup({delay:null});
  await user.click(screen.getByLabelText("Email")); await user.paste("employee@example.test"); await user.click(screen.getByLabelText("Password")); await user.paste("Long password 123!"); await user.click(screen.getByLabelText("Confirm password")); await user.paste("Long password 123!"); await user.click(screen.getByRole("button", { name: "Join workspace" }));
  await waitFor(() => expect(mocks.replace).toHaveBeenCalledWith("/")); expect(window.location.hash).toBe(""); expect(fetch.mock.calls[0][0]).toBe("/api/gateway/api/v1/auth/invitations/password");
});
