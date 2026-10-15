# Company email registration

Use admin `/register`. Fields: Company name, Owner name, Email, Phone with searchable country calling code, Password and Confirm password. Create Company submits once; no OTP screen or SMS occurs. Password confirmation is a frontend check; the authoritative API validates names, canonical email, phone and password policy.

`POST /api/v1/auth/registration/company` through Gateway accepts `company_name`, `owner_name`, `email`, `phone`, `password`, `device`. Success is 201 with the existing TokenResponse. Exact constraints and device schema are in [Identity](../services/IDENTITY-API.md). Do not include confirmation in the API body.

Identity hashes the password and commits a durable CompanyRegistration intent with fixed Identity/organization IDs before server-to-server provisioning. User creates the Owner profile idempotently; Organization atomically creates the organization, Owner membership/role and its normal audit/outbox. No cross-service database writes are used. Session issuance follows provisioning.

An advisory lock plus database uniqueness serialize canonical email submissions. Completed duplicates return a controlled 409; use Sign In. A failed provisioning attempt can be retried with the same email/password and original company/name/phone. It resumes the same intent and IDs; never repeatedly submit a different company to work around an error. The UI prevents double-click submissions. Unverified contact fields are not represented as verified.

Migration `0005_email_password` follows Identity `0004_invitation_onboarding`, adds nullable password credentials, canonical email uniqueness and nullable OTP challenge references for email-only intents. Existing OTP data/migrations remain. Conflicting historical canonical emails cause migration failure instead of silent merging. Downgrade refuses while OTP-less intents exist, rather than deleting data.

After success admin validates actual role permissions and opens Dashboard. Logout and email/password login restore the same organization/member. See [the manual company test](../manual-testing/02-COMPANY-REGISTRATION.md).
