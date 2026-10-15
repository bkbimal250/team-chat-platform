"use client";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Download, X } from "lucide-react";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { Attachment, downloadMedia } from "./api";

export function MediaViewer({
  images,
  initial,
  initialUrl,
  token,
  onClose,
}: {
  images: Attachment[];
  initial: Attachment;
  initialUrl: string;
  token: string;
  onClose: () => void;
}) {
  const [selected, setSelected] = useState(initial);
  const [url, setUrl] = useState(initialUrl);
  const [failed, setFailed] = useState(false);
  const panel = useRef<HTMLDivElement>(null);
  const position = images.findIndex(
    (image) => image.media_id === selected.media_id,
  );
  function next(direction: number) {
    const image = images[position + direction];
    if (image) {
      setSelected(image);
      setUrl(image.media_id === initial.media_id ? initialUrl : "");
      setFailed(false);
    }
  }
  useEffect(() => {
    if (selected.media_id === initial.media_id) return;
    let active = true;
    downloadMedia(selected.media_id, token)
      .then((value) => {
        if (active) setUrl(value);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [selected.media_id, initial.media_id, token]);
  useEffect(() => {
    panel.current?.querySelector<HTMLButtonElement>("button")?.focus();
  }, []);
  return (
    <div
      ref={panel}
      role="dialog"
      aria-modal="true"
      aria-label="Image viewer"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          onClose();
        }
        if (event.key === "ArrowLeft") next(-1);
        if (event.key === "ArrowRight") next(1);
        if (event.key === "Tab") {
          const items = Array.from(
            panel.current?.querySelectorAll<HTMLElement>(
              "button:not(:disabled),a[href]",
            ) || [],
          );
          const index = items.indexOf(document.activeElement as HTMLElement);
          event.preventDefault();
          items[
            (index + (event.shiftKey ? -1 : 1) + items.length) % items.length
          ]?.focus();
        }
      }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-slate-950/95 p-4 text-white"
    >
      <IconButton
        label="Close viewer"
        onClick={onClose}
        className="self-end bg-aurora-surface text-aurora-text"
      >
        <X className={iconSize} />
      </IconButton>
      {failed ? (
        <p role="alert">Image unavailable.</p>
      ) : url ? (
        <Image
          unoptimized
          width={1280}
          height={960}
          src={url}
          alt={selected.filename}
          className="max-h-[75vh] max-w-full object-contain"
          onError={() => setFailed(true)}
        />
      ) : (
        <p role="status">Loading image…</p>
      )}
      <p>{selected.filename}</p>
      <div className="flex items-center gap-3">
        <IconButton
          label="Previous image"
          disabled={position <= 0}
          onClick={() => next(-1)}
          className="text-white disabled:opacity-40"
        >
          <ChevronLeft className={iconSize} />
        </IconButton>
        <IconButton
          label="Next image"
          disabled={position < 0 || position >= images.length - 1}
          onClick={() => next(1)}
          className="text-white disabled:opacity-40"
        >
          <ChevronRight className={iconSize} />
        </IconButton>
        {url && (
          <a
            href={url}
            download={selected.filename}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Download image"
            title="Download image"
            className="inline-flex items-center gap-1.5 rounded-lg p-2 hover:bg-white/10"
          >
            <Download className={iconSize} aria-hidden />
            <span className="text-sm">Download</span>
          </a>
        )}
      </div>
    </div>
  );
}
