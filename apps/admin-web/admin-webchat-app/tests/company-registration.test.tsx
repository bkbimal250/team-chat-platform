import { it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CompanyOTPRegistration as CompanyRegistration } from "@/features/auth/company-otp-registration";
import { json } from "./fixtures";
const mocks = vi.hoisted(() => ({ login: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mocks.replace }),
}));
vi.mock("@/features/auth/auth-provider", () => ({
  useAuth: () => ({ login: mocks.login }),
}));
async function fill(phone = "+919000000003") {
  const user = userEvent.setup({ delay: null });
  for (const [name, value] of [
    ["Company Name", "Development Company"],
    ["Owner Name", "Development Owner"],
    ["Email", "owner@example.com"],
    ["Phone Number", phone],
  ]) {
    await user.click(screen.getByRole("textbox", { name }));
    await user.paste(value);
  }
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


it("searches country names and calling codes and submits normalized national phone", async () => {
 const fetch = vi.fn().mockResolvedValue(json(challenge, 202)); vi.stubGlobal("fetch",fetch);
 render(<CompanyRegistration />); const user=userEvent.setup({ delay: null });
 await user.type(screen.getByRole("searchbox", { name: "Search country or calling code" }), "+44");
 expect(screen.getByRole("option", { name: "United Kingdom (+44)" })).toBeTruthy();
 await user.selectOptions(screen.getByRole("combobox", { name: "Country calling code" }), "GB");
 await fill("07911 123456");
 await screen.findByRole("textbox", { name: "Verification code" });
 expect(JSON.parse(String(fetch.mock.calls[0][1].body)).phone).toBe("+447911123456");
});
it("uses server retry time and prevents repeated requests after 429", async () => {
 const fetch=vi.fn().mockResolvedValue(json({error:{code:"RATE_LIMITED", message:"Too many requests.",details:{retry_after:120}}},429)); vi.stubGlobal("fetch",fetch);
 render(<CompanyRegistration />); await fill();
 const button=await screen.findByRole("button",{name:/Try again in/});
 expect(button).toHaveProperty("disabled",true);
 await userEvent.click(button); expect(fetch).toHaveBeenCalledTimes(1);
 expect(screen.getByRole("status").textContent).toContain("Repeated requests will not send a code");
});
it("rejects an invalid phone without requesting an OTP", async () => {
 const fetch=vi.fn(); vi.stubGlobal("fetch",fetch); render(<CompanyRegistration />); await fill("123");
 expect(await screen.findByRole("alert")).toHaveProperty("textContent","Enter a valid phone number for the selected country."); expect(fetch).not.toHaveBeenCalled();
});
