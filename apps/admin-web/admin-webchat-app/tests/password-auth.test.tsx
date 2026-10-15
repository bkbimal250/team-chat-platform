import { expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PasswordAuth } from "@/features/auth/password-auth";
import { json, tokens } from "./fixtures";
const mocks = vi.hoisted(() => ({ login: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
vi.mock("@/features/auth/auth-provider", () => ({ useAuth: () => ({ login: mocks.login }) }));

it("signs in using email and the existing session without OTP", async () => {
  const fetch = vi.fn<typeof globalThis.fetch>(async () => json(tokens)); vi.stubGlobal("fetch", fetch);
  render(<PasswordAuth />); const user = userEvent.setup({ delay: null });
  await user.click(screen.getByLabelText("Email")); await user.paste("owner@example.test");
  await user.click(screen.getByLabelText("Password")); await user.paste("Long password 123!");
  await user.click(screen.getByRole("button", { name: "Sign In" }));
  await waitFor(() => expect(mocks.login).toHaveBeenCalledWith(tokens));
  expect(fetch.mock.calls[0][0]).toBe("/api/gateway/api/v1/auth/login");
  expect(screen.queryByText("Verification code")).toBeNull();
});
it("shows a generic wrong-password error without creating a session", async () => {
  mocks.login.mockClear(); vi.stubGlobal("fetch", vi.fn<typeof globalThis.fetch>(async () => json({ error: { code: "INVALID_CREDENTIALS", message: "Invalid email or password." } }, 401)));
  render(<PasswordAuth />); const user = userEvent.setup({ delay: null });
  await user.click(screen.getByLabelText("Email")); await user.paste("owner@example.test"); await user.click(screen.getByLabelText("Password")); await user.paste("Wrong password");
  await user.click(screen.getByRole("button", { name: "Sign In" }));
  expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Invalid email or password."); expect(mocks.login).not.toHaveBeenCalled();
});
it("validates confirmation and registers a company without an OTP step", async () => {
  const fetch = vi.fn<typeof globalThis.fetch>(async () => json(tokens)); vi.stubGlobal("fetch", fetch);
  render(<PasswordAuth registration />); const user = userEvent.setup({ delay: null });
  await user.click(screen.getByLabelText("Company name")); await user.paste("New Company"); await user.click(screen.getByLabelText("Owner name")); await user.paste("Owner Name"); await user.click(screen.getByLabelText("Email")); await user.paste("owner@example.test"); await user.click(screen.getByLabelText("Phone Number")); await user.paste("9000000003"); await user.click(screen.getByLabelText("Password")); await user.paste("Long password 123!"); await user.click(screen.getByLabelText("Confirm password")); await user.paste("different password");
  await user.click(screen.getByRole("button", { name: "Create Company" })); expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Passwords do not match."); expect(fetch).not.toHaveBeenCalled();
  await user.clear(screen.getByLabelText("Confirm password")); await user.click(screen.getByLabelText("Confirm password")); await user.paste("Long password 123!"); await user.click(screen.getByRole("button", { name: "Create Company" }));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1)); expect(fetch.mock.calls[0][0]).toBe("/api/gateway/api/v1/auth/registration/company");
});
