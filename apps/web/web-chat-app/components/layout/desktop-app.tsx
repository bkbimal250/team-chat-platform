"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/workspace/features/auth/auth-provider";
import { getAccessToken } from "@/lib/auth/session";
import { deviceApi } from "@/features/devices/api";
import { ThemeListener } from "@/features/settings/appearance";
import { AppSection, railItems } from "../navigation/app-nav-config";
import { AppRail } from "./app-rail";
import { MainContent } from "./main-content";
import { OfflineBanner } from "./offline-banner";
import { ConfirmDialog } from "../ui/confirm-dialog";
import { useChatController } from "@/features/chat/use-chat-controller";
import { ChatSecondaryPanel } from "@/features/chat/chat-secondary-panel";
import { ConversationPanel } from "@/features/chat/conversation-panel";
import { NewChatPanel } from "@/features/chat/panels/new-chat-panel";
import { NewContactPanel } from "@/features/chat/panels/new-contact-panel";
import { ConversationProfileSidebar } from "@/features/chat/conversation-profile-sidebar";
import { contactTitle } from "@/features/contacts/use-contacts";
import { EmptyState } from "../ui/empty-state";
import { MessageCircle } from "lucide-react";
import { SettingsSecondaryPanel } from "@/features/settings/settings-secondary-panel";
import { AppShellPanel } from "@/features/settings/app-shell-panel";
import { Conversation } from "@/features/chat/api";
import { contactsApi, type Contact } from "@/features/contacts/api";
import { contactMessageError } from "@/features/contacts/contact-message-error";
import {
  ContactsDetailPanel,
  ContactsListPanel,
  useContactsSelection,
} from "@/features/contacts/contacts-panels";
import { NotificationsListPanel } from "@/features/notifications/notifications-list-panel";
import { NotificationsDetailPanel } from "@/features/notifications/notifications-detail-panel";
import { useNotifications } from "@/features/notifications/use-notifications";
import { WorkspaceListPanel } from "@/features/workspace/workspace-list-panel";
import { WorkspaceResourceMain } from "@/features/workspace/workspace-resource-main";
import type { ResourceRemoteAction } from "@/workspace/features/admin/resource-screen";
import { OverviewContent } from "@/features/workspace/overview-content";
import { Company } from "@/workspace/company";
import { SecondaryPanel } from "./secondary-panel";

export function DesktopApp({
  onSignedOut,
  requested,
  initialSection = "chats",
  initialSettingsPage = "Profile",
}: {
  onSignedOut: () => void;
  requested: Conversation | null;
  initialSection?: AppSection;
  initialSettingsPage?: string;
}) {
  const auth = useAuth();
  const token = getAccessToken();
  const [section, setSection] = useState<AppSection>(initialSection);
  const [settingsPage, setSettingsPage] = useState(initialSettingsPage);
  const [resourceAction, setResourceAction] = useState<ResourceRemoteAction | null>(null);
  const [mobilePane, setMobilePane] = useState<"list" | "main">("list");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(true);
  const contactsCtx = useContactsSelection();
  const [resourceRow, setResourceRow] = useState<{
    id: string;
    [key: string]: string | number | boolean | null | string[];
  } | null>(null);
  const [notificationId, setNotificationId] = useState<string | null>(null);
  const [notifPage, setNotifPage] = useState(0);
  const [chatListMode, setChatListMode] = useState<
    "chats" | "new-chat" | "new-contact"
  >("chats");
  const [contactsListMode, setContactsListMode] = useState<
    "list" | "new-contact"
  >("list");
  const [openingContactId, setOpeningContactId] = useState<string | null>(null);
  const [activeContactId, setActiveContactId] = useState<string | null>(null);
  const [chatProfileOpen, setChatProfileOpen] = useState(false);
  const [groupNotice, setGroupNotice] = useState("");
  const notifFeed = useNotifications(notifPage, Boolean(token));
  const selectedNotice =
    notifFeed.rows.find((row) => row.id === notificationId) ?? null;

  const hasOrg = !!auth.session?.organization_id;
  const personal = !hasOrg;
  const chat = useChatController({
    personal,
    onSignOut: onSignedOut,
    requested,
  });

  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  const visibleRail = useMemo(
    () =>
      railItems.filter((item) => {
        if (item.requiresOrg && !hasOrg) return false;
        if (item.permission && !auth.permissions.has(item.permission)) return false;
        return true;
      }),
    [auth.permissions, hasOrg],
  );

  const selectSection = useCallback((id: AppSection) => {
    if (id === "profile") {
      setSection("settings");
      setSettingsPage("Profile");
      setMobilePane("main");
      return;
    }
    setSection(id);
    if (id !== "chats") setChatListMode("chats");
    if (id !== "contacts") setContactsListMode("list");
    setResourceRow(null);
    setResourceAction(null);
    if (
      [
        "chats",
        "settings",
        "contacts",
        "members",
        "teams",
        "branches",
        "invitations",
        "roles",
        "notifications",
      ].includes(id)
    )
      setMobilePane("list");
    else setMobilePane("main");
    if (id === "settings") setSettingsPage("Profile");
  }, []);

  async function logout() {
    if (!token) {
      onSignedOut();
      return;
    }
    setBusy(true);
    try {
      await deviceApi.logout(token);
      onSignedOut();
    } catch {
      setError("Unable to log out on the server. Check your connection and retry.");
    } finally {
      setBusy(false);
    }
  }

  const chatContact = useMemo(() => {
    if (activeContactId) {
      const pinned = contactsCtx.store.allItems.find((c) => c.id === activeContactId);
      if (pinned) return pinned;
    }
    if (!chat.selected?.title) return null;
    const title = chat.selected.title.trim();
    return (
      contactsCtx.store.allItems.find(
        (c) =>
          contactTitle(c) === title ||
          c.matched_user?.display_name === title,
      ) ?? null
    );
  }, [activeContactId, chat.selected?.title, contactsCtx.store.allItems]);

  useEffect(() => {
    setChatProfileOpen(false);
  }, [chat.selected?.id]);

  const openConversation = useCallback(
    (row: Conversation) => {
      chat.choose(row);
      setSection("chats");
      setChatListMode("chats");
      setMobilePane("main");
      const url = new URL(window.location.href);
      url.searchParams.set("conversation", row.id);
      window.history.replaceState({}, "", url.pathname + url.search);
    },
    [chat],
  );

  const openContactChat = useCallback(
    async (contactId: string) => {
      setActiveContactId(contactId);
      const created = await contactsApi.message(contactId);
      const row: Conversation = {
        id: created.id,
        type: created.type || "DIRECT",
        title: created.title,
        description: created.description ?? null,
        avatar_media_id: created.avatar_media_id ?? null,
        status: created.status || "ACTIVE",
        member_count: created.member_count ?? 2,
        last_message_preview: created.last_message_preview,
        last_message_at: created.last_message_at,
        unread_count: created.unread_count,
      };
      openConversation(row);
      void chat.load();
    },
    [chat, openConversation],
  );

  const openContactFromList = useCallback(
    async (contact: Contact) => {
      contactsCtx.setSelectedId(contact.id);
      if (!contact.matched_user) {
        setMobilePane("main");
        return;
      }
      setOpeningContactId(contact.id);
      contactsCtx.store.setError("");
      try {
        await openContactChat(contact.id);
      } catch (issue) {
        contactsCtx.store.setError(contactMessageError(issue));
        setMobilePane("main");
      } finally {
        setOpeningContactId(null);
      }
    },
    [contactsCtx, openContactChat],
  );

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("conversation");
    if (!id || chat.loading) return;
    const row = chat.conversations.find((c) => c.id === id);
    if (!row || chat.selected?.id === id) return;
    const timer = setTimeout(() => openConversation(row), 0);
    return () => clearTimeout(timer);
  }, [
    chat.conversations,
    chat.loading,
    chat.selected?.id,
    openConversation,
  ]);

  const splitSections: AppSection[] = [
    "chats",
    "contacts",
    "notifications",
    "settings",
    "profile",
    "members",
    "teams",
    "branches",
    "invitations",
    "roles",
  ];

  type WorkspaceResource = "members" | "teams" | "branches" | "invitations" | "roles";

  function workspaceList(resource: WorkspaceResource) {
    return (
      <WorkspaceListPanel
        resource={resource}
        selectedId={resourceRow?.id ?? null}
        onSelect={(row) => {
          setResourceRow(row);
          setMobilePane("main");
        }}
        onAdd={() => setResourceAction({ mode: "create" })}
      />
    );
  }

  function workspaceMain(resource: WorkspaceResource) {
    return (
      <WorkspaceResourceMain
        resource={resource}
        selected={resourceRow}
        action={resourceAction}
        onAction={setResourceAction}
        onModalClose={() => setResourceAction(null)}
      />
    );
  }
  const mobileShowSecondary = splitSections.includes(section) && mobilePane === "list";

  const secondary = (() => {
    switch (section) {
      case "chats":
        if (chatListMode === "new-contact") {
          return (
            <NewContactPanel
              store={contactsCtx.store}
              onBack={() => setChatListMode("new-chat")}
              onSaved={() => setChatListMode("new-chat")}
            />
          );
        }
        if (chatListMode === "new-chat" && token) {
          return (
            <NewChatPanel
              personal={personal}
              token={token}
              store={contactsCtx.store}
              onBack={() => setChatListMode("chats")}
              onNewContact={() => setChatListMode("new-contact")}
              onNewGroup={() =>
                setGroupNotice("Group chats are coming soon. Use New chat for direct messages.")
              }
              onPickContact={(contact) => {
                setChatListMode("chats");
                setMobilePane("main");
                void openContactChat(contact.id);
              }}
              onWorkspaceConversation={(row) => {
                setChatListMode("chats");
                openConversation(row);
                void chat.load();
              }}
            />
          );
        }
        return (
          <ChatSecondaryPanel
            chat={chat}
            onNewChat={() => setChatListMode("new-chat")}
            onNewGroup={() =>
              setGroupNotice("Group chats are coming soon. Use New chat for direct messages.")
            }
          />
        );
      case "contacts":
        if (contactsListMode === "new-contact") {
          return (
            <NewContactPanel
              store={contactsCtx.store}
              onBack={() => setContactsListMode("list")}
              onSaved={(contact) => {
                contactsCtx.setSelectedId(contact.id);
                setContactsListMode("list");
                setMobilePane("main");
              }}
            />
          );
        }
        return (
          <ContactsListPanel
            ctx={contactsCtx}
            openingId={openingContactId}
            onOpenChat={(contact) => void openContactFromList(contact)}
            onAdd={() => {
              contactsCtx.setEditing(null);
              contactsCtx.setFormOpen(false);
              setContactsListMode("new-contact");
            }}
          />
        );
      case "notifications":
        return token ? (
          <NotificationsListPanel
            rows={notifFeed.rows}
            loading={notifFeed.loading}
            error={notifFeed.error}
            page={notifPage}
            hasPrev={notifFeed.hasPrev}
            hasNext={notifFeed.hasNext}
            selectedId={notificationId}
            onSelect={(row) => {
              setNotificationId(row.id);
              setMobilePane("main");
            }}
            onPageChange={(p) => {
              setNotifPage(p);
              setNotificationId(null);
            }}
            onRetry={notifFeed.reload}
          />
        ) : null;
      case "members":
        return workspaceList("members");
      case "teams":
        return workspaceList("teams");
      case "branches":
        return workspaceList("branches");
      case "invitations":
        return workspaceList("invitations");
      case "roles":
        return workspaceList("roles");
      case "overview":
        return (
          <SecondaryPanel title="Workspace">
            <p className="border-b border-aurora-border p-4 text-sm text-aurora-muted">
              Summary and recent activity for your organization.
            </p>
          </SecondaryPanel>
        );
      case "company":
        return (
          <SecondaryPanel title="Company">
            <p className="p-4 text-sm text-aurora-muted">Organization profile and settings.</p>
          </SecondaryPanel>
        );
      case "settings":
      case "profile":
        return (
          <SettingsSecondaryPanel
            displayName={auth.profile?.display_name || ""}
            mediaId={auth.profile?.avatar_media_id}
            activePage={settingsPage}
            onSelect={(page) => {
              setSettingsPage(page);
              setMobilePane("main");
            }}
            onLogout={() => setConfirm(true)}
          />
        );
      default:
        return null;
    }
  })();

  const main = (() => {
    switch (section) {
      case "chats":
        return chat.selected ? (
          <ConversationPanel
            key={chat.selected.id}
            conversation={chat.selected}
            conversations={chat.allConversations}
            token={chat.token}
            memberId={chat.memberId}
            socket={chat.socketRef}
            socketGeneration={chat.socketGeneration}
            onBack={() => {
              chat.setMobileOpen(false);
              setMobilePane("list");
            }}
            onOpenProfile={() => setChatProfileOpen(true)}
            profileAside={
              chatProfileOpen
                ? (
                  <ConversationProfileSidebar
                    conversation={chat.selected}
                    contact={chatContact}
                    onClose={() => setChatProfileOpen(false)}
                  />
                )
                : null
            }
          />
        ) : (
          <ChatWelcome />
        );
      case "contacts":
        return <ContactsDetailPanel ctx={contactsCtx} />;
      case "notifications":
        return token ? (
          <NotificationsDetailPanel
            token={token}
            selected={selectedNotice}
            onConversation={openConversation}
          />
        ) : null;
      case "overview":
        return <OverviewContent onNavigate={selectSection} />;
      case "members":
        return workspaceMain("members");
      case "teams":
        return workspaceMain("teams");
      case "branches":
        return workspaceMain("branches");
      case "invitations":
        return workspaceMain("invitations");
      case "roles":
        return workspaceMain("roles");
      case "company":
        return <Company />;
      case "settings":
      case "profile":
        return (
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <AppShellPanel
              page={settingsPage}
              token={token}
              onConversation={openConversation}
              onSignedOut={onSignedOut}
              onNavigate={setSettingsPage}
              onLogout={() => setConfirm(true)}
            />
          </div>
        );
      default:
        return <ChatWelcome />;
    }
  })();

  if (auth.status !== "ready")
    return <p role="status" className="p-8">Loading account…</p>;

  return (
    <div className="flex h-dvh min-h-0 flex-col overflow-hidden bg-aurora-background text-aurora-text">
      <ThemeListener />
      {!online && (
        <OfflineBanner message="You're offline. Waiting for your connection…" />
      )}
      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        <div className="hidden md:flex">
          <AppRail
            active={section}
            onSelect={selectSection}
            visible={visibleRail}
            displayName={auth.profile?.display_name || "You"}
            mediaId={auth.profile?.avatar_media_id}
            hasOrg={hasOrg}
            notificationCount={0}
          />
        </div>
        <div className="flex min-h-0 min-w-0 flex-1">
          <div
            className={`${mobileShowSecondary ? "flex" : "hidden"} min-h-0 w-full min-w-0 shrink-0 md:flex md:w-auto`}
          >
            {secondary}
          </div>
          <MainContent
            className={`${mobileShowSecondary ? "hidden md:flex" : "flex"} min-h-0`}
          >
            {main}
          </MainContent>
        </div>
        <nav
          aria-label="Mobile navigation"
          className="flex shrink-0 items-center justify-around border-t border-aurora-border bg-aurora-surface px-2 pt-1 pb-[max(0.25rem,env(safe-area-inset-bottom))] md:hidden"
        >
          {visibleRail
            .filter((i) =>
              ["chats", "contacts", "notifications", "settings"].includes(i.id),
            )
            .map((item) => (
              <button
                key={item.id}
                type="button"
                aria-label={item.label}
                title={item.label}
                onClick={() => selectSection(item.id)}
                className={`rounded-lg p-2 ${section === item.id ? "text-aurora-primary" : "text-aurora-muted"}`}
              >
                <item.icon className="size-5" aria-hidden />
              </button>
            ))}
        </nav>
      </div>
      {groupNotice && (
        <ConfirmDialog
          title="Groups"
          busy={false}
          onCancel={() => setGroupNotice("")}
          onConfirm={() => setGroupNotice("")}
        >
          {groupNotice}
        </ConfirmDialog>
      )}
      {confirm && (
        <ConfirmDialog
          title="Log out of GlobalChat?"
          busy={busy}
          onCancel={() => setConfirm(false)}
          onConfirm={() => void logout()}
        >
          {error || "This ends your current session on this device."}
        </ConfirmDialog>
      )}
    </div>
  );
}

function ChatWelcome() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-[linear-gradient(180deg,var(--aurora-surface-alt)_0%,var(--background)_38%)] p-8">
      <EmptyState
        icon={MessageCircle}
        title="GlobalChat"
        detail="Select a conversation to start messaging. Your workspace chats stay in sync across devices."
      />
    </div>
  );
}
