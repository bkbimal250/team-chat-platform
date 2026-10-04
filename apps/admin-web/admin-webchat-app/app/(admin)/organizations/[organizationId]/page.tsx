import { OrganizationDetailClient } from "@/features/organizations/components/organization-detail-client";
export default async function Page({
  params,
}: {
  params: Promise<{ organizationId: string }>;
}) {
  const { organizationId } = await params;
  return (
    <main className="mx-auto max-w-7xl p-4 sm:p-6">
      <OrganizationDetailClient organizationId={organizationId} />
    </main>
  );
}
