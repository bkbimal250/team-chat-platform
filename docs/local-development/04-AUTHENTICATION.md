# Local authentication — email/password primary

Email/password is enabled by the local runner. Phone OTP is disabled for normal onboarding and login; its providers, data and tests remain. Read [the authoritative policy and rate limits](onboarding/EMAIL-PASSWORD-AUTH.md), [company signup](onboarding/COMPANY-EMAIL-REGISTRATION.md), and [employee onboarding](onboarding/MEMBER-PASSWORD-ONBOARDING.md). No OTP/SMS is sent by these flows.

Identity owns normalized login email and Argon2id hashes. Existing JWT/session/device/refresh/logout architecture is shared by both methods. Email and phone verification remain false unless actually proven. Password reset is not implemented; existing OTP-only accounts are not given passwords automatically. No authentication bypass or normal-member admin access is introduced.
