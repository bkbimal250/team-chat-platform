import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { WorkspacePeople } from "../features/chat/workspace-people";
import * as client from "../lib/api/client";
it("person selection sends the server member ID, never the user ID", async () => {
 const member = "550e8400-e29b-41d4-a716-446655440000";
 const api = vi.spyOn(client, "apiRequest").mockResolvedValueOnce({ users: [{ user_id: "different-user", member_id: member, display_name: "Ada", status: "ACTIVE" }] }).mockResolvedValueOnce({ id: "conversation", type: "DIRECT" });
 const open = vi.fn(); render(<WorkspacePeople token="test" onConversation={open}/>);
 fireEvent.change(screen.getByLabelText("Search people"), { target: { value: "Ada" } }); fireEvent.click(screen.getByRole("button", { name: "Search" })); await screen.findByText("Ada"); fireEvent.click(screen.getByRole("button", { name: "Chat" }));
 await waitFor(() => expect(open).toHaveBeenCalledWith({ id: "conversation", type: "DIRECT" })); expect(api.mock.calls[1][1]?.body).toBe(JSON.stringify({ member_id: member }));
});
