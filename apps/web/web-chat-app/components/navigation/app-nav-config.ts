import type { LucideIcon } from "lucide-react";
import {
  Bell,
  Building2,
  GitBranch,
  HelpCircle,
  LayoutDashboard,
  Mail,
  MessageCircle,
  Palette,
  Settings,
  Shield,
  Smartphone,
  User,
  UserRound,
  Users,
  UsersRound,
} from "lucide-react";

export type AppSection =
  | "chats"
  | "contacts"
  | "notifications"
  | "overview"
  | "members"
  | "teams"
  | "branches"
  | "invitations"
  | "roles"
  | "company"
  | "settings"
  | "profile";

export type RailItem = {
  id: AppSection;
  label: string;
  icon: LucideIcon;
  group: "primary" | "workspace" | "bottom";
  permission?: string;
  requiresOrg?: boolean;
};

export const railItems: RailItem[] = [
  { id: "chats", label: "Chats", icon: MessageCircle, group: "primary" },
  { id: "contacts", label: "Contacts", icon: UserRound, group: "primary" },
  { id: "notifications", label: "Notifications", icon: Bell, group: "primary" },
  {
    id: "overview",
    label: "Overview",
    icon: LayoutDashboard,
    group: "workspace",
    requiresOrg: true,
  },
  {
    id: "members",
    label: "Members",
    icon: Users,
    group: "workspace",
    requiresOrg: true,
    permission: "member.view",
  },
  {
    id: "teams",
    label: "Teams",
    icon: UsersRound,
    group: "workspace",
    requiresOrg: true,
    permission: "team.view",
  },
  {
    id: "branches",
    label: "Branches",
    icon: GitBranch,
    group: "workspace",
    requiresOrg: true,
    permission: "branch.view",
  },
  {
    id: "invitations",
    label: "Invitations",
    icon: Mail,
    group: "workspace",
    requiresOrg: true,
    permission: "invitation.view",
  },
  {
    id: "roles",
    label: "Roles",
    icon: Shield,
    group: "workspace",
    requiresOrg: true,
    permission: "role.view",
  },
  {
    id: "company",
    label: "Company",
    icon: Building2,
    group: "bottom",
    requiresOrg: true,
    permission: "organization.view",
  },
  { id: "profile", label: "Profile", icon: User, group: "bottom" },
  { id: "settings", label: "Settings", icon: Settings, group: "bottom" },
];

export type SettingsMenuItem = {
  label: string;
  page: string;
  icon: LucideIcon;
};

export const settingsMenuItems: SettingsMenuItem[] = [
  { label: "Profile", page: "Profile", icon: User },
  { label: "Account", page: "Settings / Account", icon: User },
  { label: "Privacy", page: "Settings / Privacy", icon: Shield },
  { label: "Notifications", page: "Settings / Notifications", icon: Bell },
  { label: "Devices", page: "Linked Devices", icon: Smartphone },
  { label: "Appearance", page: "Settings / Appearance", icon: Palette },
  { label: "Help", page: "Settings / Help", icon: HelpCircle },
];
