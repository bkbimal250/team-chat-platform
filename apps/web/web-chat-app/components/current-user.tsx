"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
export function CurrentUser({ token }: { token: string | null }) {
  const [name, setName] = useState("");
  useEffect(() => {
    let active = true;
    if (token)
      apiRequest<{ display_name: string }>("/api/v1/users/me", {}, token)
        .then((row) => {
          if (active) setName(row.display_name);
        })
        .catch(() => {});
    return () => {
      active = false;
    };
  }, [token]);
  return (
    <p className="mt-1 truncate text-xs text-aurora-muted">
      {name || "Your workspace conversations"}
    </p>
  );
}
