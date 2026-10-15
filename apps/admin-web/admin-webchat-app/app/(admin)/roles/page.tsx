import { Card } from "@/components/ui/card";
export default function Page() {
  return (
    <main className="mx-auto max-w-7xl p-4 sm:p-6">
      <section className="space-y-4">
        <h1 className="text-2xl font-semibold">Roles & Access</h1>
        <Card className="p-5">
          <h2 className="font-semibold">Platform roles</h2>
          <p className="mt-2 text-sm text-slate-500">
            Platform roles are persistent grants managed by trusted local
            operators. Tenant roles are not shown here because they remain
            organization-specific.
          </p>
          <ul className="mt-3 list-disc pl-5 text-sm">
            <li>
              SUPER_ADMIN: platform access, identities, services, sessions and
              audit.
            </li>
            <li>
              ADMIN: platform access, identities, services and organization
              metadata.
            </li>
          </ul>
        </Card>
      </section>
    </main>
  );
}
