export function IdentityDisplay({name, subtitle}: {name: string; subtitle?: string}) {
 const initials = name.trim().split(/\s+/).slice(0,2).map(part=>part[0]).join("").toUpperCase() || "?";
 return <div className="flex min-w-0 items-center gap-3"><span aria-hidden="true" className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-indigo-50 text-xs font-semibold text-indigo-700">{initials}</span><div className="min-w-0"><p className="break-words font-medium">{name || "Unnamed member"}</p>{subtitle && <p className="break-words text-xs text-slate-500">{subtitle}</p>}</div></div>;
}
