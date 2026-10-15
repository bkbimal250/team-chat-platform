import type { LucideIcon } from "lucide-react";
import { ReactNode } from "react";

export function SettingRow({
  icon: Icon,
  title,
  description,
  control,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  control: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 px-4 py-3.5 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 flex-1 gap-3">
        {Icon && <Icon className="mt-0.5 size-5 shrink-0 text-aurora-muted" aria-hidden />}
        <div className="min-w-0">
          <p className="text-sm font-medium text-aurora-text">{title}</p>
          {description && (
            <p className="mt-0.5 text-xs leading-relaxed text-aurora-muted">{description}</p>
          )}
        </div>
      </div>
      <div className="shrink-0 sm:min-w-[9rem] sm:text-right">{control}</div>
    </div>
  );
}
