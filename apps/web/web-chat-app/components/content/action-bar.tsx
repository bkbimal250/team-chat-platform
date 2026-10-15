import { ReactNode } from "react";

export function ActionBar({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`sticky bottom-0 -mx-4 flex flex-wrap items-center gap-2 border-t border-aurora-border bg-aurora-background/95 px-4 py-3 backdrop-blur-sm sm:-mx-6 sm:px-6 ${className}`}
    >
      {children}
    </div>
  );
}
