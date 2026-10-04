export type Field = {
  name: string;
  label: string;
  required?: boolean;
  maxLength?: number;
  type?: "text" | "datetime-local";
  options?: string[];
  pattern?: string;
};
export type ResourceConfig = {
  resource: string;
  title: string;
  columns: { key: string; label: string }[];
  fields: Field[];
  search?: boolean;
  statuses?: string[];
  permission: string;
  readPermission: string;
  lifecycle?: "member" | "resource" | "invitation";
  create?: boolean;
  edit?: boolean;
};
const name: Field = {
  name: "name",
  label: "Name",
  required: true,
  maxLength: 200,
};
export const configs: Record<string, ResourceConfig> = {
  branches: {
    resource: "branches",
    title: "Branches",
    columns: [
      { key: "name", label: "Name" },
      { key: "code", label: "Code" },
      { key: "country", label: "Country" },
      { key: "status", label: "Status" },
    ],
    fields: [
      name,
      { name: "code", label: "Code", required: true, maxLength: 50 },
      {
        name: "country",
        label: "Country code",
        required: true,
        maxLength: 2,
        pattern: "[A-Za-z]{2}",
      },
      { name: "city", label: "City", maxLength: 100 },
    ],
    search: true,
    statuses: ["ACTIVE", "DISABLED", "DELETED"],
    permission: "branch",
    readPermission: "branch.view",
    lifecycle: "resource",
    create: true,
    edit: true,
  },
  teams: {
    resource: "teams",
    title: "Teams",
    columns: [
      { key: "name", label: "Name" },
      { key: "type", label: "Type" },
      { key: "status", label: "Status" },
    ],
    fields: [
      name,
      { name: "description", label: "Description" },
      {
        name: "type",
        label: "Type",
        options: ["STANDARD", "DEPARTMENT", "PROJECT"],
      },
    ],
    search: true,
    statuses: ["ACTIVE", "DISABLED", "DELETED"],
    permission: "team",
    readPermission: "team.view",
    lifecycle: "resource",
    create: true,
    edit: true,
  },
  members: {
    resource: "members",
    title: "Members",
    columns: [
      { key: "display_name", label: "Member" },
      { key: "employee_code", label: "Employee code" },
      { key: "department", label: "Department" },
      { key: "status", label: "Status" },
    ],
    fields: [
      {
        name: "display_name",
        label: "Display name",
        required: true,
        maxLength: 200,
      },
      { name: "employee_code", label: "Employee code", maxLength: 50 },
      { name: "designation", label: "Designation", maxLength: 100 },
      { name: "department", label: "Department", maxLength: 100 },
    ],
    search: true,
    statuses: ["INVITED", "ACTIVE", "SUSPENDED", "LEFT", "REMOVED"],
    permission: "member",
    readPermission: "member.view",
    lifecycle: "member",
    create: true,
    edit: true,
  },
  invitations: {
    resource: "invitations",
    title: "Invitations",
    columns: [
      { key: "id", label: "Invitation" },
      { key: "status", label: "Status" },
      { key: "expires_at", label: "Expires" },
    ],
    fields: [
      { name: "intended_role_id", label: "Intended role", required: true },
      {
        name: "expires_at",
        label: "Expires at",
        required: true,
        type: "datetime-local",
      },
    ],
    statuses: ["PENDING", "ACCEPTED", "EXPIRED", "REVOKED"],
    permission: "invitation",
    readPermission: "invitation.view",
    lifecycle: "invitation",
    create: true,
  },
  "audit-logs": {
    resource: "audit-logs",
    title: "Audit logs",
    columns: [
      { key: "action", label: "Action" },
      { key: "resource_type", label: "Resource" },
      { key: "created_at", label: "Recorded" },
    ],
    fields: [],
    permission: "audit",
    readPermission: "audit.view",
  },
  roles: {
    resource: "roles",
    title: "Roles",
    columns: [
      { key: "name", label: "Role" },
      { key: "kind", label: "Kind" },
      { key: "permissions", label: "Permissions" },
    ],
    fields: [],
    permission: "role",
    readPermission: "role.view",
  },
};
export function formPayload(
  fields: Field[],
  values: Record<string, string>,
): Record<string, string | null> {
  return Object.fromEntries(
    fields.map((field) => [
      field.name,
      field.type === "datetime-local"
        ? new Date(values[field.name]).toISOString()
        : values[field.name] || null,
    ]),
  );
}
