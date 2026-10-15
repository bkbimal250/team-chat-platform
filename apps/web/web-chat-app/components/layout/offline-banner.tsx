export function OfflineBanner({ message }: { message: string }) {
  return (
    <p
      role="status"
      className="bg-amber-100 px-4 py-2 text-center text-sm text-amber-900 dark:bg-amber-950/50 dark:text-amber-100 sm:px-5"
    >
      {message}
    </p>
  );
}
