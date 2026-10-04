"use client";
import { useResource } from "@/lib/api/use-resource";
import type { Organization } from "@/lib/api/contracts";
export function WorkspaceSwitcher() {
  const response = useResource<Organization>("/api/v1/organizations/current/");
  return (
    <span
      title="Current authenticated workspace; no platform-wide workspace picker is exposed"
      className="max-w-52 truncate text-sm text-slate-600"
    >
      {response.data?.display_name ||
        response.data?.name ||
        "Current workspace"}
    </span>
  );
}
