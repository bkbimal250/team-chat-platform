import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { QRScanner } from "../features/devices/qr-scanner";
import { Login } from "../features/auth/login";
import { identityApi, ApiError } from "../lib/api/client";
it("scanner cancel stops camera and unmount clears video", async () => {
 const stop = vi.fn(); const media = { getTracks: () => [{ stop }] } as unknown as MediaStream;
 Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia: vi.fn().mockResolvedValue(media) } });
 vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
 vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
 const cancel = vi.fn(); const { unmount } = render(<QRScanner token="test" onCancel={cancel} onSuccess={vi.fn()}/>);
 await screen.findByText(/Scanning/); fireEvent.click(screen.getByRole("button", { name: "Cancel" })); expect(stop).toHaveBeenCalled(); expect(cancel).toHaveBeenCalledOnce(); unmount();
});
it("camera resolving after navigation is stopped", async () => {
 let resolve!: (stream: MediaStream) => void; const stop = vi.fn();
 Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia: vi.fn().mockReturnValue(new Promise<MediaStream>((r) => { resolve = r; })) } });
 const { unmount } = render(<QRScanner token="test" onCancel={vi.fn()} onSuccess={vi.fn()}/>); unmount(); resolve({ getTracks: () => [{ stop }] } as unknown as MediaStream); await waitFor(() => expect(stop).toHaveBeenCalledOnce());
});
it("invite-only rejection remains visible without establishing session", async () => {
 vi.spyOn(identityApi, "requestOtp").mockRejectedValue(new ApiError("REGISTRATION_NOT_ALLOWED", "Not invited")); const success = vi.fn(); render(<Login onAuthenticated={success}/>);
 fireEvent.click(screen.getByRole("button", { name: "Continue with phone" })); fireEvent.change(screen.getByLabelText("Phone number"), { target: { value: "9876543210" } }); fireEvent.click(screen.getByRole("button", { name: "Send verification code" })); await screen.findByText("Invitation required"); expect(success).not.toHaveBeenCalled();
});

