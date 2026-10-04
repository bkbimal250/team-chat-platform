"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { navigation } from "@/config/navigation";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
export function GlobalSearch() {
  const [open, setOpen] = useState(false),
    [query, setQuery] = useState("");
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  const items = navigation
    .flatMap((group) => group.items)
    .filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));
  return (
    <>
      <Button
        variant="outline"
        aria-label="Find an admin screen"
        onClick={() => setOpen(true)}
      >
        <Search size={17} />
      </Button>
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Find an admin screen"
      >
        <label className="mt-3 block text-sm">
          Screen name
          <input
            className="mt-1 w-full rounded border p-2"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <p className="mt-2 text-xs text-slate-500">
          Navigation search only. Use each resource screen for authorized
          backend data search.
        </p>
        <ul className="mt-3 max-h-80 overflow-auto">
          {items.map((item) => (
            <li key={item.href}>
              <Link
                className="block rounded p-2 hover:bg-slate-50"
                href={item.href}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </Modal>
    </>
  );
}
