import { ReactNode } from "react";

export function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="mb-6">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-aurora-muted">{title}</h2>
      {description && <p className="mt-1 mb-3 text-sm text-aurora-muted">{description}</p>}
      {!description && <div className="mb-2" />}
      <div className="divide-y divide-aurora-border overflow-hidden rounded-xl border border-aurora-border bg-aurora-surface/60">
        {children}
      </div>
    </section>
  );
}
