import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  ForgotPassword,
  ResetPassword,
} from "@/features/auth/password-recovery";

it("shows the same generic success state after requesting password recovery", async () => {
  const fetch = vi.fn<typeof globalThis.fetch>(
    async () =>
      new Response(
        JSON.stringify({
          message:
            "If an account exists for this email, password reset instructions have been prepared.",
        }),
        { status: 200 },
      ),
  );
  vi.stubGlobal("fetch", fetch);
  render(<ForgotPassword />);
  const user = userEvent.setup({ delay: null });
  await user.type(screen.getByLabelText("Email"), "unknown@example.test");
  await user.click(
    screen.getByRole("button", { name: "Send reset instructions" }),
  );
  expect(await screen.findByRole("status")).toHaveProperty(
    "textContent",
    "If an account exists for this email, password reset instructions have been prepared.",
  );
  expect(fetch.mock.calls[0][0]).toBe(
    "/api/gateway/api/v1/auth/password/forgot",
  );
});

it("validates confirmation and resets using only the URL token", async () => {
  window.history.replaceState(
    null,
    "",
    "/reset-password?token=" + "a".repeat(64),
  );
  const fetch = vi.fn<typeof globalThis.fetch>(
    async () => new Response(null, { status: 204 }),
  );
  vi.stubGlobal("fetch", fetch);
  render(<ResetPassword />);
  const user = userEvent.setup({ delay: null });
  await user.type(
    screen.getByLabelText("New password"),
    "A valid new password!",
  );
  await user.type(
    screen.getByLabelText("Confirm password"),
    "different password",
  );
  await user.click(screen.getByRole("button", { name: "Update password" }));
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "Passwords do not match.",
  );
  await user.clear(screen.getByLabelText("Confirm password"));
  await user.type(
    screen.getByLabelText("Confirm password"),
    "A valid new password!",
  );
  await user.click(screen.getByRole("button", { name: "Update password" }));
  expect(await screen.findByRole("status")).toHaveProperty(
    "textContent",
    "Password updated successfully.",
  );
  expect(fetch.mock.calls[0][0]).toBe(
    "/api/gateway/api/v1/auth/password/reset",
  );
});

it("shows a safe invalid-link error", async () => {
  window.history.replaceState(
    null,
    "",
    "/reset-password?token=" + "a".repeat(64),
  );
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(
          JSON.stringify({
            error: { code: "PASSWORD_RESET_INVALID", message: "hidden" },
          }),
          { status: 409 },
        ),
    ),
  );
  render(<ResetPassword />);
  const user = userEvent.setup({ delay: null });
  await user.type(
    screen.getByLabelText("New password"),
    "A valid new password!",
  );
  await user.type(
    screen.getByLabelText("Confirm password"),
    "A valid new password!",
  );
  await user.click(screen.getByRole("button", { name: "Update password" }));
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "This password reset link is invalid, expired, or has already been used.",
  );
});
