"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { isAbortError, safeAbort } from "@/workspace/lib/api/abort";
import { apiRequest } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Avatar } from "@/components/ui/avatar";

type PhotoProfile = { display_name?: string; avatar_media_id?: string | null; avatar_expires_at?: string | null };
export function ProfilePhotoSettings({ token }: { token: string }) {
  const [profile, setProfile] = useState<PhotoProfile>({});
  const [file, setFile] = useState<Blob | null>(null);
  const [preview, setPreview] = useState("");
  const [duration, setDuration] = useState("always");
  const [hours, setHours] = useState("24");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  useEffect(() => {
    const abort = new AbortController();
    void apiRequest<PhotoProfile>("/api/v1/users/me", { signal: abort.signal }, token).then(row => {
      if (!abort.signal.aborted) setProfile(row);
    }).catch((e) => {
      if (!abort.signal.aborted && !isAbortError(e))
        setError("Profile picture could not be loaded.");
    });
    return () => safeAbort(abort);
  }, [token]);
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    const timer = setTimeout(() => setPreview(url), 0);
    return () => { clearTimeout(timer); URL.revokeObjectURL(url); };
  }, [file]);
  async function selectFile(selected?: File) {
    if (!selected) return;
    setError(""); setStatus(""); setBusy(true);
    try {
      if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type) || selected.size > 10 * 1024 * 1024)
        throw Error("Choose a JPEG, PNG or WebP image smaller than 10 MB.");
      const bitmap = await createImageBitmap(selected);
      try {
        const canvas = document.createElement("canvas"); canvas.width = canvas.height = 512;
        const context = canvas.getContext("2d"); if (!context) throw Error("Image processing is unavailable.");
        const side = Math.min(bitmap.width, bitmap.height);
        context.fillStyle = "#ffffff"; context.fillRect(0, 0, 512, 512);
        context.drawImage(bitmap, (bitmap.width-side)/2, (bitmap.height-side)/2, side, side, 0, 0, 512, 512);
        const image = await new Promise<Blob>((resolve, reject) => canvas.toBlob(blob => blob ? resolve(blob) : reject(Error("Image processing failed.")), "image/jpeg", 0.88));
        setFile(image);
      } finally { bitmap.close(); }
    } catch (e) { setError(e instanceof Error ? e.message : "This image could not be opened."); }
    finally { setBusy(false); }
  }
  async function save() {
    const durationHours = duration === "always" ? null : duration === "24" ? 24 : Number(hours);
    if (durationHours !== null && (!Number.isInteger(durationHours) || durationHours < 1 || durationHours > 8760)) {
      setError("Enter a whole number of hours from 1 to 8760."); return;
    }
    setBusy(true); setError(""); setStatus("");
    try {
      let mediaId = profile.avatar_media_id;
      if (file) {
        const upload = await apiRequest<{media_id:string;upload_url:string;required_headers:Record<string,string>}>("/api/v1/media/profile-photos/uploads", {method:"POST",body:JSON.stringify({mime_type:file.type,size_bytes:file.size})}, token);
        const response = await fetch(upload.upload_url, {method:"PUT",headers:upload.required_headers,body:file});
        if (!response.ok) throw Error("Photo upload failed. Please retry.");
        await apiRequest(`/api/v1/media/profile-photos/${upload.media_id}/complete`, {method:"POST"}, token);
        mediaId = upload.media_id;
      }
      if (!mediaId) throw Error("Choose a profile picture first.");
      const row = await apiRequest<PhotoProfile>("/api/v1/users/me/photo", {method:"PUT",body:JSON.stringify({media_id:mediaId,duration_hours:durationHours})},token);
      setProfile(row); setFile(null); setPreview(""); setStatus("Profile picture saved.");
      window.dispatchEvent(new Event("globalchat:profile-updated"));
    } catch(e) { setError(e instanceof Error ? e.message : "Photo was not saved."); }
    finally {setBusy(false);}
  }
  async function remove() {
    setBusy(true); setError("");
    try {
      setProfile(await apiRequest<PhotoProfile>("/api/v1/users/me/photo",{method:"DELETE"},token));
      setFile(null); setPreview(""); setStatus("Profile picture removed.");
      window.dispatchEvent(new Event("globalchat:profile-updated"));
    } catch {setError("Photo could not be removed.");} finally {setBusy(false);}
  }
  return <section aria-label="Profile picture" className="mb-6 space-y-4 rounded-2xl border border-aurora-border bg-aurora-surface p-4">
    <h2 className="font-semibold">Profile picture</h2>
    <div className="flex items-center gap-4">
      {file && preview ? <Image src={preview} alt="New profile picture preview" width={80} height={80} unoptimized className="size-20 rounded-full object-cover"/> : <Avatar name={profile.display_name ?? "You"} mediaId={profile.avatar_media_id} className="size-20"/>}
      <label className="text-sm">Choose picture<input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={e=>{ void selectFile(e.target.files?.[0]); e.target.value=""; }} className="mt-2 block w-full text-sm"/></label>
    </div>
    <p className="text-xs text-aurora-muted">Square preview, private storage. Images are resized and photo metadata is removed before upload.</p>
    <label className="block text-sm">Keep picture for<select aria-label="Picture duration" value={duration} disabled={busy} onChange={e=>setDuration(e.target.value)} className="mt-1 block w-full rounded-xl border border-aurora-border bg-aurora-surface p-2"><option value="always">Always</option><option value="24">24 hours</option><option value="custom">Custom hours</option></select></label>
    {duration === "custom" && <label className="block text-sm">Custom hours<input aria-label="Custom hours" type="number" min={1} max={8760} step={1} value={hours} disabled={busy} onChange={e=>setHours(e.target.value)} className="mt-1 block w-full rounded-xl border border-aurora-border bg-aurora-surface p-2"/></label>}
    {profile.avatar_media_id && <p className="text-xs text-aurora-muted">{profile.avatar_expires_at ? `Current picture expires ${new Date(profile.avatar_expires_at).toLocaleString()}.` : "Current picture is kept until you change or remove it."}</p>}
    <p className="text-xs text-aurora-muted">Timed pictures return to initials when they expire. Saving a duration starts it from now.</p>
    <AlertBanner message={error}/>{status && <p role="status" className="text-sm">{status}</p>}
    <div className="flex gap-2"><Button type="button" variant="primary" disabled={busy || (!file && !profile.avatar_media_id)} onClick={()=>void save()}>{busy ? "Saving…" : "Save picture"}</Button><Button type="button" disabled={busy || !profile.avatar_media_id} onClick={()=>void remove()}>Remove picture</Button></div>
  </section>;
}
