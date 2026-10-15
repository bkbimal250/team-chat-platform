"use client";

import { ReactNode } from "react";

export function ContactField({
  icon,
  label,
  value,
  placeholder,
  disabled,
  required,
  type = "text",
  maxLength = 100,
  onChange,
  autoComplete,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  type?: string;
  maxLength?: number;
  autoComplete?: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="flex gap-4 border-b border-aurora-border py-3">
      <span className="mt-2 shrink-0 text-aurora-muted" aria-hidden>{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="sr-only">{label}</span>
        <input
          type={type}
          value={value}
          required={required}
          disabled={disabled}
          placeholder={placeholder}
          autoComplete={autoComplete}
          maxLength={maxLength}
          onChange={(event) => onChange(event.target.value)}
          className="w-full border-0 bg-transparent py-1 text-sm text-aurora-text placeholder:text-aurora-muted focus-visible:outline-none focus-visible:ring-0"
        />
      </span>
    </label>
  );
}
