export function AlertBanner({
  message,
  tone = "error",
}: {
  message: string;
  tone?: "error" | "success" | "info";
}) {
  if (!message) return null;
  const styles = {
    error:
      "bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-200",
    success:
      "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200",
    info: "bg-cyan-50 text-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-100",
  };
  return (
    <p role="alert" className={`rounded-xl p-3 text-sm ${styles[tone]}`}>
      {message}
    </p>
  );
}
