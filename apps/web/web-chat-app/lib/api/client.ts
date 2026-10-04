import { deviceInput } from "@/lib/auth/device";
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status?: number,
  ) {
    super(message);
  }
}

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "https://api.michat.in";
type ErrorBody = {
  code?: string;
  message?: string;
  error?: { code?: string; message?: string };
};

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  accessToken?: string | null,
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(
      "NETWORK_ERROR",
      "We could not reach GlobalChat. Check your connection and try again.",
    );
  }
  const data = (await response.json().catch(() => ({}))) as ErrorBody;
  if (!response.ok) {
    const issue = data.error ?? data;
    if (response.status === 401 && accessToken && typeof window !== "undefined")
      window.dispatchEvent(new Event("globalchat:session-expired"));
    throw new ApiError(
      issue.code ?? "REQUEST_FAILED",
      issue.message ?? "Something went wrong. Please try again.",
      response.status,
    );
  }
  return data as T;
}

export const identityApi = {
  requestOtp: (phone_number: string) =>
    apiRequest<{ challenge_id: string | null; development_code?: string | null }>("/api/v1/auth/otp/request", {
      method: "POST",
      body: JSON.stringify({ phone_number, purpose: "LOGIN" }),
    }),
  verifyOtp: (challenge_id: string, code: string) =>
    apiRequest<{ access_token: string; refresh_token: string | null }>(
      "/api/v1/auth/otp/verify",
      {
        method: "POST",
        body: JSON.stringify({ challenge_id, code, device: deviceInput() }),
      },
    ),
};
