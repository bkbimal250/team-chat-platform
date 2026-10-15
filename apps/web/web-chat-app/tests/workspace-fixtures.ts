import type { Tokens } from "@/workspace/lib/api/contracts";
export const tokens: Tokens = {
  access_token: "test-access",
  refresh_token: "test-refresh",
  member_id: "member-a",
  organization_id: "org-a",
  device_id: "device-a",
  session_id: "session-a",
  expires_in: 900,
};
export const page = (results: object[] = []) => ({
  results,
  next: null,
  previous: null,
});
export function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
