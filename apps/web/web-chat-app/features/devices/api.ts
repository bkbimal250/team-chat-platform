import { apiRequest } from "@/lib/api/client";
export type Tokens = { access_token: string; refresh_token: string | null };
export type LinkedDevice = {
  id: string;
  platform: string;
  device_name: string;
  device_model: string | null;
  status: string;
  first_seen_at: string;
  last_seen_at: string;
  is_current: boolean;
};
export type QRChallenge = {
  challenge_id: string;
  payload: string;
  expires_at: string;
};
import { deviceInput } from "@/lib/auth/device";
export const deviceApi = {
  list: (token: string) =>
    apiRequest<LinkedDevice[]>("/api/v1/devices", {}, token),
  revoke: (id: string, token: string) =>
    apiRequest(`/api/v1/devices/${id}/revoke`, { method: "POST" }, token),
  logout: (token: string) =>
    apiRequest("/api/v1/auth/logout", { method: "POST" }, token),
  createQR: (signal?: AbortSignal) =>
    apiRequest<QRChallenge>("/api/v1/auth/qr/challenges", {
      method: "POST",
      body: JSON.stringify(deviceInput()),
      signal,
    }),
  qrStatus: (id: string, signal?: AbortSignal) =>
    apiRequest<{ status: string; expires_at: string }>(
      `/api/v1/auth/qr/challenges/${id}/status`,
      { signal },
    ),
  authorize: (id: string, secret: string, token: string) =>
    apiRequest(
      `/api/v1/auth/qr/challenges/${id}/authorize`,
      { method: "POST", body: JSON.stringify({ secret }) },
      token,
    ),
  consume: (id: string, secret: string, signal?: AbortSignal) =>
    apiRequest<Tokens>(`/api/v1/auth/qr/challenges/${id}/consume`, {
      method: "POST",
      body: JSON.stringify({ secret }),
      signal,
    }),
};
