"use client";
import { createContext, useContext, useEffect, useState } from "react";
import type { RealtimeState } from "@/lib/realtime/realtime-types";
const Context = createContext<RealtimeState>("not-configured");
export const useAdminConnection = () => useContext(Context);
/** Platform administration has no chat/realtime contract. */
export function AdminLiveProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<RealtimeState>("not-configured");
  useEffect(() => {
    const offline = () => setState("offline");
    const online = () => setState("not-configured");
    window.addEventListener("online", online);
    window.addEventListener("offline", offline);
    return () => {
      window.removeEventListener("online", online);
      window.removeEventListener("offline", offline);
    };
  }, []);
  return <Context.Provider value={state}>{children}</Context.Provider>;
}
