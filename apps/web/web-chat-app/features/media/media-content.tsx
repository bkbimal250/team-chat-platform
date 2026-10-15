"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { Download, FileIcon } from "lucide-react";
import { iconSize } from "@/components/ui/icon-button";
import { Attachment, downloadMedia } from "./api";
import { MediaViewer } from "./media-viewer";

export function MediaContent({
  attachment,
  token,
  images = [attachment],
}: {
  attachment: Attachment;
  token: string;
  images?: Attachment[];
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState(false);
  const [viewer, setViewer] = useState(false);
  const [retry, setRetry] = useState(0);
  const trigger = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    let active = true;
    downloadMedia(attachment.media_id, token)
      .then((value) => {
        if (active) {
          setUrl(value);
          setError(false);
        }
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [attachment.media_id, token, retry]);
  if (error)
    return (
      <div role="alert">
        Media is unavailable.{" "}
        <button
          type="button"
          onClick={() => {
            setUrl("");
            setRetry((value) => value + 1);
          }}
        >
          Retry media
        </button>
      </div>
    );
  if (!url) return <p role="status">Loading attachment…</p>;
  const failed = () => {
    setUrl("");
    setError(true);
  };
  return (
    <div className="max-w-sm">
      {attachment.media_type === "image" ? (
        <>
          <button
            type="button"
            ref={trigger}
            aria-label={`View ${attachment.filename}`}
            title={`View ${attachment.filename}`}
            onClick={() => setViewer(true)}
          >
            <Image
              unoptimized
              width={640}
              height={480}
              src={url}
              alt={attachment.filename}
              className="max-h-64 rounded-xl object-contain"
              onError={failed}
            />
          </button>
          {viewer && (
            <MediaViewer
              images={images}
              initial={attachment}
              initialUrl={url}
              token={token}
              onClose={() => {
                setViewer(false);
                trigger.current?.focus();
              }}
            />
          )}
        </>
      ) : attachment.media_type === "video" ? (
        <video
          src={url}
          controls
          preload="metadata"
          className="max-h-80 max-w-full rounded-xl"
          onError={failed}
        />
      ) : attachment.media_type === "audio" ? (
        <audio
          src={url}
          controls
          preload="metadata"
          className="max-w-full"
          onError={failed}
        />
      ) : (
        <FileIcon className={`${iconSize} text-aurora-muted`} aria-hidden />
      )}
      <p className="break-all text-xs">
        {attachment.filename} · {(attachment.size_bytes / 1024).toFixed(1)} KB
      </p>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        download={attachment.filename}
        className="inline-flex items-center gap-1 text-xs underline"
      >
        <Download className="size-3.5 shrink-0" aria-hidden />
        Download attachment
      </a>
    </div>
  );
}
