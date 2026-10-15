import { ReactNode } from "react";

export function SecondaryPanel({
  title,
  actions,
  children,
  className = "",
}: {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <aside
      className={`flex w-full shrink-0 flex-col border-r border-aurora-border bg-aurora-surface md:w-[min(100%,400px)] lg:w-[380px] ${className}`}
    >
      <header className="flex items-center justify-between gap-2 border-b border-aurora-border px-4 py-3">
        <h2 className="text-lg font-semibold text-aurora-text">{title}</h2>
        {actions && <div className="flex items-center gap-1">{actions}</div>}
      </header>
      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">{children}</div>
    </aside>
  );
}
