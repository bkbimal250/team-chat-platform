import { ReactNode } from "react";

export function FilterBar({ children }: { children: ReactNode }) {
  return (
    <div className="space-y-2 border-b border-aurora-border p-3">{children}</div>
  );
}
