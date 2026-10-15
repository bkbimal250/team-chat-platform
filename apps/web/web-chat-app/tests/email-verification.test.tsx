import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  EmailVerificationStatus,
  VerifyEmail,
} from "@/features/auth/email-verification";

it("verifies a URL token and shows the success state", async () => {
  window.history.replaceState(
    null,
    "",
    "/verify-email?token=" + "a".repeat(64),
  );
  const fetch = vi.fn<typeof globalThis.fetch>(
    async () => new Response(null, { status: 204 }),
  );
  vi.stubGlobal("fetch", fetch);
  render(<VerifyEmail />);
  await userEvent
    .setup({ delay: null })
    .click(screen.getByRole("button", { name: "Verify email" }));
  expect(await screen.findByRole("status")).toHaveProperty(
    "textContent",
    "Email verified successfully.",
  );
  expect(fetch.mock.calls[0][0]).toBe("/api/gateway/api/v1/auth/email/verify");
});

it("shows a safe error for invalid, expired, or used verification links", async () => {
  window.history.replaceState(
    null,
    "",
    "/verify-email?token=" + "a".repeat(64),
  );
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(
          JSON.stringify({ error: { code: "EMAIL_VERIFICATION_INVALID" } }),
          { status: 409 },
        ),
    ),
  );
  render(<VerifyEmail />);
  await userEvent
    .setup({ delay: null })
    .click(screen.getByRole("button", { name: "Verify email" }));
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "This verification link is invalid, expired, or has already been used.",
  );
});

it("shows actual unverified status and safely resends", async () => {
  const fetch = vi
    .fn<typeof globalThis.fetch>()
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          identity: { email: "person@example.test", email_verified: false },
        }),
        { status: 200 },
      ),
    )
    .mockResolvedValueOnce(
      new Response(JSON.stringify({ message: "generic" }), { status: 200 }),
    );
  vi.stubGlobal("fetch", fetch);
  render(<EmailVerificationStatus token="test-token" />);
  expect(await screen.findByText("Email not verified")).toBeTruthy();
  await userEvent
    .setup({ delay: null })
    .click(screen.getByRole("button", { name: "Resend verification" }));
  expect(fetch.mock.calls[1][0]).toBe(
    "/api/gateway/api/v1/auth/email/verification/resend",
  );
});

it("shows the backend-confirmed verified state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(JSON.stringify({ identity: { email_verified: true } }), {
          status: 200,
        }),
    ),
  );
  render(<EmailVerificationStatus token="test-token" />);
  expect(await screen.findByText("Email verified")).toBeTruthy();
});
