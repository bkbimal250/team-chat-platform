export const VISIBILITY_OPTIONS = [
  { value: "EVERYONE", label: "Everyone" },
  { value: "ORGANIZATION", label: "My organization" },
  { value: "CONTACTS", label: "My contacts" },
  { value: "NOBODY", label: "Nobody" },
] as const;

export function visibilityLabel(value: string) {
  return VISIBILITY_OPTIONS.find((o) => o.value === value)?.label ?? value.replaceAll("_", " ").toLowerCase();
}

export function previewModeLabel(mode: string) {
  const map: Record<string, string> = {
    FULL: "Full preview",
    SENDER_ONLY: "Sender only",
    NONE: "Hidden until opened",
  };
  return map[mode] ?? mode.replaceAll("_", " ").toLowerCase();
}
