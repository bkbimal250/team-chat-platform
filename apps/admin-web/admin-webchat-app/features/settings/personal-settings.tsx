"use client";
import { useState } from "react";
import { apiRequest } from "@/lib/api/client";
import { useResource } from "@/lib/api/use-resource";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/feedback/error-state";
export function PersonalSettings() {
 const prefs=useResource<{language:string;timezone:string;theme_preference:string}>("/api/v1/users/me/preferences");
 const privacy=useResource<{read_receipts_enabled:boolean;about_visibility:string}>("/api/v1/users/me/privacy");
 const [busy,setBusy]=useState(false),[error,setError]=useState(""),[notice,setNotice]=useState("");
 async function save(event:React.FormEvent<HTMLFormElement>,kind:"preferences"|"privacy") {
  event.preventDefault();if(busy)return;const form=new FormData(event.currentTarget);setBusy(true);setError("");setNotice("");
  try{const payload=kind==="privacy" ? {read_receipts_enabled:form.get("read_receipts_enabled")==="on",about_visibility:String(form.get("about_visibility"))} : {language:String(form.get("language")),timezone:String(form.get("timezone")),theme_preference:String(form.get("theme_preference"))};
   if(kind==="preferences") new Intl.DateTimeFormat("en",{timeZone:String(form.get("timezone"))});
   await apiRequest(`/api/v1/users/me/${kind}`,{method:"PATCH",body:JSON.stringify(payload)});setNotice("Personal settings saved.");if(kind==="preferences")prefs.reload();else privacy.reload();
  }catch(error){setError(error instanceof Error ? error.message : "Could not save settings.");}finally{setBusy(false);}
 }
 return <><Card className="p-5"><h2 className="font-semibold">Personal preferences</h2>{prefs.loading ? <p role="status">Loading preferences…</p> : prefs.error ? <ErrorState description={prefs.error} retry={prefs.reload}/> : prefs.data && <form key={JSON.stringify(prefs.data)} onSubmit={e=>void save(e,"preferences")} className="mt-4 space-y-4"><fieldset disabled={busy} className="grid gap-4 sm:grid-cols-2"><label className="text-sm">Language<input name="language" required maxLength={16} defaultValue={prefs.data.language} className="mt-1 block w-full rounded border p-2"/></label><label className="text-sm">Timezone<input name="timezone" required maxLength={64} defaultValue={prefs.data.timezone} className="mt-1 block w-full rounded border p-2"/></label><label className="text-sm">Account theme preference<select name="theme_preference" defaultValue={prefs.data.theme_preference} className="mt-1 block w-full rounded border p-2">{["SYSTEM","LIGHT","DARK"].map(value=><option key={value}>{value}</option>)}</select><span className="text-xs text-slate-500">Saved to your backend account preferences. This does not change the admin workspace color scheme.</span></label><div className="self-end"><Button type="submit">Save personal preferences</Button></div></fieldset></form>}</Card><Card className="p-5"><h2 className="font-semibold">Privacy</h2>{privacy.loading ? <p role="status">Loading privacy…</p> : privacy.error ? <ErrorState description={privacy.error} retry={privacy.reload}/> : privacy.data && <form key={JSON.stringify(privacy.data)} onSubmit={e=>void save(e,"privacy")} className="mt-4 space-y-4"><fieldset disabled={busy} className="space-y-4"><label className="flex gap-2 text-sm"><input name="read_receipts_enabled" type="checkbox" defaultChecked={privacy.data.read_receipts_enabled}/>Share read receipts</label><label className="block text-sm">About visibility<select name="about_visibility" defaultValue={privacy.data.about_visibility} className="mt-1 block w-full rounded border p-2">{["EVERYONE","ORGANIZATION","NOBODY"].map(value=><option key={value}>{value}</option>)}</select></label><Button type="submit">Save privacy settings</Button></fieldset></form>}</Card>{error && <p role="alert" className="text-sm text-rose-700">{error}</p>}{notice && <p role="status" className="text-sm text-emerald-700">{notice}</p>}</>;
}
