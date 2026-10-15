import { it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ResourceScreen } from "@/workspace/features/admin/resource-screen";
import { saveSession } from "@/workspace/lib/auth/session";
import { tokens, json, page } from "./workspace-fixtures";
// Isolate tenant resource behavior awaiting its move to the Company Workspace.
// Platform authorization has separate deny-by-default integration tests.
vi.mock("@/workspace/features/auth/auth-provider", () => ({
  useAuth: () => ({ permissions: new Set(["branch.view", "branch.create", "branch.update"]) }),
}));
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace: vi.fn() }) }));
function prepare(
  branchResponse: Response,
  mutation?: (init: RequestInit) => Response,
) {
  saveSession(tokens);
  const fetch = vi.fn(async (url: string, init: RequestInit) => {
    if (url.includes("role-assignments"))
      return json(
        page([{ id: "assignment", member: "member-a", role: "role-a" }]),
      );
    if (url.includes("/roles/"))
      return json(
        page([
          {
            id: "role-a",
            name: "Owner",
            kind: "OWNER",
            permissions: ["branch.view", "branch.create", "branch.update"],
          },
        ]),
      );
    if (url.includes("/users/me"))
      return json({
        user_id: "user-a",
        display_name: "Alice",
        status: "ACTIVE",
      });
    if (url.includes("/branches/"))
      return init.method === "POST"
        ? (mutation?.(init) ?? json({ id: "created" }, 201))
        : branchResponse.clone();
    return json({});
  });
  vi.stubGlobal("fetch", fetch);
  render(
    <ResourceScreen resource="branches" />,
  );
  return fetch;
}
it("renders backend branch data without demo records", async () => {
  prepare(
    json(
      page([
        {
          id: "b1",
          name: "Real local branch",
          code: "R1",
          country: "IN",
          status: "ACTIVE",
        },
      ]),
    ),
  );
  expect(await screen.findByText("Real local branch")).toBeTruthy();
  expect(screen.queryByText("Mumbai HQ")).toBeNull();
});
it("shows an empty state for a real empty result", async () => {
  prepare(json(page()));
  expect(await screen.findByText("No matching records found.")).toBeTruthy();
});
it("shows backend errors and retry without fabricating rows", async () => {
  prepare(json({ message: "Backend unavailable" }, 503));
  expect(await screen.findByText("Backend unavailable")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
});
it("submits an actual branch schema and renders backend validation errors", async () => {
  const user = userEvent.setup();
  const fetch = prepare(json(page()), () =>
    json({ code: ["Code already exists."] }, 400),
  );
  await user.click(await screen.findByRole("button", { name: "Add branch" }));
  await user.type(screen.getByRole("textbox", { name: "Name" }), "New branch");
  await user.type(screen.getByRole("textbox", { name: "Code" }), "NEW");
  await user.type(screen.getByRole("textbox", { name: "Country code" }), "IN");
  await user.click(screen.getByRole("button", { name: "Save" }));
  expect(await screen.findByText("code: Code already exists.")).toBeTruthy();
  const call = fetch.mock.calls.find(([, init]) => init.method === "POST");
  expect(call).toBeTruthy();
  expect(JSON.parse(String(call?.[1].body))).toEqual({
    name: "New branch",
    code: "NEW",
    country: "IN",
    city: null,
  });
  expect(screen.getByRole("dialog")).toBeTruthy();
});
it("requires confirmation before disabling a branch", async () => {
  const user = userEvent.setup();
  const fetch = prepare(
    json(
      page([
        {
          id: "b1",
          name: "Real branch",
          code: "R1",
          country: "IN",
          status: "ACTIVE",
        },
      ]),
    ),
  );
  await user.click(await screen.findByRole("button", { name: "Disable" }));
  expect(
    fetch.mock.calls.filter(([, init]) => init.method === "POST"),
  ).toHaveLength(0);
  expect(screen.getByRole("dialog", { name: "Confirm change" })).toBeTruthy();
  await user.click(screen.getByRole("button", { name: "Confirm" }));
  await waitFor(() =>
    expect(
      fetch.mock.calls.some(
        ([url, init]) =>
          url.includes("/b1/lifecycle/") && init.method === "POST",
      ),
    ).toBe(true),
  );
});
