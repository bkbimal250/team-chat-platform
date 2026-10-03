import { describe, expect, it, vi } from "vitest";
import { e164, parseQR, qrRemaining, stopCamera } from "../features/auth/security";
import { saveSession, getAccessToken, clearSession } from "../lib/auth/session";
const id = "550e8400-e29b-41d4-a716-446655440000";
const secret = "a".repeat(43);
describe("authentication security", () => {
 it("normalizes phone entry and rejects invalid E.164", () => { expect(e164("91", "98765 43210")).toBe("+919876543210"); expect(e164("91", "abc")).toBeNull(); });
 it("extracts only opaque backend challenge data", () => { expect(parseQR(`https://internal.example/link-device?challenge=${id}.${secret}`)).toEqual({ id, secret }); expect(parseQR(`globalchat-link:${id}.${secret}`)).toEqual({ id, secret }); });
 it("rejects arbitrary QR content", () => { expect(parseQR("Bearer sensitive-token")).toBeNull(); expect(parseQR(`globalchat-link:${id}.short`)).toBeNull(); });
 it("QR countdown clamps expired challenges to zero", () => { expect(qrRemaining("2026-01-01T00:00:10Z", Date.parse("2026-01-01T00:00:00Z"))).toBe(10); expect(qrRemaining("2026-01-01T00:00:00Z", Date.parse("2026-01-01T00:00:10Z"))).toBe(0); });
 it("stops every camera track", () => { const a = vi.fn(); const b = vi.fn(); stopCamera({ getTracks: () => [{ stop: a }, { stop: b }] } as unknown as MediaStream); expect(a).toHaveBeenCalledOnce(); expect(b).toHaveBeenCalledOnce(); });
 it("session transitions store and remove credentials", () => { saveSession({ access_token: "test-access", refresh_token: "test-refresh" }); expect(getAccessToken()).toBe("test-access"); clearSession(); expect(getAccessToken()).toBeNull(); });
});
