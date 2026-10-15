"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect,useState } from "react";
import { Menu } from "lucide-react";
import { iconSize } from "@/components/ui/icon-button";
import { useAuth } from "./features/auth/auth-provider";
import { useResource } from "./lib/api/use-resource";
import { refreshAdmin } from "./lib/realtime/refresh";
import { Modal } from "./components/ui/modal";
import type { Organization } from "./lib/api/contracts";
export function WorkspaceFrame({children}:{children:React.ReactNode}){
 const auth=useAuth(),path=usePathname();const [open,setOpen]=useState(false); const [online,setOnline]=useState(true);
 const company=useResource<Organization>("/api/v1/organizations/current/",auth.status==="ready"&&auth.permissions.has("organization.view"));
 useEffect(()=>{
  if(auth.status!=="ready")return;
  const sync=()=>{setOnline(navigator.onLine);if(navigator.onLine&&document.visibilityState==="visible")refreshAdmin();}; const offline=()=>setOnline(false);
  const timer=setInterval(sync,30000);window.addEventListener("focus",sync);window.addEventListener("online",sync);window.addEventListener("offline",offline);
  return()=>{clearInterval(timer);window.removeEventListener("focus",sync);window.removeEventListener("online",sync);window.removeEventListener("offline",offline);};
 },[auth.status,auth.session?.organization_id]);
 const personal=auth.status==="ready"&&!auth.session?.organization_id;
 const title=personal?"Personal Account":"Company Workspace";
 const links=[["/","Chat",""],["/contacts","Contacts",""],["/workspace","Overview",""],["/workspace/members","Members","member.view"],["/workspace/teams","Teams","team.view"],["/workspace/branches","Branches","branch.view"],["/workspace/invitations","Invitations","invitation.view"],["/workspace/company","Company","organization.view"],["/workspace/roles","Roles","role.manage"],["/workspace/profile","Profile",""],["/workspace/devices","Devices",""],["/workspace/settings","Settings",""]];
 const navigation=<><p className="text-xl font-bold">GlobalChat</p><div className="my-5 rounded-xl bg-aurora-surface/10 p-3"><span className="mr-2 inline-grid size-9 place-items-center rounded-lg bg-aurora-primary">{(company.data?.display_name||company.data?.name||"G").slice(0,1)}</span><span className="break-words text-sm">{company.data?.display_name||company.data?.name||(personal?"Personal account":"Your workspace")}</span><p className="mt-2 text-xs text-white/70">{title}</p></div><nav aria-label="Workspace navigation" className="space-y-1">{links.filter(([href, ,permission])=>(!personal || href !== "/workspace")&&(!permission||auth.permissions.has(permission))).map(([href,label])=><Link key={href} href={href} onClick={()=>setOpen(false)} aria-current={path===href?"page":undefined} className={"block rounded-xl px-3 py-2 text-sm focus-visible:outline-2 "+(path===href?"bg-aurora-primary text-white":"text-white/80 hover:bg-aurora-surface/10")}>{label}</Link>)}</nav></>;
 if(auth.status==="loading")return <main role="status" className="p-8">Loading Company Workspace…</main>;
 if(auth.status==="anonymous")return <main className="p-8"><Link href="/login">Sign in to your workspace</Link></main>;
 if(auth.status==="error")return <main className="p-8"><p role="alert">{auth.error}</p><button onClick={()=>void auth.reload()} className="mt-4 rounded bg-aurora-primary p-3 text-white">Retry workspace authorization</button><Link className="ml-4 underline" href="/">Return to chat</Link></main>;
 return <div className="flex h-dvh min-w-0 bg-aurora-background text-aurora-text"><aside className="hidden w-56 shrink-0 overflow-y-auto bg-aurora-sidebar p-4 text-white lg:block">{navigation}</aside><div className="flex min-w-0 flex-1 flex-col"><header className="flex shrink-0 items-center justify-between border-b border-aurora-border bg-aurora-surface px-4 py-3"><button aria-label="Open workspace navigation" title="Menu" className="rounded p-2 lg:hidden" onClick={()=>setOpen(true)}><Menu className={iconSize} aria-hidden /></button><p className="text-sm font-semibold">{title}</p><span className="text-sm text-aurora-muted">{auth.profile?.display_name}</span></header>{!online&&<p role="status" className="bg-amber-100 px-4 py-2 text-sm text-amber-900">You’re offline. Workspace updates resume when your connection returns.</p>}<div className="min-h-0 min-w-0 flex-1 overflow-auto">{personal&&path?.startsWith("/workspace")&&!(["/workspace/profile","/workspace/settings","/workspace/devices"].includes(path))?<main className="p-6"><h1 className="text-2xl font-semibold">Company membership required</h1><p className="mt-3">This account has no active company context. Your personal profile, settings and devices are available.</p><Link href="/" className="mt-4 inline-block underline">Return to personal account</Link></main>:children}</div></div><Modal open={open} title={title} onClose={()=>setOpen(false)}><div className="rounded-xl bg-aurora-sidebar p-4 text-white">{navigation}</div></Modal></div>;
}
