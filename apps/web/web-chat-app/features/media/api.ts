import { apiRequest } from "@/lib/api/client";
export type MediaCategory = "image" | "video" | "audio" | "document";
export type Attachment = {
  media_id: string;
  media_type: MediaCategory;
  mime_type: string;
  filename: string;
  size_bytes: number;
};
const allowed: Record<MediaCategory, readonly string[]> = {
  image: ["image/jpeg", "image/png", "image/webp"],
  video: ["video/mp4", "video/webm"],
  audio: ["audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"],
  document: ["application/pdf"],
};
export const acceptedTypes = Object.values(allowed).flat().join(",");
export function validateAttachment(files: readonly File[]): MediaCategory {
  if (files.length !== 1) throw new Error("Choose one attachment at a time.");
  const file = files[0];
  const category = (Object.keys(allowed) as MediaCategory[]).find((key) =>
    allowed[key].includes(file.type),
  );
  if (!category)
    throw new Error("Choose a supported image, video, audio file or PDF.");
  if (!file.size) throw new Error("The selected file is empty.");
  if (file.size > (category === "image" ? 10 * 1024 ** 2 : 5 * 1024 ** 3))
    throw new Error("The selected file exceeds the media size limit.");
  return category;
}
export async function inspectFile(file: File): Promise<void> {
  const bytes = await new Promise<Uint8Array>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer)); reader.onerror = () => reject(new Error("The selected file could not be read.")); reader.readAsArrayBuffer(file.slice(0, 12)); });
  const starts = (...signature: number[]) => signature.every((value, index) => bytes[index] === value);
  const ascii = String.fromCharCode(...bytes);
  const valid = file.type === "image/jpeg" ? starts(255,216,255) : file.type === "image/png" ? starts(137,80,78,71,13,10,26,10) : file.type === "image/webp" ? ascii.startsWith("RIFF") && ascii.slice(8) === "WEBP" : file.type === "application/pdf" ? ascii.startsWith("%PDF-") : file.type === "audio/ogg" ? ascii.startsWith("OggS") : file.type === "audio/wav" ? ascii.startsWith("RIFF") && ascii.slice(8) === "WAVE" : file.type.endsWith("webm") ? starts(26,69,223,163) : file.type === "video/mp4" ? ascii.slice(4,8) === "ftyp" : file.type === "audio/mpeg" ? ascii.startsWith("ID3") || (bytes[0] === 255 && (bytes[1] & 224) === 224) : false;
  if (!valid) throw new Error("The file appears corrupt or does not match its selected type.");
}
export function privateUrl(value: string): string {
  const url = new URL(value);
  if (url.protocol !== "https:")
    throw new Error("Secure media access is unavailable.");
  return url.href;
}
export function putFile(
  url: string,
  data: Blob,
  headers: Record<string, string>,
  signal: AbortSignal,
  progress: (value: number) => void,
): Promise<string | null> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const done = () => signal.removeEventListener("abort", abort);
    const abort = () => xhr.abort();
    xhr.open("PUT", privateUrl(url));
    xhr.timeout = 120000;
    Object.entries(headers).forEach(([key, value]) =>
      xhr.setRequestHeader(key, value),
    );
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) progress(event.loaded / event.total);
    };
    xhr.onload = () => {
      done();
      if (xhr.status >= 200 && xhr.status < 300)
        resolve(xhr.getResponseHeader("ETag"));
      else
        reject(
          new Error(
            xhr.status === 403
              ? "Upload authorization expired. Retry to obtain a new URL."
              : "Upload failed. Please retry.",
          ),
        );
    };
    xhr.onerror = () => {
      done();
      reject(new Error("Upload connection failed."));
    };
    xhr.ontimeout = () => {
      done();
      reject(new Error("Upload timed out. Please retry."));
    };
    xhr.onabort = () => {
      done();
      reject(new DOMException("Upload cancelled", "AbortError"));
    };
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) {
      done();
      reject(new DOMException("Upload cancelled", "AbortError"));
      return;
    }
    xhr.send(data);
  });
}
type Signing = {
  media_id: string;
  upload_strategy: "SIMPLE" | "MULTIPART";
  upload_url?: string;
  required_headers?: Record<string, string>;
  part_size?: number;
  part_count?: number;
};
export async function uploadAttachment(
  file: File,
  conversationId: string,
  token: string,
  signal: AbortSignal,
  progress: (percent: number) => void,
): Promise<Attachment> {
  const media_type = validateAttachment([file]);
  await inspectFile(file);
  if (signal.aborted) throw new DOMException("Upload cancelled", "AbortError");
  const signed = await apiRequest<Signing>(
    "/api/v1/media/uploads",
    {
      method: "POST",
      signal,
      body: JSON.stringify({
        conversation_id: conversationId,
        filename: file.name,
        mime_type: file.type,
        size_bytes: file.size,
        media_type,
      }),
    },
    token,
  );
  try {
    if (signed.upload_strategy === "MULTIPART") {
      if (!signed.part_count || !signed.part_size)
        throw new Error("Invalid upload authorization.");
      const parts: { part_number: number; etag: string }[] = [];
      for (let part = 1; part <= signed.part_count; part++) {
        const urls = await apiRequest<
          { part_number: number; presigned_url: string }[]
        >(
          `/api/v1/media/${signed.media_id}/multipart/parts`,
          {
            method: "POST",
            signal,
            body: JSON.stringify({ part_numbers: [part] }),
          },
          token,
        );
        const offset = (part - 1) * signed.part_size;
        const data = file.slice(offset, offset + signed.part_size);
        const etag = await putFile(
          urls[0].presigned_url,
          data,
          {},
          signal,
          (fraction) =>
            progress(
              Math.round(((offset + fraction * data.size) / file.size) * 100),
            ),
        );
        if (!etag)
          throw new Error(
            "Storage did not expose the upload confirmation. Check S3 CORS.",
          );
        parts.push({ part_number: part, etag });
      }
      await apiRequest(
        `/api/v1/media/${signed.media_id}/multipart/complete`,
        { method: "POST", signal, body: JSON.stringify({ parts }) },
        token,
      );
    } else {
      if (!signed.upload_url) throw new Error("Invalid upload authorization.");
      await putFile(
        signed.upload_url,
        file,
        signed.required_headers || {},
        signal,
        (fraction) => progress(Math.round(fraction * 100)),
      );
      await apiRequest(
        `/api/v1/media/${signed.media_id}/complete`,
        { method: "POST", signal },
        token,
      );
    }
    return {
      media_id: signed.media_id,
      media_type,
      filename: file.name.replace(/.*[\\/]/, ""),
      mime_type: file.type,
      size_bytes: file.size,
    };
  } catch (error) {
    if (signed.upload_strategy === "MULTIPART")
      await apiRequest(
        `/api/v1/media/${signed.media_id}/multipart`,
        { method: "DELETE" },
        token,
      ).catch(() => {});
    throw error;
  }
}
export async function downloadMedia(
  mediaId: string,
  token: string,
): Promise<string> {
  const result = await apiRequest<{ download_url: string }>(
    `/api/v1/media/${mediaId}/download`,
    {},
    token,
  );
  return privateUrl(result.download_url);
}
