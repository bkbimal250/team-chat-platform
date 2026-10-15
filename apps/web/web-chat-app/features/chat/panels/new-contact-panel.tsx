"use client";

import { useState } from "react";
import type { CountryCode } from "libphonenumber-js";
import { PanelHeader } from "@/components/ui/panel-header";
import { ContactEditor } from "@/features/contacts/components/contact-editor";
import type { Contact } from "@/features/contacts/api";
import type { useContacts } from "@/features/contacts/use-contacts";

type ContactsStore = ReturnType<typeof useContacts>;

export function NewContactPanel({
  store,
  onBack,
  onSaved,
}: {
  store: ContactsStore;
  onBack: () => void;
  onSaved: (contact: Contact) => void;
}) {
  const [givenName, setGivenName] = useState("");
  const [familyName, setFamilyName] = useState("");
  const [localLabel, setLocalLabel] = useState("");
  const [phone, setPhone] = useState("");
  const [country, setCountry] = useState<CountryCode>("IN");

  async function submit() {
    const saved = await store.save(null, {
      givenName,
      familyName,
      localLabel,
      phone,
      country,
    });
    if (saved) {
      setGivenName("");
      setFamilyName("");
      setLocalLabel("");
      setPhone("");
      onSaved(saved);
    }
  }

  return (
    <aside
      className="flex w-full shrink-0 flex-col border-r border-aurora-border bg-aurora-surface md:w-[min(100%,400px)] lg:w-[380px]"
    >
      <PanelHeader title="New contact" onBack={onBack} />
      <div className="flex-1 overflow-y-auto">
        <ContactEditor
          editing={null}
          givenName={givenName}
          familyName={familyName}
          localLabel={localLabel}
          phone={phone}
          country={country}
          busy={store.busy}
          cooldown={store.cooldown}
          error={store.error || undefined}
          onGivenName={setGivenName}
          onFamilyName={setFamilyName}
          onLocalLabel={setLocalLabel}
          onPhone={setPhone}
          onCountry={setCountry}
          onCancel={onBack}
          onSubmit={() => void submit()}
        />
      </div>
    </aside>
  );
}
