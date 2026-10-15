import { StrictMode } from "react";
import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PhoneOTPInvitationJoin as InvitationJoin } from "@/features/auth/phone-otp-invitation";
import { getAccessToken, clearSession } from "@/lib/auth/session";
const mocks = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
const secret = "a".repeat(43);
const view = { valid: true, company_name: "Workspace Alpha", recipient_name: "Employee B", recipient_phone_masked: "+91••••••0003", expires_at: new Date(Date.now() + 86400000).toISOString() };
const challenge = { onboarding_id: "opaque-onboarding", expires_at: new Date(Date.now() + 300000).toISOString(), resend_after: 60, development_code: "123456" };
function json(data: unknown, status = 200) { return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json" } }); }
beforeEach(() => { mocks.replace.mockClear(); clearSession(); window.history.replaceState(null, "", "/join#invite=" + secret); });
it("binds all onboarding requests to the secret/challenge and enters the normal session", async () => {
  const fetch = vi.fn().mockResolvedValueOnce(json(view)).mockResolvedValueOnce(json(challenge, 202)).mockResolvedValueOnce(json({ access_token: "test-access", refresh_token: "test-refresh" }));
  vi.stubGlobal("fetch", fetch);
  render(<InvitationJoin />);
  expect(await screen.findByText("Workspace Alpha")).toBeTruthy();
  expect(window.location.hash).toBe("");
  expect(screen.getByText(view.recipient_phone_masked)).toBeTruthy();
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Request invitation code" }));
  await user.type(await screen.findByRole("textbox", { name: "Verification code" }), "123456");
  await user.click(screen.getByRole("button", { name: "Verify and join workspace" }));
  await waitFor(() => expect(mocks.replace).toHaveBeenCalledWith("/"));
  expect(getAccessToken()).toBe("test-access");
  const validate = JSON.parse(fetch.mock.calls[0][1].body);
  const request = JSON.parse(fetch.mock.calls[1][1].body);
  const verify = JSON.parse(fetch.mock.calls[2][1].body);
  expect(validate).toEqual({ token: secret }); expect(request).toEqual(validate);
  expect(Object.keys(verify).sort()).toEqual(["device", "onboarding_id", "otp"]);
  expect(verify.onboarding_id).toBe(challenge.onboarding_id);
  expect(fetch.mock.calls.every((call) => !String(call[0]).includes(secret))).toBe(true);
  clearSession();
});
it.each(["INVITATION_INVALID", "INVITATION_EXPIRED", "INVITATION_REVOKED", "INVITATION_ACCEPTED"])("shows safe %s without an OTP request", async (code) => {
  const fetch = vi.fn().mockResolvedValue(json({ error: { code, message: "sensitive upstream body" } }, 410)); vi.stubGlobal("fetch", fetch);
  render(<InvitationJoin />);
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(screen.queryByText("sensitive upstream body")).toBeNull();
  expect(screen.queryByRole("button", { name: "Request invitation code" })).toBeNull();
  expect(fetch).toHaveBeenCalledOnce(); expect(getAccessToken()).toBeNull();
});
it.each(["OTP_INVALID", "OTP_EXPIRED", "OTP_TOO_MANY_ATTEMPTS", "PROVISIONING_RETRY", "NETWORK_ERROR"])("handles %s without navigation or session issuance", async (code) => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(json(view)).mockResolvedValueOnce(json(challenge, 202)).mockResolvedValueOnce(json({ error: { code } }, 400)));
  render(<InvitationJoin />); const user = userEvent.setup();
  await user.click(await screen.findByRole("button", { name: "Request invitation code" }));
  await user.type(await screen.findByRole("textbox", { name: "Verification code" }), "123456");
  await user.click(screen.getByRole("button", { name: "Verify and join workspace" }));
  expect(await screen.findByRole("alert")).toBeTruthy(); expect(mocks.replace).not.toHaveBeenCalled(); expect(getAccessToken()).toBeNull();
});
it("keeps the fragment secret through StrictMode cleanup without leaving it in the URL", async () => {
  const fetch = vi.fn().mockImplementation(() => Promise.resolve(json(view))); vi.stubGlobal("fetch", fetch);
  render(<StrictMode><InvitationJoin /></StrictMode>);
  expect(await screen.findByText("Workspace Alpha")).toBeTruthy();
  expect(fetch.mock.calls.every((call) => JSON.parse(call[1].body).token === secret)).toBe(true);
  expect(window.location.hash).toBe("");
});
