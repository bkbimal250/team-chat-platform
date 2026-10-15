import {
  Building2,
  LayoutDashboard,
  MonitorSmartphone,
  ScrollText,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";

export const navigation = [
  {
    label: "Overview",
    items: [{ label: "Dashboard", href: "/dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Platform",
    items: [
      { label: "Organizations", href: "/organizations", icon: Building2 },
      { label: "Users", href: "/users", icon: Users },
      { label: "Platform Admins", href: "/platform-admins", icon: ShieldCheck },
    ],
  },
  {
    label: "Identity & Access",
    items: [
      { label: "Sessions", href: "/sessions", icon: MonitorSmartphone },
      { label: "Roles & Access", href: "/roles", icon: ShieldCheck },
    ],
  },
  {
    label: "Operations",
    items: [{ label: "Services", href: "/system", icon: LayoutDashboard }],
  },
  {
    label: "Security",
    items: [{ label: "Audit Logs", href: "/audit-logs", icon: ScrollText }],
  },
  {
    label: "System",
    items: [{ label: "Settings", href: "/settings", icon: Settings }],
  },
];
