import { apiRequest } from "@/lib/api/client";
import type { Branch, CursorPage } from "@/lib/api/contracts";
export const listBranches = (
  query: Record<string, string | number | undefined> = {},
) => apiRequest<CursorPage<Branch>>("/api/v1/branches/", { query });
export const listBranchesByOrganization = async (id: string) => {
  const page = await listBranches();
  return {
    ...page,
    results: page.results.filter((row) => row.organization === id),
  };
};
export type { Branch } from "@/lib/api/contracts";
