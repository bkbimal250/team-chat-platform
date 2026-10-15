export function humanStatus(value: string) {
  if (!value) return value;
  return value
    .split("_")
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(" ");
}
