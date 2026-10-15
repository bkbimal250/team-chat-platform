"use client";

export function Switch({
  checked,
  onChange,
  disabled,
  label,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 rounded-full border transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-aurora-primary disabled:opacity-50 ${checked ? "border-aurora-primary bg-aurora-primary" : "border-aurora-border bg-aurora-surface-alt"}`}
    >
      <span
        className={`pointer-events-none inline-block size-5 translate-y-0.5 rounded-full bg-white shadow transition-transform ${checked ? "translate-x-5" : "translate-x-0.5"}`}
      />
    </button>
  );
}
