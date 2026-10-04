# GlobalChat admin local integration

Target: `apps/admin-web/admin-webchat-app`. Existing Next.js 16.3.6 / React 19.2.8 / TypeScript / Tailwind CSS 4 application.

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8008` in its ignored `.env.local`. No secrets belong in public environment variables. The browser uses the same-origin `/api/gateway` bridge; it forwards bearer authorization to this configured Gateway. This avoids changing backend CORS. Organization trailing slashes are preserved.

Run `npm ci`, `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`. Use `npm run dev -- --port 3000` when free, or `npm run start -- --port 3000` after building. The user-facing chat app needs a different port while the admin occupies 3000.

Session tokens live in per-tab sessionStorage, not URLs or logs. Refresh rotates tokens on one authenticated 401 and retries once; 403 never triggers refresh. Failed logout remains visible and retryable. The admin guard reads real roles and current-member role assignments; buttons reflect permissions, but backend authorization is mandatory.

This is organization administration, not a fictional platform administrator. No global organization list/create, billing plans, system metrics, private-message admin access or cross-user device powers are invented.

See [API routes](ADMIN-API-ROUTES.md), [manual checks](ADMIN-MANUAL-TESTING.md) and [implementation matrix](ADMIN-FRONTEND-STATUS.md).

Company self-registration is available at `/register`; returning phone OTP login remains `/login`. See [onboarding](../onboarding/COMPANY-REGISTRATION.md). Email is contact information, not password authentication.
