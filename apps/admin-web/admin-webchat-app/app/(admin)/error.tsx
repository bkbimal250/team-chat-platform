"use client";
import { ErrorState } from "@/components/feedback/error-state";
export default function ErrorBoundary({ reset }: { reset: () => void }) {
  return (
    <main className="mx-auto max-w-3xl p-6">
      <ErrorState
        title="This screen could not be opened"
        description="Retry loading the screen. If the problem continues, contact your organization administrator."
        retry={reset}
      />
    </main>
  );
}
