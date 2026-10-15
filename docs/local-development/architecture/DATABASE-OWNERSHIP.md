Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Database ownership
Each of the seven persistent domains owns its separate database listed in 03-DATABASES.md. Consumers update local projections only. User Service remains authoritative for profiles; Organization for memberships; Identity for sessions. No cross-service direct writes in normal runtime. Explicit local seed invokes operator commands solely in domain databases.


## Secure employee onboarding (2026-10-05)

Organization owns recipient invitations and assignments (invitations.0002_recipient_onboarding). Identity owns invitation_onboardings intents (0004_invitation_onboarding), phone proof and sessions. User owns profiles; generic internal provisioning does not overwrite an existing profile. Service-authenticated HTTP coordinates the saga; no cross-service DB writes.
