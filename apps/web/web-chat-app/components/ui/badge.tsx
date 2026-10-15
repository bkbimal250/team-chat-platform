import { ReactNode } from "react";

export function Badge({
  children,
  tone = "primary",
}: {
  children: ReactNode;
  tone?: "primary" | "muted";
}) {
  const styles =
    tone === "primary"
      ? "bg-aurora-primary text-white"
      : "bg-aurora-surface-alt text-aurora-muted";
  return (
    <span className={`inline-flex min-w-5 items-center justify-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums ${styles}`}>
      {children}
    </span>
  );
}
