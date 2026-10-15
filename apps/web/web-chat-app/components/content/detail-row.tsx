import { ReactNode } from "react";

export function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <dt className="text-sm text-aurora-muted">{label}</dt>
      <dd className="text-sm font-medium text-aurora-text sm:max-w-[60%] sm:text-right">{value}</dd>
    </div>
  );
}
