"use client";

import { useEffect, useRef, useState } from "react";
import type { CountryCode } from "libphonenumber-js";
import { ApiError } from "@/workspace/lib/api/client";
import { isAbortError, safeAbort } from "@/workspace/lib/api/abort";
import {
  formatPhoneDisplay,
  registrationPhone,
} from "@/workspace/features/auth/country-phone";
import { contactsApi, type Contact } from "./api";

export function useContacts() {
  const [items, setItems] = useState<Contact[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [retry, setRetry] = useState(0);
  const [cooldown, setCooldown] = useState(0);
  const [filter, setFilter] = useState("");
  const mounted = useRef(false);
  const lock = useRef(false);

  useEffect(() => {
    mounted.current = true;
    const abort = new AbortController();
    const startRequest = window.setTimeout(() => {
    setLoading(true);
    setError("");
    void contactsApi
      .list(undefined, abort.signal)
      .then((page) => {
        if (abort.signal.aborted) return;
        if (!Array.isArray(page.items)) throw new Error("Invalid contact response");
        setItems(page.items);
        setCursor(page.next_cursor);
        setLoading(false);
      })
      .catch((e) => {
        if (abort.signal.aborted || isAbortError(e)) return;
        setError(
          e instanceof ApiError && e.status === 429
            ? "Too many contact checks. Please wait before retrying."
            : "Contacts could not be loaded. Please retry.",
        );
        if (e instanceof ApiError && e.status === 429)
          setCooldown(e.retryAfter ?? 60);
        setLoading(false);
      });
    }, 0);
    return () => {
      window.clearTimeout(startRequest);
      mounted.current = false;
      safeAbort(abort);
    };
  }, [retry]);

  useEffect(() => {
    if (!cooldown) return;
    const timer = setTimeout(
      () => setCooldown((v) => Math.max(0, v - 1)),
      1000,
    );
    return () => clearTimeout(timer);
  }, [cooldown]);

  function failure(e: unknown) {
    if (e instanceof ApiError && e.status === 429) {
      setCooldown(e.retryAfter ?? 60);
      setError("Too many contact checks. Please wait before retrying.");
    } else
      setError(
        e instanceof ApiError
          ? e.message
          : "The change could not be saved. Please retry.",
      );
  }

  async function save(
    editing: Contact | null,
    fields: {
      givenName: string;
      familyName: string;
      localLabel: string;
      phone: string;
      country: CountryCode;
    },
  ) {
    if (lock.current || cooldown) return;
    lock.current = true;
    setBusy(true);
    setError("");
    setStatus("");
    try {
      const given = fields.givenName.trim() || null;
      const family = fields.familyName.trim() || null;
      const phoneDisplay =
        fields.phone.trim()
          ? formatPhoneDisplay(fields.phone, fields.country)
          : null;
      const phone = registrationPhone(fields.phone, fields.country);
      const payload = {
        phone,
        country: fields.country,
        given_name: given,
        family_name: family,
        phone_display: phoneDisplay,
        local_label:
          fields.localLabel.trim() ||
          [given, family].filter(Boolean).join(" ") ||
          null,
      };
      const contact = editing
        ? await contactsApi.update(editing.id, {
            given_name: given,
            family_name: family,
            local_label: payload.local_label,
            ...(fields.phone.trim()
              ? {
                  phone: payload.phone,
                  country: fields.country,
                  phone_display: phoneDisplay,
                }
              : {}),
          })
        : await contactsApi.add(payload);
      if (!mounted.current) return;
      setItems((prev) => [
        contact,
        ...prev.filter((item) => item.id !== contact.id),
      ]);
      setStatus(
        contact.matched_user
          ? "Contact saved. Registered on GlobalChat."
          : "Contact saved. Not on GlobalChat or unavailable.",
      );
      return contact;
    } catch (e) {
      if (mounted.current) failure(e);
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(false);
    }
  }

  async function remove(contact: Contact): Promise<boolean> {
    if (lock.current) return false;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await contactsApi.remove(contact.id);
      if (mounted.current) {
        setItems((prev) => prev.filter((item) => item.id !== contact.id));
        setStatus(
          "Contact removed. Their account and workspace membership are unchanged.",
        );
      }
      return true;
    } catch (e) {
      if (mounted.current) failure(e);
      return false;
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(false);
    }
  }

  async function loadMore() {
    if (lock.current || !cursor) return;
    lock.current = true;
    setBusy(true);
    try {
      const page = await contactsApi.list(cursor);
      if (mounted.current) {
        setItems((prev) => [
          ...prev,
          ...page.items.filter((item) => !prev.some((o) => o.id === item.id)),
        ]);
        setCursor(page.next_cursor);
      }
    } catch (e) {
      if (mounted.current) failure(e);
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(false);
    }
  }

  const filtered = items.filter((item) => matchesContactQuery(item, filter));

  return {
    items: filtered,
    allItems: items,
    loading,
    error,
    busy,
    status,
    cooldown,
    filter,
    setFilter,
    setError,
    setStatus,
    setRetry,
    save,
    remove,
    loadMore,
    hasMore: !!cursor,
    lock,
  };
}

export function contactTitle(item: Contact) {
  const parts = [item.given_name, item.family_name].filter(Boolean);
  if (parts.length) return parts.join(" ");
  return item.local_label || item.matched_user?.display_name || "Saved contact";
}

export function contactSubtitle(item: Contact) {
  if (item.phone_display) {
    if (item.matched_user) {
      return `${item.phone_display} · On GlobalChat`;
    }
    return item.phone_display;
  }
  if (item.matched_user) {
    return item.matched_user.phone_verified
      ? "On GlobalChat · Verified"
      : "On GlobalChat";
  }
  return "Not on GlobalChat or unavailable";
}

function matchesContactQuery(item: Contact, filter: string) {
  const q = filter.trim().toLowerCase();
  if (!q) return true;
  const name = contactTitle(item).toLowerCase();
  if (name.includes(q)) return true;
  if (item.phone_display?.toLowerCase().includes(q)) return true;
  const digits = q.replace(/\D/g, "");
  if (digits.length >= 2) {
    const hay = [
      item.given_name ?? "",
      item.family_name ?? "",
      item.local_label ?? "",
      item.phone_display ?? "",
      item.matched_user?.display_name ?? "",
    ].join(" ");
    if (hay.replace(/\D/g, "").includes(digits)) return true;
  }
  return false;
}
