import { afterEach, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AdminLiveProvider } from "@/features/admin/live-provider";
import { AdminShell } from "@/components/layout/admin-shell";
import { DashboardClient } from "@/features/dashboard/dashboard-client";
import { ResourceScreen } from "@/features/admin/resource-screen";
import { DevicesClient } from "@/features/devices/devices-client";
import { ProfileClient } from "@/features/settings/profile-client";
import { PersonalSettings } from "@/features/settings/personal-settings";
import { apiRequest, ApiError } from "@/lib/api/client";
import { Modal } from "@/components/ui/modal";
import { useResource } from "@/lib/api/use-resource";
import { RealtimeClient } from "@/lib/realtime/realtime-client";
import { refreshAdmin, ADMIN_REFRESH } from "@/lib/realtime/refresh";
import { saveSession } from "@/lib/auth/session";
import { json, page, tokens } from "./fixtures";
const auth = vi.hoisted(() => ({
  permissions: new Set([
    "member.view",
    "branch.view",
    "team.view",
    "invitation.view",
    "invitation.create",
    "branch.create",
    "branch.update",
    "team.create",
    "team.update",
    "member.update",
    "role.manage",
    "audit.view",
  ]),
  status: "ready",
  session: { organization_id: "org-a", session_id: "session-a" },
  profile: { display_name: "Owner" },
  logout: vi.fn(),
  reload: vi.fn(),
}));
vi.mock("@/features/auth/auth-provider", () => ({ useAuth: () => auth }));
vi.mock("next/navigation", () => ({ usePathname: () => "/users" }));
function setup() {
  saveSession(tokens);
  const fetch = vi.fn(async (url: string, ..._options: RequestInit[]) => {
    void _options;
    return url.includes("organizations/current")
      ? json({ id: "org-a", name: "Acme", display_name: "Acme" })
      : json(
          page(
            url.includes("members")
              ? [
                  {
                    id: "member-a",
                    display_name: "Alice",
                    status: "ACTIVE",
                    designation: "Engineer",
                    branches: ["London"],
                    teams: ["Product"],
                    roles: ["Member"],
                  },
                ]
              : [],
          ),
        );
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}
afterEach(() => vi.useRealTimers());
it("provides active platform navigation and an accessible mobile drawer", async () => {
  setup();
  render(
    <AdminShell>
      <p>Platform content</p>
    </AdminShell>,
  );
  expect(
    screen.getByRole("link", { name: "Users" }).getAttribute("aria-current"),
  ).toBe("page");
  expect(screen.queryByRole("link", { name: "Members" })).toBeNull();
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Open navigation" }));
  expect(screen.getByRole("dialog")).toBeTruthy();
  await user.keyboard("{Escape}");
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(
    screen.getByRole("button", { name: "Open navigation" }),
  );
});
it("renders platform metadata without requiring a company workspace", async () => {
  setup();
  render(<DashboardClient />);
  await screen.findByText("Platform administration");
  expect(screen.getByRole("link", { name: "Organizations" })).toBeTruthy();
  expect(screen.getByRole("link", { name: "Identities" })).toBeTruthy();
});
it("filters members using the actual branch/team/role parameters", async () => {
  const fetch = setup();
  render(<ResourceScreen resource="members" />);
  await screen.findByText("Alice");
  expect(screen.getByText("Engineer")).toBeTruthy();
  expect(screen.getByRole("combobox", { name: "Branch filter" })).toBeTruthy();
  const user = userEvent.setup();
  await user.selectOptions(
    screen.getByRole("combobox", { name: "Status filter" }),
    "SUSPENDED",
  );
  await waitFor(() =>
    expect(
      fetch.mock.calls.some(([url]) => url.includes("status=SUSPENDED")),
    ).toBe(true),
  );
});
it("invalidates only affected tenant resources and cleans up on unmount", async () => {
  const fetch = setup();
  function Probe() {
    const data = useResource<{ results: object[] }>("/api/v1/members/");
    return <p>{data.loading ? "Loading" : "Loaded"}</p>;
  }
  const view = render(<Probe />);
  await screen.findByText("Loaded");
  const count = fetch.mock.calls.length;
  act(() =>
    window.dispatchEvent(
      new CustomEvent(ADMIN_REFRESH, {
        detail: { organizationId: "org-b", resources: ["members"] },
      }),
    ),
  );
  act(() => refreshAdmin(["branches"]));
  expect(fetch.mock.calls.length).toBe(count);
  act(() => refreshAdmin(["members"]));
  await waitFor(() => expect(fetch.mock.calls.length).toBe(count + 1));
  view.unmount();
  act(() => refreshAdmin(["members"]));
  expect(fetch.mock.calls.length).toBe(count + 1);
});
it("traps focus, closes with Escape and restores the initiating control", async () => {
  const user = userEvent.setup();
  const close = vi.fn();
  render(
    <>
      <button>Open</button>
      <Modal open title="Edit branch" onClose={close}>
        <input aria-label="Branch name" />
        <button>Save</button>
      </Modal>
    </>,
  );
  await user.click(screen.getByRole("button", { name: "Save" }));
  await user.keyboard("{Tab}");
  expect(document.activeElement).toBe(
    screen.getByRole("button", { name: "Close dialog" }),
  );
  await user.keyboard("{Escape}");
  expect(close).toHaveBeenCalledOnce();
});
it("uses actual ping frames, reconnects once and ignores duplicate conversation frames", () => {
  vi.useFakeTimers();
  let latest: WebSocket;
  const sockets: WebSocket[] = [];
  const factory = () => {
    latest = {
      readyState: 1,
      send: vi.fn(),
      close: vi.fn(),
    } as unknown as WebSocket;
    sockets.push(latest);
    return latest;
  };
  const state = vi.fn(),
    reconnect = vi.fn();
  const client = new RealtimeClient({
    url: "ws://localhost:8007",
    token: () => "test-token",
    socket: factory,
    onState: state,
    onReconnect: reconnect,
  });
  client.connect();
  sockets[0].onopen?.({} as Event);
  const frame = {
    data: JSON.stringify({
      version: 1,
      type: "message.created.v1",
      payload: {
        conversation_id: "00000000-0000-0000-0000-000000000001",
        message_id: "00000000-0000-0000-0000-000000000002",
      },
    }),
  } as MessageEvent;
  sockets[0].onmessage?.(frame);
  sockets[0].onmessage?.(frame);
  expect(reconnect).not.toHaveBeenCalled();
  vi.advanceTimersByTime(25000);
  expect(sockets[0].send).toHaveBeenCalledWith(
    JSON.stringify({ version: 1, type: "ping" }),
  );
  sockets[0].onclose?.({} as CloseEvent);
  vi.advanceTimersByTime(1000);
  sockets[1].onopen?.({} as Event);
  expect(reconnect).toHaveBeenCalledOnce();
  client.disconnect();
  vi.advanceTimersByTime(60000);
  expect(sockets).toHaveLength(2);
  expect(sockets[1].close).toHaveBeenCalledOnce();
});

it("creates a team using the real schema and confirms server feedback", async () => {
  const fetch = setup();
  render(<ResourceScreen resource="teams" />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Add team" }));
  await user.type(screen.getByLabelText("Name"), "Operations");
  await user.click(screen.getByRole("button", { name: "Save" }));
  await screen.findByText("Teams created.");
  const post = fetch.mock.calls.find(
    (call) => (call[1] as RequestInit | undefined)?.method === "POST",
  );
  expect(post).toBeDefined();
  expect(JSON.parse((post![1] as RequestInit).body as string)).toMatchObject({
    name: "Operations",
    type: "STANDARD",
    branch_id: null,
  });
});
it("shows platform access without requiring a user or organization profile", async () => {
  saveSession(tokens);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      json({ role: "SUPER_ADMIN", permissions: ["platform.access"] }),
    ),
  );
  render(<ProfileClient />);
  expect(await screen.findByText("SUPER_ADMIN")).toBeTruthy();
  expect(screen.getByText("platform.access")).toBeTruthy();
});
it("persists actual privacy preferences without a fake success", async () => {
  saveSession(tokens);
  const fetch = vi.fn(async (url: string, ..._options: RequestInit[]) => {
    void _options;
    return url.includes("privacy")
      ? json({ read_receipts_enabled: true, about_visibility: "ORGANIZATION" })
      : json({ language: "en", timezone: "UTC", theme_preference: "SYSTEM" });
  });
  vi.stubGlobal("fetch", fetch);
  render(<PersonalSettings />);
  const user = userEvent.setup();
  await user.click(await screen.findByLabelText("Share read receipts"));
  await user.click(
    screen.getByRole("button", { name: "Save privacy settings" }),
  );
  await screen.findByText("Personal settings saved.");
  expect(
    JSON.parse(
      fetch.mock.calls.find((call) => call[1]?.method === "PATCH")![1]
        .body as string,
    ),
  ).toEqual({ read_receipts_enabled: false, about_visibility: "ORGANIZATION" });
});
it.each([403, 409, 422, 429, 502])(
  "returns a safe recoverable error for HTTP %s",
  async (status) => {
    saveSession(tokens);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json({}, status)),
    );
    await expect(apiRequest("/api/v1/members/")).rejects.toBeInstanceOf(
      ApiError,
    );
  },
);

it("does not open chat realtime or poll tenant resources from the platform shell", async () => {
  vi.useFakeTimers();
  const fetch = setup();
  function Probe() {
    const data = useResource<unknown>("/api/v1/members/");
    return <p>{data.loading ? "Loading" : "Ready"}</p>;
  }
  const view = render(
    <AdminLiveProvider>
      <Probe />
    </AdminLiveProvider>,
  );
  await act(async () => {});
  expect(screen.getByText("Ready")).toBeTruthy();
  const before = fetch.mock.calls.length;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(30000);
  });
  expect(fetch.mock.calls.length).toBe(before);
  view.unmount();
});

it("requires confirmation before revoking an own device and refetches", async () => {
  saveSession(tokens);
  let status = "ACTIVE";
  const fetch = vi.fn(async (url: string, init: RequestInit) => {
    if (init.method === "POST") {
      status = "REVOKED";
      return json({});
    }
    return json(
      url.includes("/devices")
        ? [
            {
              id: "device-b",
              device_name: "Laptop",
              platform: "WEB",
              status,
              is_current: false,
            },
          ]
        : [],
    );
  });
  vi.stubGlobal("fetch", fetch);
  render(<DevicesClient />);
  const user = userEvent.setup({ delay: null });
  await user.click(await screen.findByRole("button", { name: "Revoke" }));
  expect(fetch.mock.calls.some((call) => call[1].method === "POST")).toBe(
    false,
  );
  await user.click(screen.getByRole("button", { name: "Confirm revoke" }));
  await screen.findByText("REVOKED");
  expect(fetch.mock.calls.find((call) => call[1].method === "POST")![0]).toBe(
    "/api/gateway/api/v1/devices/device-b/revoke",
  );
});
it("preserves a device when revocation is rejected", async () => {
  saveSession(tokens);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit) =>
      init.method === "POST"
        ? json(
            {
              error: { code: "CONFLICT", message: "Device cannot be revoked." },
            },
            409,
          )
        : json(
            url.includes("/devices")
              ? [
                  {
                    id: "device-b",
                    device_name: "Laptop",
                    platform: "WEB",
                    status: "ACTIVE",
                    is_current: false,
                  },
                ]
              : [],
          ),
    ),
  );
  render(<DevicesClient />);
  const user = userEvent.setup({ delay: null });
  await user.click(await screen.findByRole("button", { name: "Revoke" }));
  await user.click(screen.getByRole("button", { name: "Confirm revoke" }));
  await screen.findByText("Device cannot be revoked.");
  expect(screen.getByText("ACTIVE")).toBeTruthy();
});
