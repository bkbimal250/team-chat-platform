"""PostgreSQL composite FKs protect every tenant-to-tenant relationship, including raw SQL."""

from django.db import migrations

RELATIONS = [
    ("teams_team", "branch_id", "branches_branch"),
    ("teams_team", "created_by_member_id", "members_member"),
    ("teams_teammembership", "team_id", "teams_team"),
    ("teams_teammembership", "member_id", "members_member"),
    ("branches_branchmembership", "branch_id", "branches_branch"),
    ("branches_branchmembership", "member_id", "members_member"),
    ("roles_roleassignment", "member_id", "members_member"),
    ("roles_roleassignment", "role_id", "roles_role"),
    ("roles_rolepermission", "role_id", "roles_role"),
    ("invitations_invitation", "team_id", "teams_team"),
    ("invitations_invitation", "branch_id", "branches_branch"),
    ("invitations_invitation", "intended_role_id", "roles_role"),
    ("invitations_invitation", "invited_by_member_id", "members_member"),
    ("invitations_invitation", "accepted_member_id", "members_member"),
    ("audit_auditlog", "actor_member_id", "members_member"),
]
TENANT_TABLES = [
    "organizations_organizationsettings",
    "branches_branch",
    "branches_branchmembership",
    "teams_team",
    "teams_teammembership",
    "members_member",
    "roles_role",
    "roles_rolepermission",
    "roles_roleassignment",
    "invitations_invitation",
]
CHOICES = {
    "organizations_organization": ("status", ["ACTIVE", "SUSPENDED", "DISABLED", "DELETED"]),
    "branches_branch": ("status", ["ACTIVE", "DISABLED", "DELETED"]),
    "teams_team": ("status", ["ACTIVE", "DISABLED", "DELETED"]),
    "members_member": ("status", ["INVITED", "ACTIVE", "SUSPENDED", "LEFT", "REMOVED"]),
    "teams_teammembership": ("status", ["ACTIVE", "LEFT"]),
    "invitations_invitation": ("status", ["PENDING", "ACCEPTED", "EXPIRED", "REVOKED"]),
    "roles_role": ("kind", ["OWNER", "ADMIN", "MANAGER", "MEMBER", "CUSTOM"]),
    "outbox_outboxevent": ("status", ["PENDING", "PROCESSING", "PUBLISHED", "FAILED"]),
}

SQL = """
CREATE FUNCTION deny_tenant_change() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.organization_id IS DISTINCT FROM OLD.organization_id THEN
    RAISE EXCEPTION 'Tenant ownership is immutable' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE FUNCTION deny_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Audit records are append-only' USING ERRCODE='23514';
END $$;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit_auditlog
FOR EACH ROW EXECUTE FUNCTION deny_audit_mutation();
ALTER TABLE audit_auditlog ADD CONSTRAINT audit_actor_requires_tenant CHECK (actor_member_id IS NULL OR organization_id IS NOT NULL);
"""
REVERSE = "ALTER TABLE audit_auditlog DROP CONSTRAINT audit_actor_requires_tenant; DROP TRIGGER audit_append_only ON audit_auditlog; DROP FUNCTION deny_audit_mutation();"
for index, (table, column, target) in enumerate(RELATIONS):
    SQL += f"ALTER TABLE {table} ADD CONSTRAINT tenant_relation_{index} FOREIGN KEY (organization_id, {column}) REFERENCES {target} (organization_id, id) ON DELETE RESTRICT;\n"
    REVERSE += f"ALTER TABLE {table} DROP CONSTRAINT tenant_relation_{index};\n"
for table in TENANT_TABLES:
    SQL += f"CREATE TRIGGER immutable_tenant BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION deny_tenant_change();\n"
    REVERSE += f"DROP TRIGGER immutable_tenant ON {table};\n"
for table, (field, values) in CHOICES.items():
    allowed = ",".join(f"'{value}'" for value in values)
    SQL += (
        f"ALTER TABLE {table} ADD CONSTRAINT {table}_valid_choice CHECK ({field} IN ({allowed}));\n"
    )
    REVERSE += f"ALTER TABLE {table} DROP CONSTRAINT {table}_valid_choice;\n"
REVERSE += "DROP FUNCTION deny_tenant_change();"


class Migration(migrations.Migration):
    dependencies = [
        (app, "0001_initial")
        for app in [
            "organizations",
            "branches",
            "teams",
            "members",
            "roles",
            "invitations",
            "audit",
            "outbox",
        ]
    ]
    operations = [migrations.RunSQL(SQL, REVERSE)]
