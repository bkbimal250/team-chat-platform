import { GlobalChatApp } from "@/components/globalchat-app";

export default function Page() {
  return (
    <GlobalChatApp
      initialSection="settings"
      initialSettingsPage="Settings / Appearance"
    />
  );
}
