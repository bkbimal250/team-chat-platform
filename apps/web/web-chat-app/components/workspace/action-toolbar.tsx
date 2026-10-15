import { ReactNode } from "react";

export function ActionToolbar({
  children,
  className = "border-t border-aurora-border pt-4",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`flex flex-wrap items-center gap-1 ${className}`}>{children}</div>;
}
