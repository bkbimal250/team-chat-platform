# Active authentication for this checklist

Start with email/password company registration or an email-bound member invitation. No OTP step applies while AUTH_PHONE_OTP_ENABLED=false. See [company](02-COMPANY-REGISTRATION.md), [login](03-AUTHENTICATION.md), and [employee setup](../onboarding/MEMBER-PASSWORD-ONBOARDING.md). Any historical phone/OTP step below is future-capability testing only.

# End-to-end

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Owner registers and verifies → creates branch/team → invites employee → Incognito phone OTP join → authorized membership → people/direct chat → two-way HTTP/realtime/typing/receipts → unread/preview → logout/returning login with same identity/member → revoke separate invitation. Disposable local data only. See ../testing/END-TO-END-TESTING.md.

## Every applicable endpoint

Follow chapters02–13 in order.

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
