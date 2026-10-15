"use client";
import { createContext,useContext,useEffect,useState,useCallback } from "react";
import { apiRequest } from "@/workspace/lib/api/client";
import { collectPages } from "@/workspace/lib/api/pagination";
import { memberPermissions } from "./permissions";
import { readSession,saveSession,clearSession } from "@/workspace/lib/auth/session";
import type { Tokens,Role,RoleAssignment,UserProfile } from "@/workspace/lib/api/contracts";
type State={status:"loading"|"ready"|"anonymous"|"error";permissions:Set<string>;profile:UserProfile|null;session:Tokens|null;error:string};
const initial:State={status:"loading",permissions:new Set(),profile:null,session:null,error:""};
const Context=createContext<(State & {reload:()=>Promise<void>;login:(tokens:Tokens)=>Promise<void>;logout:()=>Promise<void>})|null>(null);
export function AuthProvider({children}:{children:React.ReactNode}){
 const [state,setState]=useState(initial);
 const reload=useCallback(async()=>{
  const session=readSession(); if(!session){setState({...initial,status:"anonymous"});return;}
  try {
   const me=await apiRequest<{context:{organization_id:string|null;member_id:string|null}}>("/api/v1/auth/me");
   if(Boolean(me.context?.organization_id) !== Boolean(me.context?.member_id)) throw Error("Invalid account context.");
   session.organization_id=me.context.organization_id;session.member_id=me.context.member_id;
   if(!session.organization_id){
    const profile=await apiRequest<UserProfile>("/api/v1/users/me");
    if(!readSession())return;
    setState({status:"ready",permissions:new Set(),profile,session:{...readSession()!,organization_id:null,member_id:null},error:""});return;
   }
   const [profile,roles,assignments]=await Promise.all([apiRequest<UserProfile>("/api/v1/users/me"),collectPages<Role>("/api/v1/roles/"),collectPages<RoleAssignment>("/api/v1/role-assignments/?member="+session.member_id)]);
   if(!readSession())return;
   setState({status:"ready",permissions:memberPermissions(session.member_id!,roles,assignments),profile,session:{...readSession()!,organization_id:me.context.organization_id,member_id:me.context.member_id},error:""});
  } catch(error){setState({...initial,status:readSession()?"error":"anonymous",session:readSession(),error:error instanceof Error?error.message:"Workspace authorization unavailable."});}
 },[]);
 useEffect(()=>{const timer=setTimeout(()=>void reload(),0);const expired=()=>setState({...initial,status:"anonymous"});window.addEventListener("globalchat:session-expired",expired);const updated=()=>void reload();window.addEventListener("globalchat:profile-updated",updated);return()=>{clearTimeout(timer);window.removeEventListener("globalchat:profile-updated",updated);window.removeEventListener("globalchat:session-expired",expired);};},[reload]);
 return <Context.Provider value={{...state,reload,login:async tokens=>{saveSession(tokens);await reload();},logout:async()=>{await apiRequest("/api/v1/auth/logout",{method:"POST",body:"{}"});clearSession();setState({...initial,status:"anonymous"});}}}>{children}</Context.Provider>;
}
export function useAuth(){const value=useContext(Context);if(!value)throw Error("Workspace provider required");return value;}

