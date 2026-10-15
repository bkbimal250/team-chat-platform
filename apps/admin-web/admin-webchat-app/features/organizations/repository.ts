import { apiRequest } from "@/lib/api/client";
import type { Organization } from "@/lib/api/contracts";
export type PlatformPage<T> = { items: T[]; total: number };
export const listOrganizations = (params: { limit: number; offset: number; search?: string }) => {
  const query = new URLSearchParams({ limit: String(params.limit), offset: String(params.offset) });
  if (params.search) query.set("search", params.search);
  return apiRequest<PlatformPage<Organization>>(`/api/v1/platform/organizations/?${query}`);
};
export async function getOrganizationById(id: string) {
  return apiRequest<Organization>(`/api/v1/platform/organizations/${id}/`);
}
