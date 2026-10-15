"use client";

import { ReactNode } from "react";

export function Tooltip({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <span className="group relative inline-flex">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-1.5 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-xs text-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 dark:bg-slate-100 dark:text-slate-900 [@media(hover:hover)]:block"
      >
        {label}
      </span>
    </span>
  );
}
