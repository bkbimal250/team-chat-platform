import { VISIBILITY_OPTIONS } from "./labels";

const selectClass =
  "w-full min-w-[10rem] rounded-lg border border-aurora-border bg-aurora-background px-2.5 py-1.5 text-sm text-aurora-text focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-aurora-primary sm:w-auto";

export function VisibilitySelect({
  value,
  onChange,
  "aria-label": ariaLabel,
}: {
  value: string;
  onChange: (value: string) => void;
  "aria-label": string;
}) {
  return (
    <select
      aria-label={ariaLabel}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={selectClass}
    >
      {VISIBILITY_OPTIONS.map((opt) => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  );
}
