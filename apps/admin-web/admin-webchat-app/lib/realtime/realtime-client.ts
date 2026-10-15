import type { RealtimeState } from "./realtime-types";
type Options = { url: string; token: () => string | undefined; onState: (state: RealtimeState) => void; onReconnect: () => void; socket?: (url: string) => WebSocket };
// Admin membership/invitation events are not delivered by the existing server.
// Connect using its actual ping/pong protocol; reconnect triggers API reconciliation.
export class RealtimeClient {
 private socket: WebSocket | null = null;
 private retry?: ReturnType<typeof setTimeout>;
 private heartbeat?: ReturnType<typeof setInterval>;
 private disposed = false;
 private opened = false;
 private attempt = 0;
 constructor(private options: Options) {}
 connect() {
  if (this.disposed || this.socket) return;
  const token = this.options.token();
  if (!this.options.url || !token) { this.options.onState("not-configured"); return; }
  if (!navigator.onLine) { this.options.onState("offline"); return; }
  this.options.onState(this.opened ? "reconnecting" : "connecting");
  const url = new URL("/api/v1/realtime", this.options.url);
  url.searchParams.set("token", token);
  const ws = (this.options.socket ?? (url => new WebSocket(url)))(url.toString());
  this.socket = ws;
  ws.onopen = () => {
   if (this.disposed || this.socket !== ws) return;
   this.attempt = 0; this.options.onState("connected");
   if (this.opened) this.options.onReconnect();
   this.opened = true;
   this.heartbeat = setInterval(() => { if (ws.readyState === 1) ws.send(JSON.stringify({version: 1, type: "ping"})); }, 25000);
  };
  // No unscoped frame is allowed to mutate tenant resources.
  ws.onmessage = () => {};
  ws.onerror = () => { if (!this.disposed) this.options.onState("reconnecting"); };
  ws.onclose = () => {
   if (this.heartbeat) clearInterval(this.heartbeat);
   this.socket = null;
   if (this.disposed) return;
   if (!navigator.onLine) { this.options.onState("offline"); return; }
   this.options.onState("reconnecting");
   this.retry = setTimeout(() => this.connect(), Math.min(30000, 1000 * 2 ** this.attempt++));
  };
 }
 disconnect() {
  this.disposed = true;
  if (this.retry) clearTimeout(this.retry);
  if (this.heartbeat) clearInterval(this.heartbeat);
  if (this.socket) { this.socket.onclose = null; this.socket.onopen = null; this.socket.onerror = null; this.socket.onmessage = null; this.socket.close(); }
  this.socket = null;
 }
}
