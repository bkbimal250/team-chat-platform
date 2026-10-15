export function StatusPill({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "success" | "warning" | "danger" }) {
  const styles = {
    neutral: "bg-aurora-surface-alt text-aurora-muted",
    success: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
    warning: "bg-amber-500/15 text-amber-800 dark:text-amber-200",
    danger: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${styles[tone]}`}>
      {children}
    </span>
  );
}
