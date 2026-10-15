import { ReactNode } from "react";

export function ContentLayout({
  children,
  width = "narrow",
}: {
  children: ReactNode;
  width?: "narrow" | "medium" | "full";
}) {
  const max =
    width === "full" ? "max-w-none" : width === "medium" ? "max-w-2xl" : "max-w-xl";
  return <div className={`mx-auto w-full ${max}`}>{children}</div>;
}
