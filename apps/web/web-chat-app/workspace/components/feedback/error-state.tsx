import { Button } from "@/workspace/components/ui/button";
export function ErrorState({
  title = "Something went wrong",
  description = "Please try again.",
  retry,
}: {
  title?: string;
  description?: string;
  retry?: () => void;
}) {
  return (
    <div role="alert" className="rounded-xl border border-rose-100 bg-rose-50 p-6 text-center">
      <span aria-hidden="true" className="text-rose-600">⚠</span>
      <h2 className="mt-2 font-semibold">{title}</h2>
      <p className="text-sm text-aurora-muted">{description}</p>
      {retry && (
        <Button className="mt-3" onClick={retry}>
          Try again
        </Button>
      )}
    </div>
  );
}
