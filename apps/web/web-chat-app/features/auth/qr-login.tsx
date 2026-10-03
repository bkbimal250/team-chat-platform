"use client";
import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { deviceApi, Tokens } from "@/features/devices/api";
import { parseQR, qrRemaining } from "./security";
export function QRLogin({
  onCancel,
  onSuccess,
}: {
  onCancel: () => void;
  onSuccess: (tokens: Tokens) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [remaining, setRemaining] = useState(0);
  const [status, setStatus] = useState("Creating secure QR…");
  const [generation, setGeneration] = useState(0);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const abort = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let tick: ReturnType<typeof setInterval>;
    let stopped = false;
    async function start() {
      try {
        const challenge = await deviceApi.createQR(abort.signal);
        if (stopped) return;
        const parsed = parseQR(challenge.payload);
        if (!parsed || parsed.id !== challenge.challenge_id)
          throw new Error("QR link is unavailable. Use phone login.");
        if (canvas.current)
          await QRCode.toCanvas(
            canvas.current,
            `globalchat-link:${parsed.id}.${parsed.secret}`,
            { width: 240, margin: 2 },
          );
        if (stopped) return;
        setReady(true);
        setStatus("Scan from an authenticated GlobalChat device.");
        setRemaining(qrRemaining(challenge.expires_at));
        tick = setInterval(() => {
          const seconds = qrRemaining(challenge.expires_at);
          setRemaining(seconds);
          if (seconds === 0) {
            setReady(false);
            setStatus("QR expired. Generate a new code.");
            clearInterval(tick);
            clearTimeout(timer);
          }
        }, 1000);
        async function poll() {
          if (stopped || qrRemaining(challenge.expires_at) === 0) return;
          try {
            const result = await deviceApi.qrStatus(parsed!.id, abort.signal);
            if (stopped) return;
            if (result.status === "AUTHORIZED") {
              const tokens = await deviceApi.consume(
                parsed!.id,
                parsed!.secret,
                abort.signal,
              );
              if (!stopped) onSuccess(tokens);
              return;
            }
            if (result.status !== "PENDING") {
              setReady(false);
              setStatus(
                `QR ${result.status.toLowerCase()}. Generate a new code.`,
              );
              return;
            }
            timer = setTimeout(poll, 2500);
          } catch {
            if (!stopped) {
              setStatus("Connection lost. Waiting to reconnect…");
              timer = setTimeout(poll, 5000);
            }
          }
        }
        timer = setTimeout(poll, 2500);
      } catch (issue) {
        if (!stopped) {
          setReady(false);
          setStatus(issue instanceof Error ? issue.message : "QR unavailable.");
        }
      }
    }
    void start();
    return () => {
      stopped = true;
      abort.abort();
      clearTimeout(timer);
      clearInterval(tick);
    };
  }, [generation, onSuccess]);
  return (
    <section className="space-y-5 text-center">
      <h2 className="text-2xl font-semibold">Link with QR code</h2>
      <p className="text-sm text-slate-500">
        Scan this code from GlobalChat on your existing device, then approve the
        link.
      </p>
      <canvas
        ref={canvas}
        aria-label="Secure device linking QR code"
        className={`mx-auto rounded-2xl ${ready ? "" : "hidden"}`}
      />
      <p role="status" className="text-sm">
        {status}
      </p>
      {ready && (
        <p className="text-xs text-slate-500">Expires in {remaining}s</p>
      )}
      <div className="flex justify-center gap-4">
        <button
          onClick={() => {
            setReady(false);
            setGeneration((n) => n + 1);
          }}
          className="font-semibold text-cyan-800"
        >
          Refresh QR
        </button>
        <button onClick={onCancel} className="text-slate-500">
          Cancel
        </button>
      </div>
    </section>
  );
}
