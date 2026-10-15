import { act,render,screen } from "@testing-library/react";
import { expect,it,vi } from "vitest";
import { AuthProvider,useAuth } from "@/workspace/features/auth/auth-provider";
import { saveSession,clearSession } from "@/lib/auth/session";
function Probe(){const auth=useAuth();return <p>{auth.status}:{auth.permissions.has("invitation.create")?"invite":"view"}</p>;}
function prepare(member:string,permissions:string[]){saveSession({access_token:`header.${btoa(JSON.stringify({org:"company",mid:member}))}.signature`,refresh_token:null});vi.stubGlobal("fetch",vi.fn(async(url:string)=>new Response(JSON.stringify(url.includes("auth/me")?{context:{organization_id:"company",member_id:member}}:url.includes("role-assignments")?{results:[{member,role:"role"}],next:null}:url.includes("/roles/")?{results:[{id:"role",permissions}],next:null}:{display_name:"Workspace user"}),{status:200,headers:{"Content-Type":"application/json"}})));}
it.each(["owner-a","owner-b","admin"])("loads %s capabilities from authoritative role assignments",async member=>{prepare(member,["member.view","invitation.create"]);render(<AuthProvider><Probe/></AuthProvider>);expect(await screen.findByText("ready:invite")).toBeTruthy();clearSession();});
it("a member cannot inherit an unassigned owner role",async()=>{prepare("member",["member.view"]);render(<AuthProvider><Probe/></AuthProvider>);expect(await screen.findByText("ready:view")).toBeTruthy();clearSession();});
it("fails closed when backend rejects tenant authorization",async()=>{prepare("member",[]);vi.stubGlobal("fetch",vi.fn(async()=>new Response(JSON.stringify({error:{code:"FORBIDDEN",message:"Access denied."}}),{status:403})));render(<AuthProvider><Probe/></AuthProvider>);expect(await screen.findByText("error:view")).toBeTruthy();clearSession();});

it("removes protected workspace state when the session expires",async()=>{prepare("member",["member.view"]);render(<AuthProvider><Probe/></AuthProvider>);await screen.findByText("ready:view");act(()=>{clearSession();window.dispatchEvent(new Event("globalchat:session-expired"));});expect(screen.getByText("anonymous:view")).toBeTruthy();});
