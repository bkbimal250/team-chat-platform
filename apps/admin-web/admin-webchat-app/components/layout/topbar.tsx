"use client";
import Link from "next/link";
import { Bell, Menu } from "lucide-react";
import { GlobalSearch } from "./global-search";
import { RealtimeStatus } from "./realtime-status";
import { ProfileMenu } from "./profile-menu";
export function Topbar({ onMenu }: { onMenu: () => void }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4">
      <div className="flex items-center gap-3">
        <button
          aria-label="Open navigation"
          onClick={onMenu}
          className="lg:hidden"
        >
          <Menu />
        </button>
        <p className="text-sm font-medium text-slate-600">Dashboard</p>
      </div>
      <div className="flex items-center gap-2">
        <GlobalSearch />
        <span className="hidden text-sm text-slate-600 md:block">
          Platform administration
        </span>
        <div className="hidden lg:block">
          <RealtimeStatus />
        </div>
        <Link
          href="/notifications"
          aria-label="Your notifications"
          className="rounded border p-2"
        >
          <Bell size={17} />
        </Link>
        <ProfileMenu />
      </div>
    </header>
  );
}
