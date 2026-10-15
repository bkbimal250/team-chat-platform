import { apiRequest } from "@/workspace/lib/api/client";
import type { Conversation } from "@/features/chat/api";
export type MatchedUser = {
  user_id: string;
  display_name: string;
  avatar_media_id: string | null;
  phone_verified: boolean;
};
export type Contact = {
  id: string;
  local_label: string | null;
  given_name: string | null;
  family_name: string | null;
  phone_display: string | null;
  matched_user: MatchedUser | null;
  created_at: string;
  updated_at: string;
};
export type ContactPage = { items: Contact[]; next_cursor: string | null };
export type ContactInput = {
  phone: string;
  country: string;
  local_label?: string | null;
  given_name?: string | null;
  family_name?: string | null;
  phone_display?: string | null;
};

/** Matches user-service `ContactCreate` / `ContactPatch` (extra fields forbidden). */
export function buildContactPayload(input: ContactInput): ContactInput {
  const phone = input.phone.trim();
  const country = input.country.trim().toUpperCase();
  const given = input.given_name?.trim() || undefined;
  const family = input.family_name?.trim() || undefined;
  const local =
    input.local_label?.trim() ||
    [given, family].filter(Boolean).join(" ").trim() ||
    undefined;
  const payload: ContactInput = { phone, country };
  if (local) payload.local_label = local;
  if (given) payload.given_name = given;
  if (family) payload.family_name = family;
  if (input.phone_display?.trim()) {
    payload.phone_display = sanitizePhoneDisplay(input.phone_display.trim());
  }
  return payload;
}

export function sanitizePhoneDisplay(value: string): string {
  return value.replace(/[^\d\s+\-().]/g, "").slice(0, 40);
}

const path = "/api/v1/contacts";
export const contactsApi = {
  message: (contact_id: string) =>
    apiRequest<Conversation & { created?: boolean }>(
      "/api/v1/conversations/personal/direct",
      { method: "POST", body: JSON.stringify({ contact_id }) },
    ),
  list: (after?: string, signal?: AbortSignal) =>
    apiRequest<ContactPage>(path, { query: { after }, signal }),
  add: (body: ContactInput) =>
    apiRequest<Contact>(path, {
      method: "POST",
      body: JSON.stringify(buildContactPayload(body)),
    }),
  update: (id: string, body: Partial<ContactInput>) => {
    const patch: Partial<ContactInput> = {};
    if (body.phone?.trim()) patch.phone = body.phone.trim();
    if (body.country?.trim()) patch.country = body.country.trim().toUpperCase();
    if (body.local_label !== undefined)
      patch.local_label = body.local_label?.trim() || null;
    if (body.given_name !== undefined)
      patch.given_name = body.given_name?.trim() || null;
    if (body.family_name !== undefined)
      patch.family_name = body.family_name?.trim() || null;
    if (body.phone_display !== undefined) {
      patch.phone_display = body.phone_display?.trim()
        ? sanitizePhoneDisplay(body.phone_display.trim())
        : null;
    }
    return apiRequest<Contact>(path + "/" + encodeURIComponent(id), {
      method: "PATCH",
      body: JSON.stringify(patch),
    });
  },
  remove: (id: string) =>
    apiRequest<{ deleted: boolean }>(path + "/" + encodeURIComponent(id), {
      method: "DELETE",
    }),
};
