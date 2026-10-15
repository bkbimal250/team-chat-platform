"use client";
import { useEffect, useState } from "react";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { SectionGroup } from "@/components/workspace/section-group";

export type Theme = "light" | "dark" | "system";
export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme =
    theme === "system"
      ? window.matchMedia?.("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      : theme;
}
export function Appearance() {
  const [theme, setTheme] = useState<Theme>("system");
  useEffect(() => {
    let value: Theme = "system";
    try {
      const saved = localStorage.getItem("globalchat.theme");
      if (saved === "light" || saved === "dark") value = saved;
    } catch {}
    const timer = setTimeout(() => setTheme(value), 0);
    applyTheme(value);
    return () => clearTimeout(timer);
  }, []);
  return (
    <DetailScaffold width="narrow" title="Appearance" subtitle="Theme for GlobalChat on this device">
      <SectionGroup title="Theme">
        <fieldset className="flex flex-wrap gap-2 py-2">
          <legend className="sr-only">Choose your theme</legend>
          {(["light", "dark", "system"] as const).map((value) => (
            <label
              key={value}
              className={`cursor-pointer rounded-xl border px-4 py-3 text-sm capitalize transition-colors ${theme === value ? "border-aurora-primary bg-aurora-primary/10" : "border-aurora-border bg-aurora-surface hover:bg-aurora-surface-alt"}`}
            >
              <input
                type="radio"
                name="theme"
                className="sr-only"
                aria-label={value}
                checked={theme === value}
                onChange={() => {
                  setTheme(value);
                  applyTheme(value);
                  try {
                    localStorage.setItem("globalchat.theme", value);
                  } catch {}
                }}
              />
              {value}
            </label>
          ))}
        </fieldset>
      </SectionGroup>
    </DetailScaffold>
  );
}
export function ThemeListener() {
  useEffect(() => {
    const media = window.matchMedia?.("(prefers-color-scheme: dark)");
    const update = () => {
      try {
        const value = localStorage.getItem("globalchat.theme");
        applyTheme(value === "dark" || value === "light" ? value : "system");
      } catch {
        applyTheme("system");
      }
    };
    media?.addEventListener("change", update);
    window.addEventListener("storage", update);
    update();
    return () => {
      media?.removeEventListener("change", update);
      window.removeEventListener("storage", update);
    };
  }, []);
  return null;
}
