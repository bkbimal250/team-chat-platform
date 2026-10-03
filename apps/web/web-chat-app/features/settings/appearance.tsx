"use client";
import { useEffect, useState } from "react";
export type Theme = "light" | "dark" | "system";
export function applyTheme(theme: Theme) { document.documentElement.dataset.theme = theme === "system" ? window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light" : theme; }
export function Appearance() {
 const [theme,setTheme]=useState<Theme>("system");
 useEffect(()=>{ let value:Theme="system";try{const saved=localStorage.getItem("globalchat.theme");if(saved === "light" || saved === "dark") value=saved;}catch{}const timer=setTimeout(()=>setTheme(value),0);applyTheme(value);return ()=>clearTimeout(timer);},[]);
 return <section><h2 className="text-2xl font-semibold">Appearance</h2><fieldset className="mt-6 flex gap-4"><legend className="mb-3">Choose your theme</legend>{(["light","dark","system"] as const).map(value=><label key={value} className="rounded-xl border p-4 capitalize"><input type="radio" name="theme" checked={theme===value} onChange={()=>{setTheme(value);applyTheme(value);try{localStorage.setItem("globalchat.theme",value);}catch{}}}/>{value}</label>)}</fieldset></section>;
}
export function ThemeListener(){useEffect(()=>{const media=window.matchMedia?.("(prefers-color-scheme: dark)");const update=()=>{try{const value=localStorage.getItem("globalchat.theme");applyTheme(value === "dark" || value === "light" ? value : "system");}catch{applyTheme("system");}};media?.addEventListener("change",update);window.addEventListener("storage",update);update();return ()=>{media?.removeEventListener("change",update);window.removeEventListener("storage",update);};},[]);return null;}
