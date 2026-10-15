import { ReactNode } from "react";

export function SectionGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-6">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-aurora-muted">{title}</h3>
      <div className="rounded-xl border border-aurora-border bg-aurora-surface px-3">{children}</div>
    </section>
  );
}
