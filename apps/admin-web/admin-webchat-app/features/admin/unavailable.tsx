import { EmptyState } from "@/components/feedback/empty-state";
export function Unavailable({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <main className="mx-auto max-w-5xl space-y-4 p-4 sm:p-6">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <EmptyState
        title="Backend admin API unavailable"
        description={description}
      />
    </main>
  );
}
