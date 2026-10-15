"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose } from "lucide-react";
import { useState } from "react";
import { navigation } from "@/config/navigation";
import { Modal } from "@/components/ui/modal";
import { Topbar } from "./topbar";
export function AdminShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const path = usePathname();
  const nav = (
    <nav className="space-y-5">
      {navigation.map((group) => (
        <div key={group.label}>
          <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            {collapsed ? "" : group.label}
          </p>
          {group.items.map((item) => {
            const Icon = item.icon;
            const active =
              path === item.href ||
              (item.href !== "/dashboard" && path.startsWith(`${item.href}/`));
            return (
              <Link
                onClick={() => setOpen(false)}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${active ? "bg-slate-800 text-white" : "text-slate-300 hover:bg-slate-800 hover:text-white"}`}
                href={item.href}
                key={item.href}
                title={collapsed ? item.label : undefined}
              >
                <Icon size={18} />
                {!collapsed && item.label}
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
  return (
    <div className="min-h-screen bg-slate-50">
      <aside
        className={`fixed inset-y-0 hidden overflow-y-auto bg-slate-950 p-4 lg:block ${collapsed ? "w-[72px]" : "w-64"}`}
      >
        <div className="mb-8 px-3 text-white">
          <b>GC</b>
          {!collapsed && (
            <>
              <strong className="ml-2">GlobalChat</strong>
              <span className="block text-xs text-slate-400">
                Platform Administration
              </span>
            </>
          )}
        </div>
        {nav}
        <button
          aria-label="Collapse sidebar"
          onClick={() => {
            setCollapsed(!collapsed);
            localStorage.setItem(
              "globalchat-admin-sidebar-collapsed",
              String(!collapsed),
            );
          }}
          className="mt-8 w-full rounded p-2 text-slate-300 hover:bg-slate-800"
        >
          <PanelLeftClose size={18} />
        </button>
      </aside>
      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title="Workspace navigation"
      >
        <div className="mt-3 rounded-lg bg-slate-950 p-4">{nav}</div>
      </Modal>
      <div className={collapsed ? "lg:pl-[72px]" : "lg:pl-64"}>
        <Topbar onMenu={() => setOpen(true)} />
        {children}
      </div>
    </div>
  );
}
