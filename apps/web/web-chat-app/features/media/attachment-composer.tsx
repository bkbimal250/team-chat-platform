"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { chatApi, ChatMessage } from "@/features/chat/api";
import {
  acceptedTypes,
  Attachment,
  uploadAttachment,
  validateAttachment,
} from "./api";
import { Paperclip } from "lucide-react";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { VoiceRecorder } from "./voice-recorder";
export function AttachmentComposer({
  conversationId,
  token,
  onSent,
}: {
  conversationId: string;
  token: string;
  onSent: (message: ChatMessage) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [voice, setVoice] = useState(false);
  const [preview, setPreview] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [ready, setReady] = useState<Attachment | null>(null);
  const controller = useRef<AbortController | null>(null);
  const clientId = useRef("");
  const input = useRef<HTMLInputElement>(null);
  const locked = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      controller.current?.abort();
    };
  }, []);
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    const timer = setTimeout(() => setPreview(url), 0);
    return () => {
      clearTimeout(timer);
      URL.revokeObjectURL(url);
    };
  }, [file]);
  function select(files: readonly File[], isVoice = false) {
    try {
      validateAttachment(files);
      setFile(files[0]);
      setVoice(isVoice);
      setReady(null);
      setError("");
      setProgress(0);
      clientId.current = crypto.randomUUID();
    } catch (issue) {
      setError(issue instanceof Error ? issue.message : "Invalid attachment.");
    }
  }
  async function send() {
    if (!file || locked.current) return;
    locked.current = true;
    setBusy(true);
    setError("");
    const abort = new AbortController();
    controller.current = abort;
    try {
      const attachment =
        ready ||
        (await uploadAttachment(
          file,
          conversationId,
          token,
          abort.signal,
          (value) => {
            if (mounted.current) setProgress(value);
          },
        ));
      if (abort.signal.aborted || !mounted.current) return;
      setReady(attachment);
      const message = await chatApi.sendAttachment(
        conversationId,
        voice ? "VOICE" : attachment.media_type.toUpperCase(),
        attachment.media_id,
        clientId.current,
        token,
      );
      if (mounted.current) {
        onSent(message);
        setFile(null);
        setPreview("");
        setReady(null);
      }
    } catch (issue) {
      if (mounted.current)
        setError(
          abort.signal.aborted
            ? "Upload cancelled. You can retry."
            : issue instanceof Error
              ? issue.message
              : "Attachment was not sent. Please retry.",
        );
    } finally {
      locked.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  return (
    <div className="mb-2 space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          ref={input}
          type="file"
          accept={acceptedTypes}
          aria-label="Choose attachment"
          className="sr-only"
          disabled={busy || recording}
          onChange={(event) => {
            if (event.target.files?.length)
              select(Array.from(event.target.files));
            event.target.value = "";
          }}
        />
        <IconButton
          label="Attach"
          disabled={busy || recording}
          onClick={() => input.current?.click()}
          className="text-cyan-800"
        >
          <Paperclip className={iconSize} />
        </IconButton>
        <VoiceRecorder onBusyChange={setRecording}
          disabled={busy || !!file}
          onRecorded={(recording) => select([recording], true)}
        />
      </div>
      {file && (
        <section
          aria-label="Attachment preview"
          className="rounded-xl border border-aurora-border p-3"
        >
          {preview &&
            (file.type.startsWith("image/") ? (
              <Image unoptimized width={640} height={480}
                src={preview}
                alt="Attachment preview"
                className="max-h-40 rounded-lg"
              />
            ) : file.type.startsWith("video/") ? (
              <video
                src={preview}
                controls
                preload="metadata"
                className="max-h-40"
              />
            ) : file.type.startsWith("audio/") ? (
              <audio src={preview} controls />
            ) : null)}
          <p className="break-all text-sm">
            {file.name} · {file.type} · {(file.size / 1024).toFixed(1)} KB
          </p>
          {busy && (
            <div role="status">
              {ready ? "Confirming message…" : `Uploading ${progress}%`}
              <progress max={100} value={progress} className="block w-full" />
            </div>
          )}
          <div className="mt-2 flex gap-3">
            <button
              type="button"
              disabled={busy || recording}
              onClick={() => void send()}
              className="rounded-lg bg-cyan-700 px-3 py-2 text-white"
            >
              {error ? "Retry attachment" : "Send attachment"}
            </button>
            {busy ? (
              <button
                type="button"
                disabled={!!ready}
                onClick={() => controller.current?.abort()}
              >
                Cancel upload
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setFile(null);
                  setPreview("");
                  setReady(null);
                  setError("");
                }}
              >
                Delete attachment
              </button>
            )}
          </div>
        </section>
      )}
      {error && (
        <p role="alert" className="text-sm text-rose-700">
          {error}
        </p>
      )}
    </div>
  );
}
