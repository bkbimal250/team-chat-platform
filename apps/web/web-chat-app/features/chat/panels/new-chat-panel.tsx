"use client";

import { UserPlus, Users } from "lucide-react";
import { iconSize } from "@/components/ui/icon-button";
import { AlertBanner } from "@/components/ui/alert-banner";
import { EmptyState } from "@/components/ui/empty-state";
import { PanelHeader } from "@/components/ui/panel-header";
import { SearchField } from "@/components/ui/search-field";
import { UserRound } from "lucide-react";
import type { Contact } from "@/features/contacts/api";
import type { useContacts } from "@/features/contacts/use-contacts";
import { ContactPickerRow } from "./contact-picker-row";
import { NewChatActionRow } from "./new-chat-action-row";
import { WorkspacePeople } from "../workspace-people";
import type { Conversation } from "../api";

type ContactsStore = ReturnType<typeof useContacts>;

export function NewChatPanel({
  personal,
  token,
  store,
  onBack,
  onPickContact,
  onNewContact,
  onNewGroup,
  onWorkspaceConversation,
}: {
  personal: boolean;
  token: string;
  store: ContactsStore;
  onBack: () => void;
  onPickContact: (contact: Contact) => void;
  onNewContact: () => void;
  onNewGroup: () => void;
  onWorkspaceConversation: (row: Conversation) => void;
}) {
  const list = store.filter.trim() ? store.items : store.allItems;

  return (
    <aside
      className="flex w-full shrink-0 flex-col border-r border-aurora-border bg-aurora-surface md:w-[min(100%,400px)] lg:w-[380px]"
    >
      <PanelHeader title="New chat" onBack={onBack} />
      <div className="border-b border-aurora-border p-3">
        <SearchField
          label="Search contacts"
          placeholder="Search name or number"
          value={store.filter}
          onChange={store.setFilter}
        />
      </div>

      {personal ? (
        <>
          <div className="border-b border-aurora-border py-1">
            <NewChatActionRow
              icon={<Users className={iconSize} aria-hidden />}
              title="New group"
              onClick={onNewGroup}
            />
            <NewChatActionRow
              icon={<UserPlus className={iconSize} aria-hidden />}
              title="New contact"
              onClick={onNewContact}
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
              <button
                type="button"
                className="mt-2 text-xs font-semibold text-aurora-primary"
                onClick={() => {
                  store.setError("");
                  store.setRetry((v) => v + 1);
                }}
              >
                Retry
              </button>
            </div>
          )}
          {!store.loading && !store.error && list.length === 0 && (
            <div className="p-6">
              <EmptyState
                icon={UserRound}
                title={store.filter.trim() ? "No matches" : "No saved contacts"}
                detail={
                  store.filter.trim()
                    ? "Try another name or phone number."
                    : "Add a contact to start messaging on GlobalChat."
                }
              />
            </div>
          )}
          <ul className="divide-y divide-aurora-border">
            {list.map((contact) => (
              <li key={contact.id}>
                <ContactPickerRow
                  contact={contact}
                  onPick={() => onPickContact(contact)}
                />
              </li>
            ))}
          </ul>
          {store.hasMore && (
            <div className="p-3">
              <button
                type="button"
                disabled={store.busy}
                onClick={() => void store.loadMore()}
                className="w-full rounded-xl border border-aurora-border py-2 text-sm font-medium"
              >
                Load more contacts
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="flex-1 overflow-y-auto p-3">
          <div className="mb-3 border-b border-aurora-border pb-2">
            <NewChatActionRow
              icon={<Users className={iconSize} aria-hidden />}
              title="New group"
              onClick={onNewGroup}
            />
          </div>
          <WorkspacePeople
            token={token}
            onConversation={onWorkspaceConversation}
            embedded
          />
        </div>
      )}
    </aside>
  );
}
