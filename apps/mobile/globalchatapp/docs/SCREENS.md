# Screens

## Auth flow

| Route | Screen |
|-------|--------|
| `/splash` | Session restore |
| `/login` | Email/password |
| `/register` | Personal registration |
| `/otp-login` | Phone OTP |
| `/forgot-password` | Reset request |
| `/reset-password` | Token + new password |
| `/session-expired` | Re-auth prompt |
| `/device-setup` | E2EE bootstrap + key upload |

## Main shell (`/home/*`)

| Tab | Route | Data |
|-----|-------|------|
| Chats | `/home/chats` | `GET /api/v1/conversations` |
| Updates | `/home/updates` | Phase 3+ |
| Contacts | `/home/contacts` | Contacts API |
| Workspace | `/home/workspace` | `POST /api/v1/auth/context` (org switch) |
| Settings | `/home/settings` | Local + logout |

## Chat flows

| Route | Purpose |
|-------|---------|
| `/new-chat` | Pick contact → `POST .../personal/direct` |
| `/new-group` | Contacts → `POST .../personal/groups` or `.../groups` |
| `/chat/:id` | E2EE messaging + realtime refresh |
| `/chat/:id/group-info` | Members, leave, remove |
| `/search` | Client filter over chats + contacts |
