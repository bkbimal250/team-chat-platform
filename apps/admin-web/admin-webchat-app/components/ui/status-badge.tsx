const colors: Record<string, string> = {
  active: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  invited: "bg-amber-50 text-amber-700",
  suspended: "bg-rose-50 text-rose-700",
  disabled: "bg-slate-100 text-slate-600",
  removed: "bg-rose-50 text-rose-700",
  revoked: "bg-slate-100 text-slate-600",
};
export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium ${colors[status.toLowerCase()] ?? "bg-slate-100 text-slate-600"}`}
    >
      {status}
    </span>
  );
}
