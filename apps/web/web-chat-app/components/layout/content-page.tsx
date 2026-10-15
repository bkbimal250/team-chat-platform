import { ReactNode } from "react";

export function ContentPage({
  title,
  description,
  children,
}: {
  title?: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <main className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-10">
      <div className="mx-auto max-w-3xl">
        {title && (
          <header className="mb-6 md:mb-8">
            <h1 className="text-2xl font-semibold text-aurora-text sm:text-3xl">
              {title}
            </h1>
            {description && (
              <p className="mt-2 text-sm text-aurora-muted">{description}</p>
            )}
          </header>
        )}
        {children}
      </div>
    </main>
  );
}
