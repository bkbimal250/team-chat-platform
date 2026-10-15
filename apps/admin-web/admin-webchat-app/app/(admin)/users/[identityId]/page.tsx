import { UserDetailClient } from "@/features/platform/user-detail-client";

export default async function Page({ params }: { params: Promise<{ identityId: string }> }) {
  const { identityId } = await params;
  return <main className="mx-auto max-w-7xl p-4 sm:p-6"><UserDetailClient identityId={identityId} /></main>;
}
