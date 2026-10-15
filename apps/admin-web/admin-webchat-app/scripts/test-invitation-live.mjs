/** Real local browser/Gateway/Rabbit workflow. Never prints secrets or exception URLs. */
import { chromium } from "playwright";
import { readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { randomUUID, randomInt } from "node:crypto";
const root = path.resolve("../../.."), local = path.join(root, ".local");
const admin = "http://localhost:3000", web = "http://localhost:3001", gateway = "http://localhost:8008";
const results = {}; let step = "startup";
function check(name, ok) { step=name; results[name]=ok?"PASS":"FAIL"; console.log(name, results[name]); if (!ok) throw Error("Local live check failed"); }
async function api(route, token, method="GET", body) {
  const response = await fetch(gateway+route, {method, headers:{"Content-Type":"application/json", ...(token?{Authorization:"Bearer "+token}:{})}, body:body===undefined?undefined:JSON.stringify(body)});
  return {status:response.status, body:await response.json().catch(()=>null)};
}
async function until(callback) { for(let n=0;n<80;n++) { const result=await callback(); if(result) return result; await new Promise(resolve=>setTimeout(resolve,250)); } return null; }
const dirs=await readdir(path.join(process.env.LOCALAPPDATA,"ms-playwright"));
const cached=dirs.find(x=>x.startsWith("chromium-")&&!x.includes("headless"));
const browser=await chromium.launch({executablePath:path.join(process.env.LOCALAPPDATA,"ms-playwright",cached,"chrome-win/chrome.exe"),headless:true});
const a=await browser.newContext({viewport:{width:1440,height:1000}}), b=await browser.newContext({viewport:{width:1440,height:1000}});
const owner=await a.newPage(), employee=await b.newPage();
const frames={owner:[],employee:[]}; let critical=false;
function watch(page,name) { page.on("pageerror",()=>{critical=true;}); page.on("websocket",socket=>socket.on("framereceived",frame=>{try{frames[name].push(JSON.parse(String(frame.payload)));}catch{}})); }
watch(employee,"employee"); watch(owner,"owner");
let ownerTokens, employeeTokens, employeeProfile, invitation, branch, team, phone;
try {
  check("gateway_ready",(await api("/health/ready")).status===200);
  try { ownerTokens=JSON.parse(await readFile(path.join(local,"invitation-owner-session.json"),"utf8")); if((await api("/api/v1/auth/me",ownerTokens.access_token)).status!==200) ownerTokens=null; } catch { ownerTokens=null; }
  if(!ownerTokens) {
    step="owner_login"; await owner.goto(admin+"/login"); await owner.getByRole("textbox",{name:"Phone number"}).fill("+919000000001");
    const requested=owner.waitForResponse(r=>r.url().includes("/auth/otp/request")&&r.request().method()==="POST"); await owner.getByRole("button",{name:"Request code"}).click(); const request=await requested, challenge=await request.json();
    check("owner_real_development_otp",request.status()===202||request.status()===200);
    if(!challenge.development_code) throw Error("Development OTP required");
    await owner.getByRole("textbox",{name:"Verification code"}).fill(challenge.development_code);
    const verified=owner.waitForResponse(r=>r.url().includes("/auth/otp/verify")&&r.request().method()==="POST"); await owner.getByRole("button",{name:"Verify and sign in"}).click(); const response=await verified;
    check("owner_real_otp_login",response.status()===200); ownerTokens=await response.json(); await writeFile(path.join(local,"invitation-owner-session.json"),JSON.stringify(ownerTokens));
  } else {
    await owner.addInitScript(tokens=>sessionStorage.setItem("globalchat.admin.session",JSON.stringify(tokens)),ownerTokens);
    await owner.goto(admin+"/dashboard"); check("owner_existing_real_session",true);
  }
  await owner.getByRole("heading",{name:"Dashboard",exact:true}).waitFor(); check("owner_admin_dashboard",true);
  const suffix=randomUUID().slice(0,8), name="Employee "+suffix;
  phone="+9196"+String(randomInt(10000000,99999999));
  branch=(await api("/api/v1/branches/",ownerTokens.access_token,"POST",{name:"Invitation Branch "+suffix,code:"INV"+suffix,country:"IN"})); check("real_branch_created",branch.status===201); branch=branch.body;
  team=(await api("/api/v1/teams/",ownerTokens.access_token,"POST",{name:"Invitation Team "+suffix,branch_id:branch.id})); check("real_team_created",team.status===201); team=team.body;
  const roles=await api("/api/v1/roles/",ownerTokens.access_token); const role=roles.body.results.find(x=>x.kind==="MEMBER"); check("actual_member_role",Boolean(role));
  step="invite_form"; await owner.goto(admin+"/members"); await owner.getByRole("link",{name:"Invite Member",exact:true}).click(); await owner.getByRole("button",{name:"Invite Member",exact:true}).click();
  await owner.getByRole("textbox",{name:"Name",exact:true}).fill(name); await owner.getByRole("textbox",{name:"Phone Number"}).fill(phone);
  await owner.getByRole("combobox",{name:"Role",exact:true}).selectOption(role.id);
  // Resource choices are cursor-paged. Find this real target without inventing IDs.
  async function choose(label,id) { for(let n=0;n<100;n++) { const select=owner.getByRole("combobox",{name:label,exact:true}); if(await select.locator(`option[value="${id}"]`).count()) {await select.selectOption(id);return;} const container=select.locator("..").locator(".."); await container.getByRole("button",{name:"More choices"}).click(); await owner.waitForTimeout(250); } throw Error("Choice unavailable"); }
  await choose("Branch",branch.id); await choose("Team",team.id);
  const created=owner.waitForResponse(r=>r.url().endsWith("/api/v1/invitations/")&&r.request().method()==="POST"); await owner.getByRole("button",{name:"Create invitation"}).click(); const creation=await created; invitation=await creation.json();
  check("admin_create_invitation",creation.status()===201); check("invitation_pending",invitation.status==="PENDING"); check("hash_not_exposed",!invitation.token_hash);
  let link=await owner.getByRole("textbox",{name:"Development invitation link"}).inputValue(); check("development_local_link",new URL(link).origin===web&&link.includes("#invite="));
  const oldToken=new URLSearchParams(new URL(link).hash.slice(1)).get("invite");
  const rotated=owner.waitForResponse(r=>r.url().endsWith(`/invitations/${invitation.id}/resend/`)&&r.request().method()==="POST");
  await owner.getByRole("row").filter({hasText:name}).getByRole("button",{name:"Resend",exact:true}).click();
  const rotation=await rotated;const rotationBody=await rotation.json();check("admin_resend_ui",rotation.status()===200&&rotationBody.id===invitation.id);
  await owner.getByRole("textbox",{name:"Development invitation link"}).waitFor();link=await owner.getByRole("textbox",{name:"Development invitation link"}).inputValue();
  const oldLink=await api("/api/v1/auth/invitations/validate",null,"POST",{token:oldToken});check("old_token_rotated_invalid",oldLink.status===404);
  const raw=new URLSearchParams(new URL(link).hash.slice(1)).get("invite");
  const duplicate=await api("/api/v1/invitations/",ownerTokens.access_token,"POST",{recipient_name:name,recipient_phone:phone,intended_role_id:role.id}); check("duplicate_pending_rejected",duplicate.status===409);
  step="employee_join"; await employee.goto(link); await employee.getByText("Hello, "+name+".",{exact:true}).waitFor(); check("employee_company_validation",true); check("fragment_removed",!employee.url().includes(raw));
  const otpRequested=employee.waitForResponse(r=>r.url().endsWith("/auth/invitations/request")&&r.request().method()==="POST"); await employee.getByRole("button",{name:"Request invitation code"}).click(); const otpResponse=await otpRequested, challenge=await otpResponse.json(); check("employee_development_otp_request",otpResponse.status()===202&&Boolean(challenge.development_code));
  await employee.getByRole("textbox",{name:"Verification code"}).fill(challenge.development_code);
  const accepted=employee.waitForResponse(r=>r.url().endsWith("/auth/invitations/verify")&&r.request().method()==="POST"); await employee.getByRole("button",{name:"Verify and join workspace"}).click(); const acceptedResponse=await accepted; employeeTokens=await acceptedResponse.json();
  check("employee_otp_verified",acceptedResponse.status()===200); check("normal_session_issued",Boolean(employeeTokens.access_token&&employeeTokens.refresh_token));
  await employee.waitForURL(web+"/"); await employee.getByRole("button",{name:"Chats",exact:true}).waitFor(); check("employee_chat_redirect",true);
  employeeProfile=await api("/api/v1/users/me",employeeTokens.access_token); check("employee_profile",employeeProfile.status===200&&employeeProfile.body.display_name===name);
  const member=await api(`/api/v1/members/${employeeTokens.member_id}/`,ownerTokens.access_token); check("membership_active",member.status===200&&member.body.status==="ACTIVE"); check("member_role_binding",member.body.roles.includes(role.name)); check("branch_team_binding",member.body.branches.includes(branch.name)&&member.body.teams.includes(team.name)); check("phone_masked_member_view",member.body.recipient_phone_masked&&!JSON.stringify(member.body).includes(phone));
  const listed=await api(`/api/v1/invitations/${invitation.id}/`,ownerTokens.access_token); check("accepted_timestamp",listed.body.status==="ACCEPTED"&&Boolean(listed.body.accepted_at));
  const replay=await api("/api/v1/auth/invitations/validate",null,"POST",{token:raw}); check("accepted_link_replay_rejected",replay.status===410||replay.status===409);
  step="admin_member_list"; await owner.goto(admin+"/members"); await owner.getByText(name,{exact:true}).waitFor(); check("admin_member_list_updated",true);
  const previous=await api("/api/v1/conversations",ownerTokens.access_token); if(previous.body.length) { const denied=await api(`/api/v1/conversations/${previous.body[0].id}`,employeeTokens.access_token); check("private_conversation_access_denied",denied.status===403||denied.status===404); }
  const ownerChat=await a.newPage(); watch(ownerChat,"owner"); await ownerChat.addInitScript(tokens=>sessionStorage.setItem("globalchat.session",JSON.stringify(tokens)),ownerTokens); await ownerChat.goto(web+"/"); await ownerChat.getByText("Connected",{exact:true}).waitFor();
  const people=await until(async()=>{const response=await api("/api/v1/users/search?q="+encodeURIComponent(name),ownerTokens.access_token);return response.status===200&&response.body.users.some(x=>x.member_id===employeeTokens.member_id);}); check("workspace_people_member_resolution",Boolean(people));
  step="new_direct_ui"; await ownerChat.getByRole("button",{name:"+ New conversation",exact:true}).click(); await ownerChat.getByRole("textbox",{name:"Search people"}).fill(name); await ownerChat.getByRole("button",{name:"Search",exact:true}).click();
  const direct=ownerChat.waitForResponse(r=>r.url().endsWith("/conversations/direct")&&r.request().method()==="POST"); await ownerChat.getByRole("button",{name:"Chat",exact:true}).click(); const directResponse=await direct, conversation=await directResponse.json(); check("direct_creation_ui",[200,201].includes(directResponse.status()));
  check("messaging_projection_ready",Boolean(await until(async()=>(await api(`/api/v1/conversations/${conversation.id}/messages`,ownerTokens.access_token)).status===200)));
  await ownerChat.getByRole("textbox",{name:"Write a message"}).waitFor();
  await employee.getByRole("button",{name:"Refresh conversations",exact:true}).click(); await employee.getByRole("button",{name:/Direct conversation/}).waitFor();
  const outbound="Owner hello "+suffix; const sent=ownerChat.waitForResponse(r=>r.url().endsWith(`/conversations/${conversation.id}/messages`)&&r.request().method()==="POST"); await ownerChat.getByRole("textbox",{name:"Write a message"}).fill(outbound); await ownerChat.getByRole("textbox",{name:"Write a message"}).press("Enter"); const sentResponse=await sent; const message=await sentResponse.json(); if(![200,201].includes(sentResponse.status())) console.log("Send error category",sentResponse.status(),message.error?.code ?? message.code ?? "UNKNOWN"); check("owner_to_employee_text_ui",[200,201].includes(sentResponse.status()));
  check("rabbit_realtime_new_message",Boolean(await until(()=>frames.employee.some(x=>x.type==="message.created.v1"&&x.payload?.conversation_id===conversation.id))));
  const summary=await until(async()=>{const rows=(await api("/api/v1/conversations",employeeTokens.access_token)).body;const row=rows.find(x=>x.id===conversation.id);return row?.unread_count>0&&row.last_message_preview===outbound?row:null;}); check("durable_unread_preview",Boolean(summary));
  await employee.getByRole("button",{name:"Refresh conversations",exact:true}).click(); await employee.getByRole("button",{name:/Direct conversation/}).click(); await employee.getByRole("textbox",{name:"Write a message"}).waitFor(); await employee.getByText(outbound,{exact:true}).first().waitFor(); check("employee_received_message_ui",true);
  check("delivery_receipt",Boolean(await until(()=>frames.owner.some(x=>x.type==="message.delivered.v1"&&x.payload?.conversation_id===conversation.id)))); check("read_receipt",Boolean(await until(()=>frames.owner.some(x=>x.type==="message.read.v1"&&x.payload?.conversation_id===conversation.id))));
  const read=await until(async()=>{const rows=(await api("/api/v1/conversations",employeeTokens.access_token)).body;return rows.find(x=>x.id===conversation.id)?.unread_count===0;}); check("read_clears_unread",Boolean(read));
  step="typing_ui"; await ownerChat.getByRole("textbox",{name:"Write a message"}).fill("typing check"); await employee.getByText("Someone is typing…",{exact:true}).waitFor(); check("typing_ui",true); await ownerChat.getByRole("textbox",{name:"Write a message"}).fill("");
  const inbound="Employee hello "+suffix; const reply=employee.waitForResponse(r=>r.url().endsWith(`/conversations/${conversation.id}/messages`)&&r.request().method()==="POST"); await employee.getByRole("textbox",{name:"Write a message"}).fill(inbound); await employee.getByRole("textbox",{name:"Write a message"}).press("Enter"); check("employee_to_owner_text_ui",[200,201].includes((await reply).status())); await ownerChat.getByText(inbound,{exact:true}).first().waitFor(); check("owner_received_realtime_ui",true);
  step="employee_logout"; await employee.getByRole("button",{name:"Logout",exact:true}).click(); await employee.getByRole("button",{name:"Confirm",exact:true}).click(); await employee.getByRole("button",{name:"Continue with phone"}).waitFor(); check("employee_logout",true);
  await employee.getByRole("button",{name:"Continue with phone"}).click(); await employee.getByRole("textbox",{name:"Phone number"}).fill(phone.slice(3)); const returning=employee.waitForResponse(r=>r.url().endsWith("/auth/otp/request")&&r.request().method()==="POST"); await employee.getByRole("button",{name:"Send verification code"}).click(); const returningResponse=await returning, returningChallenge=await returningResponse.json(); check("returning_phone_otp",returningResponse.status()===202||returningResponse.status()===200);
  await employee.getByRole("textbox",{name:/Verification code/}).fill(returningChallenge.development_code); const returned=employee.waitForResponse(r=>r.url().endsWith("/auth/otp/verify")&&r.request().method()==="POST"); await employee.getByRole("button",{name:"Continue securely"}).click(); const returnedResponse=await returned, restored=await returnedResponse.json(); check("returning_login",returnedResponse.status()===200); check("same_membership_restored",restored.member_id===employeeTokens.member_id); const restoredProfile=await api("/api/v1/users/me",restored.access_token); check("same_profile_restored",restoredProfile.body.user_id===employeeProfile.body.user_id);
  const memberships=await api("/api/v1/members/?page_size=50",ownerTokens.access_token);check("no_duplicate_membership",memberships.body.results.filter(x=>x.id===restored.member_id).length===1);
  const memberDenied=await api("/api/v1/invitations/",restored.access_token,"POST",{recipient_name:"Unauthorized",recipient_phone:"+919000000007",intended_role_id:role.id});check("normal_member_invite_denied",memberDenied.status===403);
  const revokedName="Revoked "+suffix;const other=await api("/api/v1/invitations/",ownerTokens.access_token,"POST",{recipient_name:revokedName,recipient_phone:"+9195"+String(randomInt(10000000,99999999)),intended_role_id:role.id}); check("revoke_fixture_pending",other.status===201&&other.body.status==="PENDING");
  step="revoke_ui";await owner.goto(admin+"/invitations");const row=owner.getByRole("row").filter({hasText:revokedName});await row.getByRole("button",{name:"Revoke",exact:true}).click();const revoked=owner.waitForResponse(r=>r.url().endsWith(`/invitations/${other.body.id}/revoke/`)&&r.request().method()==="POST");await owner.getByRole("button",{name:"Confirm revoke"}).click();check("admin_revoke_ui",(await revoked).status()===200);
  const deniedPage=await b.newPage();await deniedPage.goto(other.body.development_url);await deniedPage.getByRole("alert").filter({hasText:"revoked"}).waitFor();check("revoked_join_denied",true);const revokedRecord=await api(`/api/v1/invitations/${other.body.id}/`,ownerTokens.access_token);check("revoked_no_membership",revokedRecord.body.status==="REVOKED"&&!revokedRecord.body.accepted_member);
  await writeFile(path.join(local,"invitation-live-check.json"),JSON.stringify({invitation_id:invitation.id,organization_id:ownerTokens.organization_id,identity_id:member.body.user_id,user_id:employeeProfile.body.user_id,member_id:employeeTokens.member_id,branch_id:branch.id,team_id:team.id,revoked_invitation_id:other.body.id},null,2));
  check("browser_no_uncaught_errors",!critical);
} catch { console.log("Stopped at",step,"(details redacted)"); results[step]="FAIL"; process.exitCode=1; }
finally {await writeFile(path.join(local,"invitation-live-results.json"),JSON.stringify(results,null,2));await browser.close();}
