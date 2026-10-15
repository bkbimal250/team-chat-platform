"use client";

import { Search, X } from "lucide-react";
import { iconSize } from "./icon-button";

type SearchFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  minLength?: number;
  className?: string;
  inputClassName?: string;
};

export function SearchField({
  label,
  value,
  onChange,
  placeholder,
  required,
  minLength,
  className = "",
  inputClassName = "",
}: SearchFieldProps) {
  return (
    <div className={`relative ${className}`}>
      <Search
        className={`${iconSize} pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-aurora-muted`}
        aria-hidden
      />
      <input
        type="search"
        onKeyDown={(event) => { if (event.key === "Escape") onChange(""); }}
        aria-label={label}
        placeholder={placeholder ?? label}
        value={value}
        required={required}
        minLength={minLength}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-xl border border-aurora-border bg-aurora-surface py-2 pl-9 pr-10 text-sm ${inputClassName}`}
      />
      {value && <button type="button" aria-label={`Clear ${label.toLowerCase()}`} onClick={() => onChange("")} className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-1 text-aurora-muted hover:bg-aurora-surface-alt focus-visible:outline-2 focus-visible:outline-aurora-primary"><X className={iconSize} aria-hidden /></button>}
    </div>
  );
}
