import { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  detail,
}: {
  icon: LucideIcon;
  title: string;
  detail: string;
}) {
  return (
    <div className="m-auto max-w-sm p-6 text-center sm:p-8">
      <div
        className="mx-auto mb-4 grid size-14 place-items-center rounded-3xl bg-cyan-100 text-cyan-700 dark:bg-cyan-950/50 dark:text-cyan-200"
      >
        <Icon className="size-7" aria-hidden />
      </div>
      <p className="font-semibold text-aurora-text">{title}</p>
      <p className="mt-2 text-sm leading-6 text-aurora-muted">{detail}</p>
    </div>
  );
}
