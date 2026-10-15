"""Read-only local physical persistence verification. Only counts/statuses are printed."""

import json
import subprocess
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local"
fixture = json.loads((LOCAL / "invitation-live-check.json").read_text(encoding="utf-8"))
# Never interpolate unchecked browser/test input into SQL.
fixture = {key: str(UUID(value)) for key, value in fixture.items()}
results = {}


def verify(database, label, sql, expected="1"):
    value = subprocess.check_output(
        [
            "docker",
            "compose",
            "--env-file",
            str(LOCAL / "compose.env"),
            "-f",
            str(ROOT / "docker-compose.local.yml"),
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "postgres",
            "-d",
            database,
            "-Atc",
            sql,
        ],
        text=True,
    ).strip()
    results[label] = "PASS" if value == expected else "FAIL"
    print(label, results[label], flush=True)
    if value != expected:
        raise RuntimeError("Physical local database verification failed: " + label)


identity, user, member, org, invitation = [
    fixture[key]
    for key in [
        "identity_id",
        "user_id",
        "member_id",
        "organization_id",
        "invitation_id",
    ]
]
verify(
    "identity_db",
    "identity_phone_unique",
    f"SELECT count(*) FROM identities WHERE phone_number=(SELECT phone_number FROM identities WHERE id='{identity}')",
)
verify(
    "identity_db",
    "identity_active_verified",
    f"SELECT count(*) FROM identities WHERE id='{identity}' AND status='ACTIVE' AND phone_verified",
)
verify(
    "identity_db",
    "onboarding_completed_once",
    f"SELECT count(*) FROM invitation_onboardings WHERE invitation_id='{invitation}' AND identity_id='{identity}' AND member_id='{member}' AND state='COMPLETED' AND verified_code_hash IS NULL",
)
verify(
    "identity_db",
    "identity_migration_head",
    "SELECT version_num FROM alembic_version",
    "0004_invitation_onboarding",
)
verify(
    "teamchat_user_db",
    "user_profile_identity_unique",
    f"SELECT count(*) FROM users WHERE identity_id='{identity}' AND id='{user}'",
)
verify(
    "teamchat_organization_db",
    "membership_identity_tenant_unique",
    f"SELECT count(*) FROM members_member WHERE organization_id='{org}' AND user_id='{identity}' AND id='{member}' AND status='ACTIVE'",
)
verify(
    "teamchat_organization_db",
    "accepted_invitation_binding",
    f"SELECT count(*) FROM invitations_invitation WHERE id='{invitation}' AND status='ACCEPTED' AND accepted_member_id='{member}' AND accepted_at IS NOT NULL AND token_hash IS NOT NULL",
)
verify(
    "teamchat_organization_db",
    "role_assignment_once",
    f"SELECT count(*) FROM roles_roleassignment WHERE member_id='{member}' AND role_id=(SELECT intended_role_id FROM invitations_invitation WHERE id='{invitation}')",
)
verify(
    "teamchat_organization_db",
    "branch_assignment_once",
    f"SELECT count(*) FROM branches_branchmembership WHERE member_id='{member}' AND branch_id='{fixture['branch_id']}' AND left_at IS NULL",
)
verify(
    "teamchat_organization_db",
    "team_assignment_once",
    f"SELECT count(*) FROM teams_teammembership WHERE member_id='{member}' AND team_id='{fixture['team_id']}' AND status='ACTIVE'",
)
verify(
    "teamchat_organization_db",
    "revoked_invitation_no_membership",
    f"SELECT count(*) FROM invitations_invitation WHERE id='{fixture['revoked_invitation_id']}' AND status='REVOKED' AND accepted_member_id IS NULL",
)
verify(
    "teamchat_organization_db",
    "organization_invitation_migration",
    "SELECT count(*) FROM django_migrations WHERE app='invitations' AND name='0002_recipient_onboarding'",
)
(LOCAL / "invitation-database-results.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
