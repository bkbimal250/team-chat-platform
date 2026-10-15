import { AdminLiveProvider } from "@/features/admin/live-provider";
import { AdminShell } from "@/components/layout/admin-shell";
import { AdminGuard } from "@/features/auth/admin-guard";
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminGuard>
      <AdminLiveProvider><AdminShell>{children}</AdminShell></AdminLiveProvider>
    </AdminGuard>
  );
}
