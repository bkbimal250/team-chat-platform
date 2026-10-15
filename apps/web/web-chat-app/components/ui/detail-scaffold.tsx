import { ReactNode } from "react";
import { Avatar } from "./avatar";
import { ContentLayout } from "@/components/content/content-layout";

export function DetailScaffold({
  title,
  subtitle,
  avatarName,
  actions,
  children,
  width = "full",
}: {
  title: string;
  subtitle?: string;
  avatarName?: string;
  actions?: ReactNode;
  children: ReactNode;
  width?: "narrow" | "medium" | "full";
}) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-aurora-border bg-aurora-surface px-4 py-4 sm:px-6">
        <div className="flex items-start gap-3">
          {avatarName && <Avatar name={avatarName} size="lg" />}
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-semibold">{title}</h1>
            {subtitle && (
              <p className="mt-1 text-sm text-aurora-muted">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex shrink-0 gap-1">{actions}</div>}
        </div>
      </header>
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        <ContentLayout width={width}>{children}</ContentLayout>
      </div>
    </div>
  );
}
