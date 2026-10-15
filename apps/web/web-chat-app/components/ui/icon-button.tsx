"use client";

import { ButtonHTMLAttributes, ReactNode } from "react";
import { Tooltip } from "./tooltip";

export const iconSize = "size-5 shrink-0 pointer-events-none";

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
};

export function IconButton({
  label,
  children,
  className = "",
  type = "button",
  ...props
}: IconButtonProps) {
  return (
    <Tooltip label={label}>
      <button
        type={type}
        aria-label={label}
        title={label}
        className={`inline-flex items-center justify-center rounded-lg p-2 hover:bg-aurora-surface-alt disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
        {...props}
      >
        {children}
      </button>
    </Tooltip>
  );
}
