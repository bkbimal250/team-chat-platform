import { apiRequest } from "@/lib/api/client";
import type { Organization } from "@/lib/api/contracts";
export const getCurrentOrganization = () =>
  apiRequest<Organization>("/api/v1/organizations/current/");
export const listOrganizations = async () => [await getCurrentOrganization()];
export async function getOrganizationById(id: string) {
  const current = await getCurrentOrganization();
  return current.id === id ? current : null;
}
export const updateOrganization = (value: {
  name: string;
  display_name: string;
  slug: string;
  timezone: string;
  country_code: string;
}) =>
  apiRequest<Organization>("/api/v1/organizations/current/", {
    method: "PATCH",
    body: JSON.stringify(value),
  });
