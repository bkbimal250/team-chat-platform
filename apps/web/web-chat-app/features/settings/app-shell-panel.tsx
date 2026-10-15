"use client";

import { Conversation } from "@/features/chat/api";
import { LinkedDevices } from "@/features/devices/linked-devices";
import { NotificationInbox } from "@/features/notifications/inbox";
import { NotificationSettings } from "@/features/notifications/settings";
import { People } from "@/components/people";
import { ContentPage } from "@/components/layout/content-page";
import { Appearance } from "./appearance";
import { ProfileSettings } from "./profile-settings";
import { AccountSettings } from "./account-settings";
import { HelpContent } from "./help-content";
import { SettingsHome } from "./settings-home";

export function AppShellPanel({
  page,
  token,
  onConversation,
  onSignedOut,
  onNavigate,
  onLogout,
}: {
  page: string;
  token: string | null;
  onConversation: (row: Conversation) => void;
  onSignedOut: () => void;
  onNavigate: (page: string) => void;
  onLogout: () => void;
}) {
  if (page === "Workspace Members" && token) {
    return (
      <ContentPage>
        <People
          token={token}
          onConversation={(row) => {
            onConversation(row);
            onNavigate("Chats");
          }}
        />
      </ContentPage>
    );
  }
  if (page === "Linked Devices" && token) {
    return <LinkedDevices token={token} onSignedOut={onSignedOut} />;
  }
  if (page === "Profile" && token) {
    return <ProfileSettings token={token} />;
  }
  if (page === "Notifications" && token) {
    return (
      <NotificationInbox
        token={token}
        onConversation={(row) => {
          onConversation(row);
          onNavigate("Chats");
        }}
      />
    );
  }
  if (page === "Settings / Notifications" && token) {
    return <NotificationSettings token={token} />;
  }
  if (page === "Settings / Privacy" && token) {
    return <ProfileSettings token={token} privacy />;
  }
  if (page === "Settings / Appearance") {
    return <Appearance />;
  }
  if (page === "Settings / Help") {
    return <HelpContent />;
  }
  if (page === "Settings / Account" && token) {
    return (
      <AccountSettings
        token={token}
        onDevices={() => onNavigate("Linked Devices")}
        onLogout={onLogout}
      />
    );
  }
  return <SettingsHome onSelect={onNavigate} />;
}
