"use client";

import { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

const controlClass =
  "mt-2 block w-full rounded-xl border border-aurora-border bg-aurora-surface px-3 py-2 text-sm text-aurora-text placeholder:text-aurora-muted";

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm font-medium text-aurora-text">
      {label}
      {children}
    </label>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={controlClass} {...props} />;
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`${controlClass} resize-none`} {...props} />;
}
