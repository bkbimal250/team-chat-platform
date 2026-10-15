import { ReactNode } from "react";
import { Avatar } from "@/components/ui/avatar";

export function DetailHeader({
  title,
  subtitle,
  avatarName,
  actions,
}: {
  title: string;
  subtitle?: string;
  avatarName?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="border-b border-aurora-border bg-aurora-surface px-4 py-4 sm:px-6">
      <div className="flex items-start gap-3">
        {avatarName && <Avatar name={avatarName} size="lg" />}
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-aurora-muted">{subtitle}</p>}
        </div>
        {actions && <div className="flex shrink-0 gap-1">{actions}</div>}
      </div>
    </header>
  );
}
