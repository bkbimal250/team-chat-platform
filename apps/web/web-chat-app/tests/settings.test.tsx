import { afterEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiRequest } from "@/lib/api/client";
import { NotificationSettings } from "@/features/notifications/settings";
import { NotificationInbox } from "@/features/notifications/inbox";
import { ProfileSettings } from "@/features/settings/profile-settings";
import { Appearance } from "@/features/settings/appearance";

const { apiRequestMock, WorkspaceApiError } = vi.hoisted(() => ({
  apiRequestMock: vi.fn(),
  WorkspaceApiError: class ApiError extends Error {
    status?: number;
    constructor(message: string, status?: number) {
      super(message);
      this.status = status;
    }
  },
}));

vi.mock("@/lib/api/client", () => ({ apiRequest: apiRequestMock }));
vi.mock("@/workspace/lib/api/client", () => ({
  apiRequest: apiRequestMock,
  ApiError: WorkspaceApiError,
}));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
  localStorage.clear();
});

it("notification settings persist only supported fields", async () => {
  apiRequestMock
    .mockResolvedValueOnce({ push_enabled: true, preview: "FULL" })
    .mockResolvedValueOnce({ push_enabled: false, preview: "NONE" });
  render(<NotificationSettings token="token" />);
  await screen.findByLabelText("Message push notifications");
  fireEvent.click(screen.getByLabelText("Message push notifications"));
  fireEvent.change(screen.getByLabelText("Content visibility"), {
    target: { value: "NONE" },
  });
  await screen.findByText("Save preferences");
  fireEvent.click(screen.getByText("Save preferences"));
  await screen.findByText("Preferences saved.");
  expect(apiRequest).toHaveBeenLastCalledWith(
    "/api/v1/notifications/preferences",
    {
      method: "PATCH",
      body: JSON.stringify({
        push_enabled: false,
        notification_preview: "NONE",
      }),
    },
    "token",
  );
});

it("permission already granted is never requested again", async () => {
  const requestPermission = vi.fn();
  vi.stubGlobal("Notification", { permission: "granted", requestPermission });
  apiRequestMock.mockResolvedValue({ push_enabled: true, preview: "FULL" });
  render(<NotificationSettings token="token" />);
  await screen.findByText("granted");
  expect(screen.queryByText("Allow notifications")).toBeNull();
  expect(requestPermission).not.toHaveBeenCalled();
});

it("inbox opens real conversation and preserves hidden previews", async () => {
  apiRequestMock.mockImplementation((path: string) => {
    if (path.startsWith("/api/v1/notifications")) {
      return Promise.resolve([
        {
          id: "n",
          conversation_id: "c",
          message_id: "m",
          title: "Private title",
          body: "Private body",
          preview_mode: "NONE",
        },
      ]);
    }
    return Promise.resolve({ id: "c" });
  });
  const open = vi.fn();
  render(<NotificationInbox token="token" onConversation={open} />);
  await screen.findByRole("button", { name: /Workspace notification/i });
  fireEvent.click(
    screen.getAllByRole("button", { name: "Open conversation" })[0],
  );
  await waitFor(() => expect(open).toHaveBeenCalledWith({ id: "c" }));
  expect(screen.queryByText("Private body")).toBeNull();
});

it("profile edit uses actual user contract", async () => {
  apiRequestMock
    .mockResolvedValueOnce({ display_name: "Member", about: "Hello" })
    .mockResolvedValueOnce({ display_name: "Updated", about: "Hello" });
  render(<ProfileSettings token="token" />);
  const input = await screen.findByLabelText("Display name");
  fireEvent.change(input, { target: { value: "Updated" } });
  fireEvent.click(screen.getByText("Save changes"));
  await screen.findByText("Changes saved.");
  expect(apiRequest).toHaveBeenLastCalledWith(
    "/api/v1/users/me",
    {
      method: "PATCH",
      body: JSON.stringify({ display_name: "Updated", about: "Hello" }),
    },
    "token",
  );
});

it("appearance persists locally and applies dark theme", async () => {
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  render(<Appearance />);
  fireEvent.click(screen.getByLabelText("dark"));
  expect(localStorage.getItem("globalchat.theme")).toBe("dark");
  expect(document.documentElement.dataset.theme).toBe("dark");
});

it("contact discoverability uses the existing private settings endpoint", async () => {
  apiRequestMock
    .mockResolvedValueOnce({
      profile_photo_visibility: "NOBODY",
      about_visibility: "NOBODY",
      online_status_visibility: "NOBODY",
      last_seen_visibility: "NOBODY",
      read_receipts_enabled: true,
      discoverable: true,
    })
    .mockResolvedValueOnce({ discoverable: false });
  render(<ProfileSettings token="token" privacy />);
  fireEvent.click(
    await screen.findByLabelText("Allow exact phone contact discovery"),
  );
  fireEvent.click(screen.getByText("Save changes"));
  await screen.findByText("Changes saved.");
  const call = apiRequestMock.mock.calls.at(-1)!;
  expect(call[0]).toBe("/api/v1/users/me/privacy");
  expect(JSON.parse(String(call[1]?.body)).discoverable).toBe(false);
});
