import { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="mb-6 border-b border-aurora-border pb-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-aurora-text">{title}</h1>
          {description && (
            <p className="mt-1 text-sm leading-relaxed text-aurora-muted">{description}</p>
          )}
        </div>
        {actions}
      </div>
    </header>
  );
}
