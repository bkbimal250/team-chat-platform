import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import QRCode from "qrcode";
import { QRLogin } from "../features/auth/qr-login";
import { deviceApi } from "../features/devices/api";
const id = "550e8400-e29b-41d4-a716-446655440000";
const secret = "a".repeat(43);
afterEach(() => vi.useRealTimers());
it("QR status approval consumes backend challenge before session establishment", async () => {
 vi.useFakeTimers(); vi.spyOn(QRCode, "toCanvas").mockResolvedValue();
 vi.spyOn(deviceApi, "createQR").mockResolvedValue({ challenge_id: id, payload: `https://internal.invalid/link-device?challenge=${id}.${secret}`, expires_at: new Date(Date.now() + 60_000).toISOString() });
 vi.spyOn(deviceApi, "qrStatus").mockResolvedValue({ status: "AUTHORIZED", expires_at: new Date(Date.now() + 60_000).toISOString() });
 const tokens = { access_token: "test-access", refresh_token: "test-refresh" }; const consume = vi.spyOn(deviceApi, "consume").mockResolvedValue(tokens); const success = vi.fn();
 render(<QRLogin onCancel={vi.fn()} onSuccess={success}/>); await act(async () => { await Promise.resolve(); }); expect(success).not.toHaveBeenCalled();
 await act(async () => { await vi.advanceTimersByTimeAsync(2500); }); expect(consume).toHaveBeenCalledWith(id, secret, expect.any(AbortSignal)); expect(success).toHaveBeenCalledWith(tokens);
 expect(QRCode.toCanvas).toHaveBeenCalledWith(expect.any(HTMLCanvasElement), `globalchat-link:${id}.${secret}`, expect.any(Object));
});
it("expired QR stops polling and cannot establish a session", async () => {
 vi.useFakeTimers(); vi.spyOn(QRCode, "toCanvas").mockResolvedValue();
 vi.spyOn(deviceApi, "createQR").mockResolvedValue({ challenge_id: id, payload: `globalchat-link:${id}.${secret}`, expires_at: new Date(Date.now() + 1000).toISOString() }); const poll = vi.spyOn(deviceApi, "qrStatus"); const success = vi.fn();
 render(<QRLogin onCancel={vi.fn()} onSuccess={success}/>); await act(async () => { await Promise.resolve(); await vi.advanceTimersByTimeAsync(5000); }); expect(screen.getByText("QR expired. Generate a new code.")).toBeTruthy(); expect(poll).not.toHaveBeenCalled(); expect(success).not.toHaveBeenCalled();
});
