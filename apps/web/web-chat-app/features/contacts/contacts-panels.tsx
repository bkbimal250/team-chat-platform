"use client";

import { useEffect, useRef, useState } from "react";
import type { CountryCode } from "libphonenumber-js";
import { MoreVertical, Pencil, Plus, Trash2, UserRound } from "lucide-react";
import { SecondaryPanel } from "@/components/layout/secondary-panel";
import { Avatar } from "@/components/ui/avatar";
import { AlertBanner } from "@/components/ui/alert-banner";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { DetailScaffold } from "@/components/ui/detail-scaffold";
import { EmptyState } from "@/components/ui/empty-state";
import { IconButton, iconSize } from "@/components/ui/icon-button";
import { ListRow } from "@/components/ui/list-row";
import { SearchField } from "@/components/ui/search-field";
import type { Contact } from "./api";
import { ContactUnavailablePanel } from "./contact-unavailable-panel";
import { ContactsWelcome } from "./contacts-welcome";
import { ContactEditor } from "./components/contact-editor";
import { contactSubtitle, contactTitle, useContacts } from "./use-contacts";

export function useContactsSelection() {
  const store = useContacts();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Contact | null>(null);
  const [givenName, setGivenName] = useState("");
  const [familyName, setFamilyName] = useState("");
  const [localLabel, setLocalLabel] = useState("");
  const [phone, setPhone] = useState("");
  const [country, setCountry] = useState<CountryCode>("IN");
  const selected =
    store.allItems.find((c) => c.id === selectedId) ?? null;

  function clearForm() {
    setGivenName("");
    setFamilyName("");
    setLocalLabel("");
    setPhone("");
    setCountry("IN");
  }

  function beginAdd() {
    clearForm();
    setEditing(null);
    setFormOpen(true);
  }

  function beginEdit(contact: Contact) {
    setSelectedId(contact.id);
    setGivenName(contact.given_name ?? "");
    setFamilyName(contact.family_name ?? "");
    setLocalLabel(contact.local_label ?? "");
    setPhone("");
    setCountry("IN");
    setEditing(contact);
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditing(null);
    clearForm();
  }

  return {
    store,
    selectedId: selected?.id ?? null,
    setSelectedId,
    selected,
    formOpen,
    setFormOpen,
    editing,
    setEditing,
    givenName,
    setGivenName,
    familyName,
    setFamilyName,
    localLabel,
    setLocalLabel,
    phone,
    setPhone,
    country,
    setCountry,
    beginAdd,
    beginEdit,
    closeForm,
  };
}

export function ContactsListPanel({
  ctx,
  onAdd,
  onOpenChat,
  openingId,
}: {
  ctx: ReturnType<typeof useContactsSelection>;
  onAdd: () => void;
  onOpenChat?: (contact: Contact) => void;
  openingId?: string | null;
}) {
  const { store, selectedId, setSelectedId } = ctx;
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [removing, setRemoving] = useState<Contact | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!openMenuId) return;
    function onPointerDown(event: PointerEvent) {
      if (event.target instanceof Node && !menuRef.current?.contains(event.target)) {
        setOpenMenuId(null);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpenMenuId(null);
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [openMenuId]);

  async function deleteContact(contact: Contact) {
    const deleted = await store.remove(contact);
    if (deleted && selectedId === contact.id) setSelectedId(null);
    setRemoving(null);
  }

  return (
    <SecondaryPanel
      title="Contacts"
      actions={
        <IconButton label="Add contact" onClick={onAdd} className="text-aurora-primary">
          <Plus className={iconSize} />
        </IconButton>
      }
    >
      <div className="border-b border-aurora-border p-3">
        <SearchField
          label="Search contacts"
          placeholder="Search name or number"
          value={store.filter}
          onChange={store.setFilter}
        />
      </div>
      {store.loading && (
        <p role="status" className="animate-pulse p-4 text-sm text-aurora-muted">
          Loading contacts…
        </p>
      )}
      {store.error && (
        <div className="p-3">
          <AlertBanner message={store.error} />
          {store.cooldown > 0 && <p className="text-xs">Try again in {store.cooldown}s.</p>}
          <button
            type="button"
            disabled={store.busy || store.cooldown > 0}
            onClick={() => {
              store.setError("");
              store.setRetry((v) => v + 1);
            }}
            className="mt-2 text-xs font-semibold underline"
          >
            Refresh contacts
          </button>
        </div>
      )}
      {!store.loading && !store.error && store.filter && !store.items.length && store.allItems.length > 0 && (
        <p className="p-4 text-sm text-aurora-muted">No contacts match your search.</p>
      )}
      {!store.loading && !store.allItems.length && !store.error && (
        <div className="p-6">
          <EmptyState
            icon={UserRound}
            title="No contacts yet"
            detail="Use Add contact above to save a phone number and see if they are on GlobalChat."
          />
        </div>
      )}
      <ul className="divide-y divide-aurora-border">
        {store.items.map((item) => (
          <li key={item.id} className="relative flex items-center pr-2">
            <div className="min-w-0 flex-1">
              <ListRow
                active={selectedId === item.id || openingId === item.id}
                onClick={() => {
                  setOpenMenuId(null);
                  setSelectedId(item.id);
                  onOpenChat?.(item);
                }}
                leading={<Avatar name={contactTitle(item)} mediaId={item.matched_user?.avatar_media_id} />}
                title={contactTitle(item)}
                subtitle={
                  openingId === item.id
                    ? "Opening chat…"
                    : contactSubtitle(item)
                }
              />
            </div>
            <div
              ref={openMenuId === item.id ? menuRef : undefined}
              className="relative shrink-0"
            >
              <IconButton
                label={`More actions for ${contactTitle(item)}`}
                aria-haspopup="menu"
                aria-expanded={openMenuId === item.id}
                disabled={store.busy}
                onClick={() =>
                  setOpenMenuId((current) => current === item.id ? null : item.id)
                }
              >
                <MoreVertical className={iconSize} />
              </IconButton>
              {openMenuId === item.id && (
                <div
                  role="menu"
                  aria-label={`${contactTitle(item)} actions`}
                  className="absolute right-0 top-full z-20 min-w-36 rounded-xl border border-aurora-border bg-aurora-surface p-1 shadow-lg"
                >
                  <button
                    type="button"
                    role="menuitem"
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-aurora-surface-alt"
                    onClick={() => {
                      setOpenMenuId(null);
                      ctx.beginEdit(item);
                    }}
                  >
                    <Pencil className="size-4" aria-hidden />
                    Edit
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-rose-600 hover:bg-aurora-surface-alt"
                    onClick={() => {
                      setOpenMenuId(null);
                      setRemoving(item);
                    }}
                  >
                    <Trash2 className="size-4" aria-hidden />
                    Delete
                  </button>
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
      {store.hasMore && (
        <div className="p-3">
          <Button variant="outline" disabled={store.busy} onClick={() => void store.loadMore()}>
            Load more contacts
          </Button>
        </div>
      )}
        {removing && (
          <ConfirmDialog
            title="Delete saved contact?"
            busy={store.busy}
            onCancel={() => setRemoving(null)}
            onConfirm={() => void deleteContact(removing)}
          >
            Only your private contact entry is deleted.
          </ConfirmDialog>
        )}
    </SecondaryPanel>
  );
}

export function ContactsDetailPanel({
  ctx,
  onEdit,
  onRemove,
}: {
  ctx: ReturnType<typeof useContactsSelection>;
  onEdit?: (contact: Contact) => void;
  onRemove?: (contact: Contact) => void;
}) {
  const {
    store,
    selected,
    formOpen,
    editing,
    givenName,
    setGivenName,
    familyName,
    setFamilyName,
    localLabel,
    setLocalLabel,
    phone,
    setPhone,
    country,
    setCountry,
  } = ctx;
  const [removing, setRemoving] = useState<Contact | null>(null);

  function beginEdit(contact: Contact) {
    ctx.beginEdit(contact);
  }

  async function submitForm() {
    const saved = await store.save(editing, {
      givenName,
      familyName,
      localLabel,
      phone,
      country,
    });
    if (saved) {
      ctx.closeForm();
      ctx.setSelectedId(saved.id);
    }
  }

  if (formOpen && (editing || !selected)) {
    return (
      <DetailScaffold
        width="narrow"
        title={editing ? "Edit contact" : "Add contact"}
        subtitle="Private to you — numbers are matched securely, not stored in plain text."
      >
        {store.status && <p role="status" className="mb-4 text-sm text-aurora-muted">{store.status}</p>}
        <ContactEditor
          editing={editing}
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
          onCancel={
            store.allItems.length
              ? ctx.closeForm
              : undefined
          }
          onSubmit={() => void submitForm()}
        />
      </DetailScaffold>
    );
  }

  if (!selected) {
    return <ContactsWelcome />;
  }

  if (!selected.matched_user) {
    return (
      <>
        <ContactUnavailablePanel
          contact={selected}
          busy={store.busy}
          onEdit={() => {
            if (onEdit) onEdit(selected);
            else beginEdit(selected);
          }}
          onRemove={() => {
            if (onRemove) onRemove(selected);
            else setRemoving(selected);
          }}
        />
        {removing && (
          <ConfirmDialog
            title="Delete saved contact?"
            busy={store.busy}
            onCancel={() => setRemoving(null)}
            onConfirm={async () => {
              const deleted = await store.remove(removing);
              if (deleted) ctx.setSelectedId(null);
              setRemoving(null);
            }}
          >
            Only your private contact entry is deleted.
          </ConfirmDialog>
        )}
      </>
    );
  }

  return <ContactsWelcome />;
}
