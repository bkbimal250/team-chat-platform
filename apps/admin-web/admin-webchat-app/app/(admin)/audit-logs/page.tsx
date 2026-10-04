import { ResourceScreen } from "@/features/admin/resource-screen";
export default function Page() {
  return (
    <main className="mx-auto max-w-7xl p-4 sm:p-6">
      <ResourceScreen resource="audit-logs" />
    </main>
  );
}
