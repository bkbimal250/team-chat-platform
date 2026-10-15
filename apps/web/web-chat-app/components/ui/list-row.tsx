import { ReactNode } from "react";

export function ListRow({
  active,
  onClick,
  leading,
  title,
  subtitle,
  trailing,
}: {
  active?: boolean;
  onClick: () => void;
  leading?: ReactNode;
  title: string;
  subtitle?: ReactNode;
  trailing?: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-aurora-surface-alt ${active ? "bg-aurora-primary/10" : ""}`}
    >
      {leading}
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium">{title}</span>
        {subtitle && (
          <span className="mt-0.5 block truncate text-xs text-aurora-muted">
            {subtitle}
          </span>
        )}
      </span>
      {trailing}
    </button>
  );
}
