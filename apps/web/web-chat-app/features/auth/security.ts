export function parseQR(value: string): { id: string; secret: string } | null {
  let candidate = value;
  if (value.startsWith("globalchat-link:")) candidate = value.slice(16);
  else {
    try {
      candidate = new URL(value).searchParams.get("challenge") ?? "";
    } catch {
      return null;
    }
  }
  const match =
    /^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.([A-Za-z0-9_-]{32,512})$/i.exec(
      candidate,
    );
  return match ? { id: match[1], secret: match[2] } : null;
}
export function qrRemaining(expiresAt: string, now = Date.now()) {
  return Math.max(0, Math.ceil((Date.parse(expiresAt) - now) / 1000));
}
export function stopCamera(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop());
}
export function e164(country: string, number: string) {
  const value = number.trim().startsWith("+")
    ? number.replace(/[\s()-]/g, "")
    : `+${country}${number.replace(/[\s()-]/g, "")}`;
  return /^\+[1-9]\d{7,14}$/.test(value) ? value : null;
}
