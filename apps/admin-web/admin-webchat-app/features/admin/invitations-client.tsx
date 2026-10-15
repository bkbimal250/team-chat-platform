"use client";
import Link from "next/link";
import { useState } from "react";
import { useAuth } from "@/features/auth/auth-provider";
import { apiRequest, gatewayPath } from "@/lib/api/client";
import { useResource } from "@/lib/api/use-resource";
import type { Branch, Team, Role, CursorPage } from "@/lib/api/contracts";
import { DataTable } from "@/components/data-table/data-table";
import { TableToolbar } from "@/components/data-table/table-toolbar";
import { TablePagination } from "@/components/data-table/table-pagination";
import { TableEmpty } from "@/components/data-table/table-empty";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/feedback/error-state";
import { refreshAdmin } from "@/lib/realtime/refresh";
import { StatusBadge } from "@/components/ui/status-badge";

type Invitation = { id: string; recipient_name: string; recipient_phone: string; recipient_email: string; intended_role_id: string; branch_id: string | null; team_id: string | null; status: string; expires_at: string; created_at?: string; development_url?: string };
type Form = { recipient_name: string; recipient_phone: string; recipient_email: string; intended_role_id: string; branch_id: string; team_id: string };
const empty: Form = { recipient_name: "", recipient_phone: "", recipient_email: "", intended_role_id: "", branch_id: "", team_id: "" };
export function maskPhone(phone: string) { return phone ? phone.slice(0, 3) + "â€¢".repeat(Math.max(0, phone.length - 7)) + phone.slice(-4) : "â€”"; }
export function invitationPayload(form: Form) {
  if (form.recipient_name.trim().length < 2 || (!!form.recipient_phone.trim() && !/^\+[1-9]\d{7,14}$/.test(form.recipient_phone.trim())) || !form.intended_role_id || !form.recipient_email.trim()) throw new Error("Enter an employee name, email and role.");
  return { ...form, recipient_name: form.recipient_name.trim(), recipient_phone: form.recipient_phone.trim(), recipient_email: form.recipient_email.trim(), branch_id: form.branch_id || null, team_id: form.team_id || null };
}
export function Selection({ resource, label, value, onChange, required = false }: { resource: "roles" | "branches" | "teams"; label: string; value: string; onChange: (value: string) => void; required?: boolean }) {
  const [cursor, setCursor] = useState<string | null>(null);
  const result = useResource<CursorPage<Role | Branch | Team>>(cursor ?? `/api/v1/${resource}/?page_size=50`);
  return <div><label className="block text-sm">{label}<select required={required} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 block w-full rounded border p-2"><option value="">{required ? "Choose a role" : "No assignment"}</option>{result.data?.results.filter((row) => !('status' in row) || row.status === "ACTIVE").map((row) => <option value={row.id} key={row.id}>{row.name}</option>)}</select></label>{result.error && <p role="alert">{result.error}</p>}{result.loading && <p role="status">Loading {label.toLowerCase()}…</p>}<div className="flex flex-wrap gap-2">{result.data?.previous && <Button type="button" variant="ghost" size="sm" onClick={() => setCursor(gatewayPath(result.data!.previous!))}>Previous choices</Button>}{result.data?.next && <Button type="button" variant="ghost" size="sm" onClick={() => setCursor(gatewayPath(result.data!.next!))}>More choices</Button>}</div></div>;
}
export function InvitationsClient() {
  const auth = useAuth();
  const [status, setStatus] = useState("");
  const [cursor, setCursor] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const invitations = useResource<CursorPage<Invitation>>(cursor ?? `/api/v1/invitations/?page_size=20${status ? `&status=${status}` : ""}`);
  const roles = useResource<CursorPage<Role>>("/api/v1/roles/?page_size=50", auth.permissions.has("role.view") || auth.permissions.has("role.manage"));
  const branches = useResource<CursorPage<Branch>>("/api/v1/branches/?page_size=50", auth.permissions.has("branch.view"));
  const teams = useResource<CursorPage<Team>>("/api/v1/teams/?page_size=50", auth.permissions.has("team.view"));
  const [detail,setDetail] = useState<Invitation | null>(null);
  const [creating, setCreating] = useState(false);
  const [revoke, setRevoke] = useState<Invitation | null>(null);
  const [form, setForm] = useState<Form>(empty);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [developmentUrl, setDevelopmentUrl] = useState("");
  const [notice, setNotice] = useState("");
  async function action(path: string, body?: object) {
    if (busy) return;
    setBusy(true); setError(""); setDevelopmentUrl("");
    try {
      const result = await apiRequest<Invitation>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
      setDevelopmentUrl(result.development_url ?? ""); setNotice(result.status === "REVOKED" ? "Invitation revoked. Memberships are unchanged." : "Invitation ready. Local development delivery only.");
      setCreating(false); setRevoke(null); setForm(empty); invitations.reload(); refreshAdmin(["invitations","audit-logs"]);
    } catch (issue) { setError(issue instanceof Error ? issue.message : "Invitation action failed."); }
    finally { setBusy(false); }
  }
  if (!auth.permissions.has("invitation.view")) return <p role="alert">Your role does not grant invitation access.</p>;
  return <section className="space-y-4"><header><h1 className="text-2xl font-semibold">Invitations</h1><p className="text-sm text-slate-500">Email-bound employee access for your current organization.</p></header>
    {notice && <p role="status">{notice}</p>}{error && !creating && !revoke && <p role="alert" className="text-rose-700">{error}</p>}
    {developmentUrl && <Card className="space-y-2 p-4"><h2 className="font-semibold">Development-only invitation link</h2><p className="text-sm">Share this secret link privately with the invited employee. It is not saved in browser storage. Regenerating invalidates the previous link.</p><input aria-label="Development invitation link" readOnly value={developmentUrl} className="w-full rounded border p-2" /><Button variant="outline" onClick={async()=>{try{await navigator.clipboard.writeText(developmentUrl);setNotice("Private invitation link copied.");}catch{setError("Copy is unavailable. Select and copy the link manually.");}}}>Copy link</Button><Link href={developmentUrl} target="_blank" rel="noreferrer" className="text-indigo-700 underline">Open employee onboarding</Link></Card>}
    <Card className="p-4"><TableToolbar><label>Status <select aria-label="Invitation status" value={status} onChange={(e) => { setStatus(e.target.value); setCursor(null); setPage(1); }} className="rounded border p-2"><option value="">All statuses</option>{["PENDING", "ACCEPTED", "EXPIRED", "REVOKED"].map((value) => <option key={value}>{value}</option>)}</select></label><Button variant="outline" onClick={invitations.reload}>Refresh invitations</Button>{auth.permissions.has("invitation.create") && <Button onClick={() => { setCreating(true); setError(""); }}>Invite Member</Button>}</TableToolbar>
      {invitations.loading ? <p role="status">Loading invitations…</p> : invitations.error ? <ErrorState description={invitations.error} retry={invitations.reload}/> : invitations.data?.results.length ? <DataTable rows={invitations.data.results} getRowKey={(row) => row.id} columns={[
        { header: "Employee", cell: (row) => row.recipient_name || "Legacy invitation" }, { header: "Email", cell: (row) => row.recipient_email || "—" }, { header: "Phone", cell: (row) => maskPhone(row.recipient_phone) }, { header: "Status", cell: (row) => <StatusBadge status={row.status} /> }, { header: "Role", cell: (row) => roles.data?.results.find(role=>role.id === row.intended_role_id)?.name ?? row.intended_role_id }, { header: "Created", cell: (row) => row.created_at ? new Date(row.created_at).toLocaleDateString() : "—" }, { header: "Expires", cell: (row) => new Date(row.expires_at).toLocaleString() },
        { header: "Actions", cell: (row) => <div className="space-y-2"><Button variant="ghost" size="sm" onClick={()=>setDetail(row)}>Details</Button>{row.status === "PENDING" ? <div className="flex flex-wrap gap-2">{row.recipient_phone && auth.permissions.has("invitation.create") && <Button disabled={busy} variant="outline" size="sm" onClick={() => action(`/api/v1/invitations/${row.id}/resend/`)}>Regenerate link</Button>}{!row.recipient_phone && <span className="text-xs text-slate-500">Email-only link regeneration unavailable</span>}{auth.permissions.has("invitation.revoke") && <Button disabled={busy} variant="danger" size="sm" onClick={() => { setRevoke(row); setError(""); }}>Revoke</Button>}</div> : "No pending actions"}</div> }
      ]} /> : <TableEmpty />}
      <TablePagination page={page} total={page + (invitations.data?.next ? 1 : 0)} onPageChange={(n) => { const next = n > page ? invitations.data?.next : invitations.data?.previous; if (next) { setCursor(gatewayPath(next)); setPage(n); } }} />
    </Card>
    <Modal open={!!detail} title="Invitation details" onClose={()=>setDetail(null)}>{detail && <dl className="mt-4 space-y-3 text-sm">{Object.entries({Employee:detail.recipient_name,Email:detail.recipient_email,Phone:maskPhone(detail.recipient_phone),Role:roles.data?.results.find(row=>row.id===detail.intended_role_id)?.name ?? detail.intended_role_id,Branch:branches.data?.results.find(row=>row.id===detail.branch_id)?.name ?? detail.branch_id ?? "No assignment",Team:teams.data?.results.find(row=>row.id===detail.team_id)?.name ?? detail.team_id ?? "No assignment",Status:detail.status,Created:detail.created_at ? new Date(detail.created_at).toLocaleString() : "Not provided",Expires:new Date(detail.expires_at).toLocaleString()}).map(([label,value])=><div key={label}><dt className="text-xs font-medium text-slate-500">{label}</dt><dd className="break-words">{value || "—"}</dd></div>)}</dl>}</Modal>
    <Modal open={creating} onClose={() => { if (!busy) setCreating(false); }} title="Invite Member"><form className="space-y-4" onSubmit={(event) => { event.preventDefault(); try { void action("/api/v1/invitations/", invitationPayload(form)); } catch (issue) { setError(issue instanceof Error ? issue.message : "Check the invitation form."); } }}>
      <label className="block text-sm">Name<input autoFocus required minLength={2} maxLength={200} value={form.recipient_name} onChange={(e) => setForm({ ...form, recipient_name: e.target.value })} className="mt-1 block w-full rounded border p-2" /></label>
      <label className="block text-sm">Phone Number (optional)<input type="tel" placeholder="+91…" value={form.recipient_phone} onChange={(e) => setForm({ ...form, recipient_phone: e.target.value })} className="mt-1 block w-full rounded border p-2" /></label>
      <label className="block text-sm">Email<input required type="email" maxLength={254} value={form.recipient_email} onChange={(e) => setForm({ ...form, recipient_email: e.target.value })} className="mt-1 block w-full rounded border p-2" /></label>
      <Selection resource="roles" label="Role" required value={form.intended_role_id} onChange={(value) => setForm({ ...form, intended_role_id: value })} />
      <Selection resource="branches" label="Branch" value={form.branch_id} onChange={(value) => setForm({ ...form, branch_id: value })} />
      <Selection resource="teams" label="Team" value={form.team_id} onChange={(value) => setForm({ ...form, team_id: value })} />
      <p className="text-sm text-slate-500">The backend enforces role delegation and tenant ownership. No paid message is sent in local development.</p>{error && <p role="alert" className="text-rose-700">{error}</p>}<Button disabled={busy} type="submit">{busy ? "Creating…" : "Create invitation"}</Button>
    </form></Modal>
    <Modal open={Boolean(revoke)} title="Revoke invitation" onClose={() => { if (!busy) setRevoke(null); }}><p className="mb-4">Revoke the pending invitation for {revoke?.recipient_name}? The link will stop working. This does not remove an accepted member.</p>{error && <p role="alert">{error}</p>}<Button variant="danger" disabled={busy} onClick={() => action(`/api/v1/invitations/${revoke?.id}/revoke/`)}>Confirm revoke</Button></Modal>
  </section>;
}
