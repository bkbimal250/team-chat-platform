"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import { safeAbort } from "@/workspace/lib/api/abort";
import { apiRequest } from "@/workspace/lib/api/client";
export function Avatar({
  name,
  mediaId,
  size = "md",
  className = "",
}: {
  name: string;
  mediaId?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const [photo, setPhoto] = useState<{id:string;url:string} | null>(null);
  useEffect(() => {
    if (!mediaId) return;
    const abort = new AbortController(); let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const result = await apiRequest<{download_url:string;expires_in:number}>(`/api/v1/users/profile-photos/${mediaId}`, {signal:abort.signal});
        if (abort.signal.aborted) return;
        setPhoto({id:mediaId!,url:result.download_url});
        timer = setTimeout(refresh, Math.max(1000, result.expires_in * 1000));
      } catch { if (!abort.signal.aborted) setPhoto(null); }
    }
    timer = setTimeout(refresh, 0);
    return () => {
      safeAbort(abort);
      clearTimeout(timer);
    };
  }, [mediaId]);
  const sizes = { sm: "size-8 text-xs", md: "size-10 text-sm", lg: "size-12 text-base" };
  return (
    <span
      className={`relative overflow-hidden grid shrink-0 place-items-center rounded-full bg-aurora-primary/15 font-semibold text-aurora-primary dark:bg-aurora-primary/25 ${sizes[size]} ${className}`}
      aria-hidden
    >
      {photo && photo.id === mediaId ? <Image src={photo.url} alt="" fill unoptimized className="object-cover" onError={()=>setPhoto(null)}/> : (name || "?").slice(0, 1).toUpperCase()}
    </span>
  );
}
