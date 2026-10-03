"use client";
import { Conversation } from "@/features/chat/api";
import { People } from "./people";
import { ReactNode, useEffect, useState } from "react";
import { LinkedDevices } from "@/features/devices/linked-devices";
import { deviceApi } from "@/features/devices/api";
import { ProfileSettings } from "@/features/settings/profile-settings";
import { Appearance, ThemeListener } from "@/features/settings/appearance";
import { NotificationSettings } from "@/features/notifications/settings";
import { NotificationInbox } from "@/features/notifications/inbox";
import { getAccessToken } from "@/lib/auth/session";
import { Toast } from "./ui/toast";
import { ConfirmDialog } from "./ui/confirm-dialog";
const destinations = [
  "Chats",
  "People",
  "Notifications",
  "Profile",
  "Linked Devices",
  "Settings",
] as const;
export function ApplicationStructure({
  children,
  onSignedOut,
  onConversation,
}: {
  children: ReactNode;
  onSignedOut: () => void;
  onConversation: (row: Conversation) => void;
}) {
  const [page, setPage] = useState<string>("Chats");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(true);
  const token = getAccessToken();
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  async function logout() {
    if (!token) {
      onSignedOut();
      return;
    }
    setBusy(true);
    try {
      await deviceApi.logout(token);
      onSignedOut();
    } catch {
      setError(
        "Unable to log out on the server. Check your connection and retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="flex h-dvh flex-col bg-slate-50 md:flex-row">
      <ThemeListener/><Toast/>
      <nav
        aria-label="Main navigation"
        className="order-2 flex shrink-0 justify-around border-t border-slate-200 bg-cyan-950 p-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] text-cyan-100 md:order-1 md:w-24 md:flex-col md:justify-start md:gap-4 md:border-t-0 md:py-6"
      >
        <div className="hidden text-center text-3xl text-white md:block">◈</div>
        {destinations.map((item) => (
          <button
            key={item}
            aria-current={page === item ? "page" : undefined}
            onClick={() => setPage(item)}
            className={`rounded-xl px-2 py-3 text-[11px] font-semibold md:text-xs ${page === item ? "bg-white/15 text-white" : "hover:bg-white/10"}`}
          >
            {item}
          </button>
        ))}
        <button
          onClick={() => setConfirm(true)}
          className="rounded-xl px-2 py-3 text-xs md:mt-auto"
        >
          Logout
        </button>
      </nav>
      <div className="order-1 flex min-h-0 min-w-0 flex-1 flex-col md:order-2">
        {!online && (
          <p
            role="status"
            className="bg-amber-100 px-5 py-2 text-center text-sm text-amber-900"
          >
            You’re offline. Waiting for your connection…
          </p>
        )}
        {page === "Chats" ? (
          children
        ) : (
          <main className="flex-1 overflow-y-auto p-6 md:p-10">
            <div className="mx-auto max-w-3xl">
              {page === "People" && token ? (
                <People
                  token={token}
                  onConversation={(row) => {
                    onConversation(row);
                    setPage("Chats");
                  }}
                />
              ) : page === "Linked Devices" && token ? (
                <LinkedDevices token={token} onSignedOut={onSignedOut} />
              ) : page === "Profile" && token ? (
                <ProfileSettings token={token} />
              ) : page === "Notifications" && token ? <NotificationInbox token={token} onConversation={row=>{onConversation(row);setPage("Chats");}}/> : page === "Settings / Notifications" && token ? <NotificationSettings token={token}/> : page === "Settings / Privacy" && token ? <ProfileSettings token={token} privacy/> : page === "Settings / Appearance" ? <Appearance/> : page === "Settings / Help" ? <section><h1 className="text-2xl font-semibold">Help</h1><p className="mt-5">Contact your organization administrator for workspace access, account support and privacy questions.</p></section> : page === "Settings / Account" ? <section><h1 className="text-2xl font-semibold">Account</h1><p className="mt-5">Manage signed-in devices in Linked Devices. Workspace access is managed by your organization administrator.</p><button className="mt-5 rounded-xl border p-3" onClick={()=>setPage("Linked Devices")}>Manage linked devices</button><button className="ml-3 rounded-xl border p-3" onClick={()=>setConfirm(true)}>Log out</button></section> : (
                <>
                  <h1 className="text-3xl font-semibold">Settings</h1>
                  <div className="mt-8 grid gap-3">
                    {[
                      "Profile",
                      "Account",
                      "Privacy",
                      "Notifications",
                      "Linked Devices",
                      "Appearance",
                      "Help",
                    ].map((item) => (
                      <button
                        key={item}
                        onClick={() =>
                          setPage(
                            item === "Profile" || item === "Linked Devices"
                              ? item
                              : `Settings / ${item}`,
                          )
                        }
                        className="rounded-2xl border bg-white p-5 text-left font-medium"
                      >
                        {item}{" "}
                        <span className="float-right text-slate-400">→</span>
                      </button>
                    ))}
                  </div>
                  {page.startsWith("Settings /") && (
                    <p
                      role="status"
                      className="mt-5 rounded-xl bg-cyan-50 p-4 text-sm"
                    >
                      {page.split("/")[1].trim()} controls are not connected in
                      this frontend yet.
                    </p>
                  )}
                </>
              )}
            </div>
          </main>
        )}
      </div>
      {confirm && (
        <ConfirmDialog
          title="Log out of GlobalChat?"
          busy={busy}
          onCancel={() => setConfirm(false)}
          onConfirm={() => void logout()}
        >
          {error || "This ends your current session on this device."}
        </ConfirmDialog>
      )}
    </div>
  );
}