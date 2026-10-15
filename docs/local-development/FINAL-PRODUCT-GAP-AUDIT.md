# Final product gap audit — updated 2026-10-11

This document tracked pre-personal-account gaps. **Personal accounts, optional-org login, personal conversations, gateway ingress, and cross-service `member.*.v2` revocation are implemented** in the services layer.

## Still follow dedicated guides

- Personal accounts: `PERSONAL-ACCOUNTS.md` (if present in repo docs)
- Member invitations: `MEMBER-INVITATION-TESTING.md`
- Platform topology: `docs/platform/TOPOLOGY.md`
- Event contracts: `docs/platform/EVENT_CONTRACT_MATRIX.md`

## Remaining product/policy items (not service blockers)

- Production email/SMS delivery providers (development OTP/email abstractions exist)
- VPS/terraform deployment automation (see `infrastructure/terraform`)
- Policy review: ordinary members creating workspace groups, custom role permissions

Use live integration scripts under `scripts/local/` (for example `verify_personal_chat.py`, `smoke.py`) with `GLOBALCHAT_INTEGRATION_URL` when the Docker stack is running.
