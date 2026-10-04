# Company registration

Registration uses phone OTP, not email/password authentication. Email is normalized and unique in Identity but remains unverified; it is not a login credential. Existing member registration remains `invite_only`.

## Service ownership and recovery

Identity owns the short-lived company-registration challenge, OTP and identity/session. Pending registration contains authoritative company/owner names, normalized phone/email and a server-generated organization ID. No organization is created at start. PostgreSQL contact advisory locks serialize concurrent starts; existing phone/email identities are rejected. Verification accepts only registration ID, OTP and device, never company details or an organization ID.

After provider verification, Identity commits a durable VERIFIED intent and PENDING identity with unique phone/email. It uses authenticated internal HTTP to provision User first, then Organization. User owns its profile/preferences/privacy and transactional outbox; Organization atomically provisions its organization/settings/owner membership/backend OWNER role/audit/outbox using the existing provisioning command. The assigned organization UUID is the idempotency key, protected by PostgreSQL advisory locking. User provisioning locks the identity reference and retries never reset a profile. Identity becomes ACTIVE and creates its normal session/outbox only after both services confirm provisioning.

This is a durable saga, not a cross-database transaction. A remote step may commit before a later failure. Those rows belong to a tracked VERIFIED intent and are recovered using the same IDs; they are not deleted or recreated. A PENDING identity cannot sign in. Failed OTP attempts are committed, so retries cannot reset attempt limits. Verified retries require the same code, stored only as an Argon2 hash, with attempt limits and a 30-minute bounded recovery window. COMPLETED verification is rejected; returning login authenticates instead of creating another company. A lost final network response is handled by normal login.

For an already VERIFIED intent beyond the retry window, a trusted local operator can run, from repository root:

```powershell
python -c "import sys; sys.path.insert(0,'scripts/local'); from dev import run; run('identity',['-m','app.recover_registration','REGISTRATION_UUID'],'registration-recovery.log')"
```

This command is restricted to development and loopback PostgreSQL port 5434. It cannot recover an unverified intent, issues no tokens and sends no SMS. It resumes service-owned provisioning, then the owner signs in via normal OTP. Recovery is idempotent. No public recovery bypass or production operator command is added.

## Local migration and runtime

Identity migration `0003_company_registration` follows `0002_vonage_verify_request_mapping`; it creates only the durable registration table. Organization/User reuse existing tables. Migration was upgraded locally and verified at head. Identity requires `USER_SERVICE_URL` in addition to its existing Organization URL/internal token. The local runner configures both. Production deployment and configuration are outside this task.

DevelopmentOTPProvider is used locally. Production uses the existing provider abstraction; no provider credentials or OTP values are logged. Public calls go through Gateway. Internal provisioning routes are not exposed by Gateway. Registration of an arbitrary verified phone always creates a NEW company; it cannot join an existing one. Invitation delivery remains a separate feature.
