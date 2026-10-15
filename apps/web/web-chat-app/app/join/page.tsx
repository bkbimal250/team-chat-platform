import type { Metadata } from "next";
import { InvitationJoin } from "@/features/auth/invitation";
export const metadata: Metadata = { title: "Join your workspace | GlobalChat", robots: { index: false, follow: false }, referrer: "no-referrer" };
export default function Page() { return <InvitationJoin />; }
