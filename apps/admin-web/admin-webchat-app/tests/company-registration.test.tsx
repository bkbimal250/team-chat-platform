import { it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CompanyRegistration } from "@/features/auth/company-registration";
import { json } from "./fixtures";
const mocks = vi.hoisted(() => ({ login: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace }),
}));
vi.mock("@/features/auth/auth-provider", () => ({
  useAuth: () => ({ login: mocks.login }),
}));
async function fill() {
  const user = userEvent.setup();
  await user.type(
    screen.getByRole("textbox", { name: "Company Name" }),
    "Development Company",
  );
  await user.type(
    screen.getByRole("textbox", { name: "Owner Name" }),
    "Development Owner",
  );
  await user.type(
    screen.getByRole("textbox", { name: "Email" }),
    "owner@example.com",
  );
  await user.type(
    screen.getByRole("textbox", { name: "Phone Number" }),
    "+919000000003",
  );
  await user.click(
    screen.getByRole("button", { name: "Request registration code" }),
  );
  return user;
}
const challenge = {
  registration_id: "opaque-registration",
  expires_at: new Date(Date.now() + 300000).toISOString(),
  resend_after: 60,
};
it("submits registration details then verifies only authoritative challenge and device", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json(challenge, 202))
    .mockResolvedValueOnce(json({ access_token: "test-token" }));
  vi.stubGlobal("fetch", fetch);
  render(<CompanyRegistration />);
  const user = await fill();
  await user.type(
    await screen.findByRole("textbox", { name: "Verification code" }),
    "123456",
  );
  await user.click(
    screen.getByRole("button", { name: "Verify and create company" }),
  );
  await waitFor(() => expect(mocks.replace).toHaveBeenCalledWith("/dashboard"));
  const body = JSON.parse(String(fetch.mock.calls[1][1].body));
  expect(Object.keys(body).sort()).toEqual([
    "device",
    "otp",
    "registration_id",
  ]);
  expect(body.registration_id).toBe(challenge.registration_id);
  expect(body.device.platform).toBe("WEB");
  expect(mocks.login).toHaveBeenCalled();
});
it("shows duplicate account error without issuing tokens", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        json(
          {
            error: {
              code: "ACCOUNT_EXISTS",
              message: "Sign in to your existing account.",
            },
          },
          409,
        ),
      ),
  );
  render(<CompanyRegistration />);
  await fill();
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "Sign in to your existing account.",
  );
});
it("shows provisioning retry and preserves challenge instead of submitting company again", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json(challenge, 202))
    .mockResolvedValueOnce(
      json(
        { error: { code: "PROVISIONING_RETRY", message: "Retry safely." } },
        503,
      ),
    );
  vi.stubGlobal("fetch", fetch);
  render(<CompanyRegistration />);
  const user = await fill();
  await user.type(
    await screen.findByRole("textbox", { name: "Verification code" }),
    "123456",
  );
  await user.click(
    screen.getByRole("button", { name: "Verify and create company" }),
  );
  expect(
    await screen.findByRole("button", { name: "Resume provisioning" }),
  ).toBeTruthy();
  expect(screen.getByText(/Verified. Retry with the same code/)).toBeTruthy();
});
it("disables resend during the server cooldown", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(json(challenge, 202)));
  render(<CompanyRegistration />);
  await fill();
  expect(
    await screen.findByRole("button", { name: /Resend in/ }),
  ).toHaveProperty("disabled", true);
});
