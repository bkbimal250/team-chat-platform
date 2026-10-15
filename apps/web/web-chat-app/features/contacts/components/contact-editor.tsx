"use client";

import type { CountryCode } from "libphonenumber-js";
import { UserRound } from "lucide-react";
import { iconSize } from "@/components/ui/icon-button";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import type { Contact } from "../api";
import { ContactField } from "./contact-field";
import { ContactPhoneField } from "./contact-phone-field";

export function ContactEditor({
  editing,
  givenName,
  familyName,
  localLabel,
  phone,
  country,
  busy,
  cooldown,
  error,
  onGivenName,
  onFamilyName,
  onLocalLabel,
  onPhone,
  onCountry,
  onCancel,
  onSubmit,
}: {
  editing: Contact | null;
  givenName: string;
  familyName: string;
  localLabel: string;
  phone: string;
  country: CountryCode;
  busy: boolean;
  cooldown: number;
  error?: string;
  onGivenName: (value: string) => void;
  onFamilyName: (value: string) => void;
  onLocalLabel: (value: string) => void;
  onPhone: (value: string) => void;
  onCountry: (value: CountryCode) => void;
  onCancel?: () => void;
  onSubmit: () => void;
}) {
  return (
    <form
      aria-label="Contact form"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
      className="flex flex-col"
    >
      {error && (
        <div className="px-4 pt-3">
          <AlertBanner message={error} />
        </div>
      )}
      <div className="px-4">
        <ContactField
          icon={<span className={`${iconSize} inline-block`} aria-hidden />}
          label="Private name (optional)"
          placeholder="Private name"
          value={localLabel}
          disabled={busy}
          maxLength={200}
          onChange={onLocalLabel}
        />
        <ContactField
          icon={<UserRound className={iconSize} />}
          label="First name"
          placeholder="First name"
          autoComplete="given-name"
          value={givenName}
          disabled={busy}
          onChange={onGivenName}
        />
        <ContactField
          icon={<span className={`${iconSize} inline-block`} aria-hidden />}
          label="Last name"
          placeholder="Last name"
          autoComplete="family-name"
          value={familyName}
          disabled={busy}
          onChange={onFamilyName}
        />
        <ContactPhoneField
          country={country}
          phone={phone}
          disabled={busy}
          required={!editing}
          onCountry={onCountry}
          onPhone={onPhone}
        />
      </div>
      <p className="px-4 pt-4 text-xs leading-relaxed text-aurora-muted">
        We match the full number securely. Your list shows the name and formatted number you save here.
      </p>
      <div className="mt-6 flex flex-wrap gap-2 px-4 pb-4">
        <Button type="submit" variant="primary" disabled={busy || cooldown > 0}>
          {busy ? "Saving…" : editing ? "Save" : "Save contact"}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" disabled={busy} onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
      {cooldown > 0 && (
        <p role="status" className="px-4 pb-4 text-xs text-aurora-muted">
          Please wait {cooldown}s before trying again.
        </p>
      )}
    </form>
  );
}
