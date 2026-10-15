import { it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider } from "@/features/auth/auth-provider";
import { PhoneOTPLogin as Login } from "@/features/auth/phone-otp-login";
import { json } from "./fixtures";
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn() }) }));
it("keeps invite-only rejection visible without auto-registration", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue(
      json(
        { error: { code: "REGISTRATION_NOT_ALLOWED", message: "Denied" } },
        403,
      ),
    );
  vi.stubGlobal("fetch", fetch);
  render(
    <AuthProvider>
      <Login />
    </AuthProvider>,
  );
  const user = userEvent.setup();
  await user.type(
    screen.getByRole("textbox", { name: "Phone number" }),
    "+919000000001",
  );
  await user.click(screen.getByRole("button", { name: "Request code" }));
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "This phone number has not been invited. Contact your organization administrator for access.",
  );
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(JSON.parse(fetch.mock.calls[0][1].body).purpose).toBe("LOGIN");
});
it("requests and verifies OTP through the actual Identity request shapes", async () => {
  const fetch = vi.fn(async (url: string, init: RequestInit) => {
    void init;
    return url.includes("otp/request")
      ? json({ challenge_id: "challenge-a" })
      : json({ detail: "Code invalid" }, 400);
  });
  vi.stubGlobal("fetch", fetch);
  render(
    <AuthProvider>
      <Login />
    </AuthProvider>,
  );
  const user = userEvent.setup();
  await user.type(
    screen.getByRole("textbox", { name: "Phone number" }),
    "+919000000001",
  );
  await user.click(screen.getByRole("button", { name: "Request code" }));
  await user.type(
    await screen.findByRole("textbox", { name: "Verification code" }),
    "123456",
  );
  await user.click(screen.getByRole("button", { name: "Verify and sign in" }));
  expect(await screen.findByText("Code invalid")).toBeTruthy();
  const call = fetch.mock.calls.find(([url]) => url.includes("otp/verify"));
  const body = JSON.parse(String(call?.[1]?.body ?? "{}"));
  expect(body.challenge_id).toBe("challenge-a");
  expect(body.device.platform).toBe("WEB");
  expect(body.device.installation_id).toBeTruthy();
});
