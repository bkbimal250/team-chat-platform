# Member password onboarding

Owner/admin creates an invitation with Name, Email, optional Phone, Role and optional Branch/Team. Organization retains its tenant permission, delegation, capacity, expiration, revocation and assignment validation. Local delivery returns the existing private development link, `/join#invite=<opaque-token>`. Share it privately. No paid email delivery or SMS is configured by this task.

Employee opens that link and enters the invited email, password and confirmation. A new account chooses a 12–128 character password. An existing email/password account supplies its current password: Identity authenticates it without replacing the hash. Existing OTP-only accounts require a future legitimate password setup/recovery path; they receive the generic credentials error now.

`POST /api/v1/auth/invitations/password` accepts `token`, `email`, `password`, `device` (existing login schema). Extra organization/member/team/role fields are rejected. Identity validates the token through Organization and compares normalized recipient email, commits a durable acceptance intent, provisions the User profile and calls the private `accept-email` Organization action. That action rechecks token, current inviter authority, tenant, role and assignment state under the existing locks. Browser traffic goes through Gateway; the private action is never exposed through it.

Acceptance marks the invitation single-use and creates only the authorized membership. An interrupted VERIFIED intent retries with the same token and authenticated password; Organization's same-identity accepted response is idempotent. Completed replay is rejected. Different identities cannot reuse an accepted invitation. The employee gets the normal SessionService tokens and web chat; returning email/password login selects the same membership.

The invitation token is removed from the browser URL and not persisted by the UI. Permanent employee passwords are never selected by or displayed to administrators. Phone fields remain in the existing models/invitation data, unverified; invitation acceptance does not treat typed phone or email as verification proof.
