import { ReactNode } from "react";

export function MainContent({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`flex min-h-0 min-w-0 flex-1 flex-col bg-aurora-background ${className}`}
    >
      {children}
    </section>
  );
}
