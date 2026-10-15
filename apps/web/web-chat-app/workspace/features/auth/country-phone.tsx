"use client";
import {
  parsePhoneNumberFromString,
  type CountryCode,
} from "libphonenumber-js";
import { useState } from "react";
import countryData from "./countries.json";
const countries = countryData as {
  code: CountryCode;
  name: string;
  dial: string;
}[];
export function registrationPhone(value: string, country: CountryCode): string {
  const phone = parsePhoneNumberFromString(value.trim(), country);
  if (!phone?.isValid())
    throw new Error("Enter a valid phone number for the selected country.");
  return phone.number;
}

export function formatPhoneDisplay(value: string, country: CountryCode): string {
  const phone = parsePhoneNumberFromString(value.trim(), country);
  if (phone?.isValid()) return phone.formatInternational();
  const trimmed = value.trim();
  return trimmed.length <= 40 ? trimmed : trimmed.slice(0, 40);
}
export function CountryPhone({
  value,
  country,
  onChange,
  onCountryChange,
  disabled,
  legend = "Owner phone number",
  required = true,
  help,
}: {
  value: string;
  country: CountryCode;
  onChange: (value: string) => void;
  onCountryChange: (value: CountryCode) => void;
  disabled: boolean;
  legend?: string;
  required?: boolean;
  help?: string;
}) {
  const [search, setSearch] = useState("");
  const query = search.trim().toLowerCase();
  const filtered = countries.filter((item) =>
    `${item.name} ${item.code} +${item.dial}`.toLowerCase().includes(query),
  );
  const options = filtered.some((item) => item.code === country)
    ? filtered
    : [countries.find((item) => item.code === country)!, ...filtered];
  const fieldClass =
    "mt-1 w-full rounded-xl border border-aurora-border bg-aurora-surface px-3 py-2 text-sm text-aurora-text placeholder:text-aurora-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-aurora-primary";
  return (
    <fieldset className="space-y-3" disabled={disabled}>
      <legend className="text-sm font-medium text-aurora-text">{legend}</legend>
      <label className="block text-sm font-medium text-aurora-text">
        Country
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by name or +code…"
          className={fieldClass}
        />
      </label>
      {filtered.length === 0 && (
        <p role="status" className="text-sm text-aurora-muted">
          No matching countries. Your selected country is unchanged.
        </p>
      )}
      <div className="grid gap-3 sm:grid-cols-[1fr_1.2fr]">
        <label className="block text-sm font-medium text-aurora-text">
          Region
          <select
            value={country}
            onChange={(event) =>
              onCountryChange(event.target.value as CountryCode)
            }
            className={fieldClass}
          >
            {options.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name} (+{item.dial})
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-medium text-aurora-text">
          Phone number
          <input
            required={required}
            type="tel"
            inputMode="tel"
            autoComplete="tel-national"
            maxLength={32}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            aria-describedby="registration-phone-help"
            placeholder="Mobile number"
            className={fieldClass}
          />
        </label>
      </div>
      <p id="registration-phone-help" className="text-xs leading-relaxed text-aurora-muted">
        {help ?? "Include your country code or pick a region first. You can paste a full international number starting with +."}
      </p>
    </fieldset>
  );
}
