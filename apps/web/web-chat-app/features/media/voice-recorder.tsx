"use client";
import { useEffect, useRef, useState } from "react";
export function VoiceRecorder({
  onRecorded,
  disabled,
  onBusyChange,
}: {
  onRecorded: (file: File) => void;
  disabled: boolean;
  onBusyChange?: (busy: boolean) => void;
}) {
  const [state, setState] = useState<"idle" | "permission" | "recording">(
    "idle",
  );
  const [error, setError] = useState("");
  const [seconds, setSeconds] = useState(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const mounted = useRef(true);
  const discarded = useRef(false);
  useEffect(() => { onBusyChange?.(state !== "idle"); }, [state, onBusyChange]);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      discarded.current = true;
      if (recorder.current?.state === "recording") recorder.current.stop();
      stream.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);
  useEffect(() => {
    if (state !== "recording") return;
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, [state]);
  async function start() {
    setError("");
    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setError("Voice recording is not supported in this browser.");
      return;
    }
    const mime = [
      "audio/webm;codecs=opus",
      "audio/ogg;codecs=opus",
      "audio/webm",
    ].find((type) => MediaRecorder.isTypeSupported(type));
    if (!mime) {
      setError("This browser cannot record a supported audio format.");
      return;
    }
    setState("permission");
    try {
      const media = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current) {
        media.getTracks().forEach((track) => track.stop());
        return;
      }
      stream.current = media;
      const instance = new MediaRecorder(media, { mimeType: mime });
      recorder.current = instance;
      const chunks: Blob[] = [];
      discarded.current = false;
      instance.ondataavailable = (event) => {
        if (event.data.size) chunks.push(event.data);
      };
      instance.onstop = () => {
        media.getTracks().forEach((track) => track.stop());
        stream.current = null;
        if (!mounted.current) return;
        setState("idle");
        if (!discarded.current) {
          const type = mime.split(";")[0];
          const blob = new Blob(chunks, { type });
          if (blob.size)
            onRecorded(
              new File(
                [blob],
                `voice-note.${type === "audio/ogg" ? "ogg" : "webm"}`,
                { type },
              ),
            );
          else setError("No audio was recorded. Please try again.");
        }
      };
      instance.onerror = () => {
        discarded.current = true;
        media.getTracks().forEach((track) => track.stop());
        if (mounted.current) {
          setState("idle");
          setError("Recording failed. Please try again.");
        }
      };
      instance.start();
      setSeconds(0);
      setState("recording");
    } catch {
      stream.current?.getTracks().forEach((track) => track.stop());
      if (mounted.current) {
        setState("idle");
        setError("Microphone access was denied or unavailable.");
      }
    }
  }
  return (
    <div>
      {state === "recording" ? (
        <div className="flex items-center gap-2">
          <span role="status" className="text-sm text-red-600">
            ● Recording {seconds}s
          </span>
          <button type="button" onClick={() => recorder.current?.stop()}>
            Stop recording
          </button>
          <button
            type="button"
            onClick={() => {
              discarded.current = true;
              recorder.current?.stop();
            }}
          >
            Cancel recording
          </button>
        </div>
      ) : (
        <button
          type="button"
          disabled={disabled || state === "permission"}
          onClick={() => void start()}
          className="rounded-lg px-3 py-2 text-sm text-cyan-800"
        >
          {state === "permission" ? "Allow microphone…" : "Record voice note"}
        </button>
      )}
      {error && (
        <p role="alert" className="text-sm text-rose-700">
          {error}
        </p>
      )}
    </div>
  );
}
