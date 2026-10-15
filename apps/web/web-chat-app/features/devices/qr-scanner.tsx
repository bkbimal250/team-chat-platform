"use client";
import { useEffect, useRef, useState } from "react";
import jsQR from "jsqr";
import { parseQR, stopCamera } from "@/features/auth/security";
import { deviceApi } from "./api";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
export function QRScanner({
  token,
  onCancel,
  onSuccess,
}: {
  token: string;
  onCancel: () => void;
  onSuccess: () => void;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const stream = useRef<MediaStream | null>(null);
  const [scanned, setScanned] = useState<{ id: string; secret: string } | null>(
    null,
  );
  const [message, setMessage] = useState("Starting camera…");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let disposed = false;
    let frame = 0;
    const element = video.current;
    async function start() {
      try {
        if (!navigator.mediaDevices?.getUserMedia)
          throw new Error(
            "Camera is unavailable. Use a supported browser over HTTPS.",
          );
        const media = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });
        if (disposed) {
          stopCamera(media);
          return;
        }
        stream.current = media;
        const preview = video.current;
        if (!preview) {
          stopCamera(media);
          return;
        }
        preview.srcObject = media;
        await preview.play();
        if (disposed) return;
        setMessage("Scanning… Point your camera at the new device’s QR code.");
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d", { willReadFrequently: true });
        function scan() {
          if (disposed || !context) return;
          if (preview!.readyState >= 2 && preview!.videoWidth) {
            canvas.width = preview!.videoWidth;
            canvas.height = preview!.videoHeight;
            context.drawImage(preview!, 0, 0);
            const image = context.getImageData(
              0,
              0,
              canvas.width,
              canvas.height,
            );
            const result = jsQR(image.data, image.width, image.height);
            if (result) {
              const payload = parseQR(result.data);
              if (payload) {
                stopCamera(stream.current);
                setScanned(payload);
                setMessage("Review this device link before approving.");
                return;
              }
              setMessage("Invalid QR. Scan a GlobalChat device-link code.");
            }
          }
          frame = requestAnimationFrame(scan);
        }
        frame = requestAnimationFrame(scan);
      } catch (issue) {
        if (!disposed) {
          const name = issue instanceof DOMException ? issue.name : "";
          setMessage(
            name === "NotAllowedError"
              ? "Camera permission denied. Allow camera access in your browser and try again."
              : name === "NotFoundError"
                ? "No camera found on this device."
                : "Camera unavailable. Try a supported browser with camera access.",
          );
          stopCamera(stream.current);
        }
      }
    }
    void start();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      stopCamera(stream.current);
      if (element) element.srcObject = null;
    };
  }, []);
  async function approve() {
    if (!scanned || busy) return;
    setBusy(true);
    try {
      await deviceApi.authorize(scanned.id, scanned.secret, token);
      stopCamera(stream.current);
      onSuccess();
    } catch (issue) {
      setScanned(null);
      setMessage(
        issue instanceof Error
          ? issue.message
          : "Unable to approve. The QR may be expired or already used.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="space-y-5">
      <h2 className="text-xl font-semibold">Link a device</h2>
      <p className="text-sm text-aurora-muted">
        Scan the QR code shown on the device you want to link.
      </p>
      <video
        ref={video}
        muted
        playsInline
        className="aspect-square w-full max-w-md rounded-3xl bg-slate-950 object-cover"
        aria-label="QR camera preview"
      />
      <p role="status" className="text-sm">
        {message}
      </p>
      <button
        onClick={() => {
          stopCamera(stream.current);
          onCancel();
        }}
        className="rounded-xl border px-4 py-2"
      >
        Cancel
      </button>
      {scanned && (
        <ConfirmDialog
          title="Approve device link?"
          busy={busy}
          onCancel={() => {
            stopCamera(stream.current);
            onCancel();
          }}
          onConfirm={() => void approve()}
        >
          Only approve if you are linking your own device. This grants it access
          to your workspace.
        </ConfirmDialog>
      )}
    </section>
  );
}
