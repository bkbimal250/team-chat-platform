const colors: Record<string, string> = {
  owner: "bg-violet-100 text-violet-800",
  admin: "bg-indigo-100 text-indigo-800",
  manager: "bg-blue-100 text-blue-800",
  member: "bg-aurora-surface-alt text-aurora-muted",
  active: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  invited: "bg-amber-50 text-amber-700",
  suspended: "bg-rose-50 text-rose-700",
  disabled: "bg-aurora-surface-alt text-aurora-muted",
  removed: "bg-rose-50 text-rose-700",
  revoked: "bg-aurora-surface-alt text-aurora-muted",
};
export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium ${colors[status.toLowerCase()] ?? "bg-aurora-surface-alt text-aurora-muted"}`}
    >
      {status}
    </span>
  );
}
