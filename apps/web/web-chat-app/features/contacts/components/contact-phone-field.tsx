"use client";

import { Phone } from "lucide-react";
import type { CountryCode } from "libphonenumber-js";
import countryData from "@/workspace/features/auth/countries.json";
import { iconSize } from "@/components/ui/icon-button";

const countries = countryData as {
  code: CountryCode;
  name: string;
  dial: string;
}[];

export function ContactPhoneField({
  country,
  phone,
  disabled,
  required,
  onCountry,
  onPhone,
}: {
  country: CountryCode;
  phone: string;
  disabled?: boolean;
  required?: boolean;
  onCountry: (code: CountryCode) => void;
  onPhone: (value: string) => void;
}) {
  const dial = countries.find((item) => item.code === country)?.dial ?? "";
  return (
    <div className="flex gap-4 border-b border-aurora-border py-3">
      <Phone className={`${iconSize} mt-2 shrink-0 text-aurora-muted`} aria-hidden />
      <div className="flex min-w-0 flex-1 gap-3">
        <label className="shrink-0">
          <span className="sr-only">Country</span>
          <select
            disabled={disabled}
            value={country}
            onChange={(event) => onCountry(event.target.value as CountryCode)}
            className="max-w-[6.5rem] border-0 bg-transparent py-1 text-sm font-medium text-aurora-text focus-visible:outline-none"
          >
            {countries.map((item) => (
              <option key={item.code} value={item.code}>
                {item.code} +{item.dial}
              </option>
            ))}
          </select>
        </label>
        <label className="min-w-0 flex-1">
          <span className="sr-only">Phone</span>
          <input
            type="tel"
            inputMode="tel"
            autoComplete="tel-national"
            required={required}
            disabled={disabled}
            value={phone}
            maxLength={32}
            placeholder="Phone"
            onChange={(event) => onPhone(event.target.value)}
            className="w-full border-0 bg-transparent py-1 text-sm text-aurora-text placeholder:text-aurora-muted focus-visible:outline-none"
          />
        </label>
      </div>
      {dial && (
        <span className="sr-only">
          Selected country calling code +{dial}
        </span>
      )}
    </div>
  );
}
