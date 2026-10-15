"use client";
import { Conversation } from "@/features/chat/api";
import { WorkspacePeople } from "@/features/chat/workspace-people";
export function People({
  token,
  onConversation,
}: {
  token: string;
  onConversation: (row: Conversation) => void;
}) {
  return (
    <section>
      <h1 className="text-2xl font-semibold sm:text-3xl">Workspace Members</h1>
      <WorkspacePeople token={token} onConversation={onConversation} />
    </section>
  );
}
