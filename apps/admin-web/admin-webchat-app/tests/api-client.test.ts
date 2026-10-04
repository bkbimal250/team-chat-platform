import { describe, it, expect, vi } from "vitest";
import { apiRequest, gatewayPath } from "@/lib/api/client";
import { readSession, saveSession } from "@/lib/auth/session";
import { tokens, json } from "./fixtures";
describe("central Gateway client", () => {
  it("forwards bearer auth and encoded query to the same-origin Gateway bridge", async () => {
    saveSession(tokens);
    const fetch = vi.fn().mockResolvedValue(json({ name: "Workspace" }));
    vi.stubGlobal("fetch", fetch);
    await apiRequest("/api/v1/members/", {
      query: { search: "A & B", page_size: 20 },
    });
    const [url, init] = fetch.mock.calls[0];
    expect(url).toContain("search=A+%26+B");
    expect(url).toContain("page_size=20");
    expect(new Headers(init.headers).get("Authorization")).toBe(
      "Bearer test-access",
    );
  });
  it("does not send existing credentials on public OTP requests", async () => {
    saveSession(tokens);
    const fetch = vi
      .fn()
      .mockResolvedValue(json({ challenge_id: "test-challenge" }));
    vi.stubGlobal("fetch", fetch);
    await apiRequest("/api/v1/auth/otp/request", {
      public: true,
      method: "POST",
      body: "{}",
    });
    expect(
      new Headers(fetch.mock.calls[0][1].headers).has("Authorization"),
    ).toBe(false);
  });
  it("refreshes once and retries with the rotated token on 401", async () => {
    saveSession(tokens);
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(json({ detail: "expired" }, 401))
      .mockResolvedValueOnce(
        json({
          ...tokens,
          access_token: "rotated",
          refresh_token: "rotated-refresh",
        }),
      )
      .mockResolvedValueOnce(json({ ok: true }));
    vi.stubGlobal("fetch", fetch);
    expect(await apiRequest("/api/v1/users/me")).toEqual({ ok: true });
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls[1][0]).toContain("/auth/refresh");
    expect(
      new Headers(fetch.mock.calls[2][1].headers).get("Authorization"),
    ).toBe("Bearer rotated");
  });
  it("clears an invalid session when refresh is rejected", async () => {
    saveSession(tokens);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(json({ detail: "invalid" }, 401)),
    );
    await expect(apiRequest("/api/v1/users/me")).rejects.toMatchObject({
      status: 401,
    });
    expect(readSession()).toBeNull();
  });
  it("preserves a valid session on 403 and does not refresh", async () => {
    saveSession(tokens);
    const fetch = vi
      .fn()
      .mockResolvedValue(
        json(
          {
            error: { code: "PERMISSION_DENIED", message: "Permission denied." },
          },
          403,
        ),
      );
    vi.stubGlobal("fetch", fetch);
    await expect(apiRequest("/api/v1/invitations/")).rejects.toMatchObject({
      status: 403,
      code: "PERMISSION_DENIED",
    });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(readSession()?.access_token).toBe(tokens.access_token);
  });
  it("shows backend field validation errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(json({ name: ["This field is required."] }, 400)),
    );
    await expect(
      apiRequest("/api/v1/branches/", { method: "POST", body: "{}" }),
    ).rejects.toMatchObject({ fields: { name: "This field is required." } });
  });
  it("redacts network exception details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("secret request details")),
    );
    await expect(apiRequest("/api/v1/users/me")).rejects.toMatchObject({
      code: "NETWORK_ERROR",
      message: "Cannot reach GlobalChat. Check your connection and retry.",
    });
  });
  it("normalizes private upstream cursor links without fetching private origins", () => {
    expect(
      gatewayPath("http://organization:8000/api/v1/members/?cursor=abc"),
    ).toBe("/api/v1/members/?cursor=abc");
    expect(() => gatewayPath("http://example.com/internal/v1/users")).toThrow(
      "Unsupported Gateway route.",
    );
  });
});
