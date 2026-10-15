"use client";
import { parsePhoneNumberFromString, type CountryCode } from "libphonenumber-js";
import { useState } from "react";
import countryData from "./countries.json";
const countries = countryData as { code: CountryCode; name: string; dial: string }[];
export function registrationPhone(value: string, country: CountryCode): string {
  const phone = parsePhoneNumberFromString(value.trim(), country);
  if (!phone?.isValid()) throw new Error("Enter a valid phone number for the selected country.");
  return phone.number;
}
export function CountryPhone({ value, country, onChange, onCountryChange, disabled }: { value: string; country: CountryCode; onChange: (value: string) => void; onCountryChange: (value: CountryCode) => void; disabled: boolean }) {
 const [search, setSearch] = useState("");
 const query = search.trim().toLowerCase();
 const filtered = countries.filter(item => `${item.name} ${item.code} +${item.dial}`.toLowerCase().includes(query));
 const options = filtered.some(item => item.code === country) ? filtered : [countries.find(item => item.code === country)!, ...filtered];
 return <fieldset className="space-y-2" disabled={disabled}>
  <legend className="font-medium">Owner phone number</legend>
  <label className="block text-sm">Search country or calling code
   <input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="India, United Kingdom, +44…" className="mt-1 w-full rounded border p-3 focus-visible:outline-indigo-600" />
  </label>
  {filtered.length === 0 && <p role="status" className="text-sm text-slate-600">No matching countries. Your selected country is unchanged.</p>}
  <div className="grid gap-3 sm:grid-cols-2">
   <label className="block text-sm">Country calling code
    <select value={country} onChange={event => onCountryChange(event.target.value as CountryCode)} className="mt-1 w-full rounded border bg-white p-3 focus-visible:outline-indigo-600">
     {options.map(item => <option key={item.code} value={item.code}>{item.name} (+{item.dial})</option>)}
    </select>
   </label>
   <label className="block text-sm">Phone Number
    <input required type="tel" inputMode="tel" autoComplete="tel-national" maxLength={32} value={value} onChange={event => onChange(event.target.value)} aria-describedby="registration-phone-help" placeholder="Your phone number" className="mt-1 w-full rounded border p-3 focus-visible:outline-indigo-600" />
   </label>
  </div>
  <p id="registration-phone-help" className="text-xs text-slate-600">Select your country and enter your number. You can also paste a complete international number starting with +. This number is retained for future phone authentication.</p>
 </fieldset>;
}
