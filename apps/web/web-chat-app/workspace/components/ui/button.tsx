import { forwardRef, type ButtonHTMLAttributes } from "react";
export const Button = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
    size?: "sm" | "md" | "lg" | "icon";
  }
>(({ className = "", variant = "primary", size = "md", ...props }, ref) => {
  const v = {
    primary: "bg-aurora-primary text-white hover:bg-indigo-700",
    secondary: "bg-aurora-surface-alt text-aurora-text",
    outline: "border border-aurora-border bg-aurora-surface",
    ghost: "hover:bg-aurora-surface-alt",
    danger: "bg-rose-600 text-white",
  }[variant];
  const s = {
    sm: "px-2 py-1 text-sm",
    md: "px-3 py-2 text-sm",
    lg: "px-4 py-2.5",
    icon: "p-2",
  }[size];
  return (
    <button
      ref={ref}
      className={`rounded-md font-medium transition focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:opacity-50 ${v} ${s} ${className}`}
      {...props}
    />
  );
});
Button.displayName = "Button";
