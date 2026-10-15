import { ReactNode } from "react";

export function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-aurora-border py-2.5 text-sm last:border-0">
      <dt className="text-aurora-muted">{label}</dt>
      <dd className="max-w-[65%] text-right font-medium text-aurora-text">{value}</dd>
    </div>
  );
}
