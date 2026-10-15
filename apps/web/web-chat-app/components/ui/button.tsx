"use client";

import { ButtonHTMLAttributes } from "react";

const variants = {
  primary:
    "bg-aurora-primary text-white hover:opacity-90 disabled:opacity-50",
  secondary: "bg-cyan-800 text-white hover:bg-cyan-900 disabled:opacity-50",
  outline:
    "border border-aurora-border bg-aurora-surface hover:bg-aurora-surface-alt disabled:opacity-50",
  ghost: "hover:bg-aurora-surface-alt disabled:opacity-50",
  danger: "text-rose-700 border border-aurora-border hover:bg-rose-50 dark:hover:bg-rose-950/30",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof variants;
};

export function Button({
  variant = "outline",
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors ${variants[variant]} ${className}`}
      {...props}
    />
  );
}
