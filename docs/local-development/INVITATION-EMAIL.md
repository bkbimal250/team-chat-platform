# Invitation and account email delivery

Local invitations expose a private development link through the existing delivery-provider boundary. Email verification and password recovery use digest-only expiring challenges and development-only token responses. These are development facilities, not proof that production email is delivered.

No production invitation/account email provider has been configured or tested. Add a secure environment-configured delivery adapter in Phase 6; preserve expiry, revocation, anti-enumeration, single use and secret-free logs. Never send email while running this Phase 1 verification.
