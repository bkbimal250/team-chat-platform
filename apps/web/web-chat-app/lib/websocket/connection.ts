export function connectRealtime(accessToken: string) {
  const url = new URL(
    "/api/v1/realtime",
    process.env.NEXT_PUBLIC_WS_URL ?? "wss://ws.michat.in",
  );
  url.searchParams.set("token", accessToken);
  return new WebSocket(url);
}
