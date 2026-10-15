import { apiRequest, gatewayPath } from "./client";
import type { CursorPage } from "./contracts";
export async function collectPages<T>(path: string): Promise<T[]> {
  const rows: T[] = [];
  const seen = new Set<string>();
  let next: string | null = path;
  while (next) {
    const route = gatewayPath(next);
    if (seen.has(route) || seen.size >= 100)
      throw new Error("Pagination limit reached. Retry or narrow the query.");
    seen.add(route);
    const page: CursorPage<T> = await apiRequest<CursorPage<T>>(route);
    rows.push(...page.results);
    next = page.next;
  }
  return rows;
}
