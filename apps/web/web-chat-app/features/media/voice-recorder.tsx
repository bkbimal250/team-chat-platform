"use client";
import { useEffect, useRef, useState } from "react";
import { Mic, Square, X } from "lucide-react";
import { IconButton, iconSize } from "@/components/ui/icon-button";
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
          <IconButton
            label="Stop recording"
            onClick={() => recorder.current?.stop()}
            className="text-red-700"
          >
            <Square className={iconSize} />
          </IconButton>
          <IconButton
            label="Cancel recording"
            onClick={() => {
              discarded.current = true;
              recorder.current?.stop();
            }}
            className="text-aurora-muted"
          >
            <X className={iconSize} />
          </IconButton>
        </div>
      ) : state === "permission" ? (
        <span role="status" className="px-2 py-2 text-sm text-cyan-800">
          Allow microphone…
        </span>
      ) : (
        <IconButton
          label="Record voice note"
          disabled={disabled}
          onClick={() => void start()}
          className="text-cyan-800"
        >
          <Mic className={iconSize} />
        </IconButton>
      )}
      {error && (
        <p role="alert" className="text-sm text-rose-700">
          {error}
        </p>
      )}
    </div>
  );
}
