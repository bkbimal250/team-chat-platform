export type Tokens = {
  access_token: string;
  refresh_token: string | null;
  organization_id: string | null;
  member_id: string | null;
  device_id: string;
  session_id: string;
  expires_in: number;
};
export type CursorPage<T> = {
  results: T[];
  next: string | null;
  previous: string | null;
};
export type Organization = {
  id: string;
  name: string;
  display_name: string;
  slug: string;
  status: string;
  email: string | null;
  timezone: string;
  country_code: string;
  created_at: string;
};
export type Member = {
  id: string;
  display_name: string;
  employee_code: string | null;
  designation: string | null;
  department: string | null;
  status: string;
  user_id: string | null;
  organization: string;
  created_at: string;
};
export type Branch = {
  id: string;
  name: string;
  code: string;
  country: string;
  city: string | null;
  status: string;
  organization: string;
  created_at: string;
};
export type Team = {
  id: string;
  name: string;
  description: string | null;
  type: string;
  status: string;
  organization: string;
  created_at: string;
};
export type Invitation = {
  id: string;
  intended_role_id: string;
  status: string;
  expires_at: string;
  created_at: string;
};
export type Role = {
  id: string;
  name: string;
  kind: string;
  permissions: string[];
};
export type RoleAssignment = { id: string; member: string; role: string };
export type Audit = {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  created_at: string;
};
export type Device = {
  id: string;
  device_name: string;
  platform: string;
  status: string;
  last_seen_at: string | null;
  first_seen_at: string;
  is_current: boolean;
};
export type UserProfile = {
  avatar_media_id?: string | null;
  avatar_expires_at?: string | null;
  user_id: string;
  display_name: string;
  status: string;
};
export type NotificationPreferences = {
  push_enabled: boolean;
  preview: string;
};
export type OrganizationSettings = {
  allow_member_invites: boolean;
  allow_group_creation: boolean;
  allow_external_chat: boolean;
  default_timezone: string;
  max_members: number | null;
  max_teams: number | null;
};

export type IdentitySession = {
  id: string;
  device_id: string;
  platform: string;
  device_name: string;
  status: string;
  created_at: string;
  last_activity_at: string;
  is_current: boolean;
};
export type Notification = {
  id: string;
  conversation_id: string;
  message_id: string;
  title: string;
  body: string;
  preview_mode: string;
};
