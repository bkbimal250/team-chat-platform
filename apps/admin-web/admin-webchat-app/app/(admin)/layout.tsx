import { AdminShell } from "@/components/layout/admin-shell";
import { AdminGuard } from "@/features/auth/admin-guard";
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminGuard>
      <AdminShell>{children}</AdminShell>
    </AdminGuard>
  );
}
