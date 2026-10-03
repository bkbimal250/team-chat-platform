import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { LinkedDevices } from "../features/devices/linked-devices";
import { deviceApi } from "../features/devices/api";
import { QRLogin } from "../features/auth/qr-login";
const row = { id: "device", platform: "WEB", device_name: "Test browser", device_model: null, status: "ACTIVE", first_seen_at: new Date().toISOString(), last_seen_at: new Date().toISOString(), is_current: false };
it("device revocation requires confirmation and uses real API adapter", async () => {
 vi.spyOn(deviceApi, "list").mockResolvedValue([row]); const revoke = vi.spyOn(deviceApi, "revoke").mockResolvedValue({});
 render(<LinkedDevices token="test" onSignedOut={vi.fn()}/>); await screen.findByText("Test browser"); fireEvent.click(screen.getByRole("button", { name: "Log out device" })); expect(revoke).not.toHaveBeenCalled(); fireEvent.click(screen.getByRole("button", { name: "Confirm" })); await waitFor(() => expect(revoke).toHaveBeenCalledWith("device", "test"));
});
it("QR cancellation aborts pending challenge request", async () => {
 let signal: AbortSignal | undefined; vi.spyOn(deviceApi, "createQR").mockImplementation((input) => { signal = input; return new Promise(() => {}); }); const cancel = vi.fn(); const { unmount } = render(<QRLogin onCancel={cancel} onSuccess={vi.fn()}/>); fireEvent.click(screen.getByRole("button", { name: "Cancel" })); expect(cancel).toHaveBeenCalledOnce(); unmount(); expect(signal?.aborted).toBe(true);
});
