import { afterEach, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { Contacts } from "@/features/contacts/contacts";
import { contactsApi } from "@/features/contacts/api";
import { ApiError } from "@/workspace/lib/api/client";
const { push } = vi.hoisted(() => ({push: vi.fn()}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));
vi.mock("@/workspace/features/auth/auth-provider", () => ({
  useAuth: () => ({ session: { organization_id: null } }),
}));
vi.mock("@/features/contacts/api", () => ({
  contactsApi: {
    message: vi.fn(),
    list: vi.fn(),
    add: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));
const contact = {
  id: "c",
  local_label: "Office friend",
  given_name: null,
  family_name: null,
  phone_display: null,
  matched_user: {
    user_id: "b",
    display_name: "Actual profile",
    avatar_media_id: null,
    phone_verified: false,
  },
  created_at: "2026-10-08T00:00:00Z",
  updated_at: "2026-10-08T00:00:00Z",
};
afterEach(() => vi.resetAllMocks());
it("lists private labels and truthful unverified association", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [contact],
    next_cursor: null,
  });
  render(<Contacts />);
  await screen.findByText("Office friend");
  expect(screen.getByText("On GlobalChat")).toBeTruthy();
  expect(screen.queryByText("Actual profile")).toBeNull();
  expect(screen.queryByText("Start chat")).toBeNull();
});
it("empty book has no invented contacts", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [],
    next_cursor: null,
  });
  render(<Contacts />);
  await screen.findByText(/No contacts yet/);
});
it("manual country entry sends canonical phone and private label", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [],
    next_cursor: null,
  });
  vi.mocked(contactsApi.add).mockResolvedValue(contact);
  render(<Contacts />);
  await screen.findByText(/No contacts yet/);
  fireEvent.click(screen.getByRole("button", {name:"Add contact"}));
  fireEvent.change(screen.getByLabelText("Private name (optional)"), {
    target: { value: "Office friend" },
  });
  fireEvent.change(screen.getByLabelText("Phone number"), {
    target: { value: "2025550123" },
  });
  fireEvent.click(screen.getByText("Save contact"));
  await waitFor(() =>
    expect(contactsApi.add).toHaveBeenCalledWith({
      phone: "+12025550123",
      country: "US",
      local_label: "Office friend",
    }),
  );
  await screen.findByText("Office friend");
});
it("unknown hidden and blocked share neutral state", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [{ ...contact, matched_user: null }],
    next_cursor: null,
  });
  render(<Contacts />);
  await screen.findAllByText("Not on GlobalChat or unavailable");
  expect(screen.queryByText(/Actual profile/)).toBeNull();
});
it("edit changes private label without a phone or profile mutation", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [contact],
    next_cursor: null,
  });
  vi.mocked(contactsApi.update).mockResolvedValue({
    ...contact,
    local_label: "Private name",
  });
  render(<Contacts />);
  fireEvent.click(await screen.findByLabelText("More actions for Office friend"));
  fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
  fireEvent.change(screen.getByLabelText("Private name (optional)"), {
    target: { value: "Private name" },
  });
  fireEvent.click(screen.getByText("Save"));
  await waitFor(() =>
    expect(contactsApi.update).toHaveBeenCalledWith("c", {
      given_name: null,
      family_name: null,
      local_label: "Private name",
    }),
  );
  await screen.findByText("Private name");
  expect(screen.queryByText("Actual profile")).toBeNull();
});
it("remove requires confirmation", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [contact],
    next_cursor: null,
  });
  vi.mocked(contactsApi.remove).mockResolvedValue({ deleted: true });
  render(<Contacts />);
  fireEvent.click(await screen.findByLabelText("More actions for Office friend"));
  fireEvent.click(screen.getByRole("menuitem", { name: "Delete" }));
  expect(contactsApi.remove).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("Confirm"));
  await waitFor(() => expect(contactsApi.remove).toHaveBeenCalledWith("c"));
  await screen.findByText(/No contacts yet/);
});
it("invalid phone does not reach backend", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [],
    next_cursor: null,
  });
  render(<Contacts />);
  await screen.findByText(/No contacts yet/);
  fireEvent.click(screen.getByRole("button", {name:"Add contact"}));
  fireEvent.change(screen.getByLabelText("Phone number"), {
    target: { value: "123" },
  });
  fireEvent.click(screen.getByText("Save contact"));
  await screen.findAllByRole("alert");
  expect(contactsApi.add).not.toHaveBeenCalled();
});
it("rate limit blocks immediate resubmission", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [],
    next_cursor: null,
  });
  vi.mocked(contactsApi.add).mockRejectedValue(
    new ApiError("Limit", 429, "RATE_LIMITED", {}, 60),
  );
  render(<Contacts />);
  await screen.findByText(/No contacts yet/);
  fireEvent.click(screen.getByRole("button", {name:"Add contact"}));
  fireEvent.change(screen.getByLabelText("Phone number"), {
    target: { value: "2025550123" },
  });
  fireEvent.click(screen.getByText("Save contact"));
  await screen.findAllByText(/Too many contact checks/);
  expect(
    (screen.getByText("Save contact") as HTMLButtonElement).disabled,
  ).toBe(true);
});
it("failure retains saved contact", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({
    items: [contact],
    next_cursor: null,
  });
  vi.mocked(contactsApi.update).mockRejectedValue(
    new ApiError("Unavailable", 503),
  );
  render(<Contacts />);
  fireEvent.click(await screen.findByLabelText("More actions for Office friend"));
  fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
  fireEvent.click(screen.getByText("Save"));
  await screen.findAllByText("Unavailable");
  expect(within(screen.getByRole("list")).getByText("Office friend")).toBeTruthy();
});

it("international country context is explicit and local name is optional", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({items:[],next_cursor:null});
  vi.mocked(contactsApi.add).mockResolvedValue({...contact,local_label:null});
  render(<Contacts/>);
  await screen.findByText(/No contacts yet/);
  fireEvent.click(screen.getByRole("button", {name:"Add contact"}));
  fireEvent.change(screen.getByLabelText("Country"),{target:{value:"United Kingdom"}});
  fireEvent.change(screen.getByRole("combobox"),{target:{value:"GB"}});
  fireEvent.change(screen.getByLabelText("Phone number"),{target:{value:"02079460018"}});
  fireEvent.click(screen.getByText("Save contact"));
  await waitFor(()=>expect(contactsApi.add).toHaveBeenCalledWith({phone:"+442079460018",country:"GB",local_label:null}));
});
it("pagination uses server cursor and deduplicates repeated rows", async () => {
  vi.mocked(contactsApi.list).mockResolvedValueOnce({items:[contact],next_cursor:"cursor"}).mockResolvedValueOnce({items:[contact,{...contact,id:"d",local_label:"Second"}],next_cursor:null});
  render(<Contacts/>);
  fireEvent.click(await screen.findByText("Load more contacts"));
  await screen.findByText("Second");
  expect(contactsApi.list).toHaveBeenLastCalledWith("cursor");
  expect(within(screen.getByRole("list")).getAllByText("Office friend")).toHaveLength(1);
});

it("Message creates from the saved contact and opens the real chat route", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({items:[contact],next_cursor:null});
  vi.mocked(contactsApi.message).mockResolvedValue({
    id: "conversation-123",
    type: "DIRECT",
    title: null,
    description: null,
    avatar_media_id: null,
    status: "ACTIVE",
    member_count: 2,
  });
  render(<Contacts/>);
  fireEvent.click(
    await within(screen.getByRole("list")).findByRole("button", {
      name: /Office friend.*On GlobalChat/,
    }),
  );
  await waitFor(() => expect(push).toHaveBeenCalledWith("/?conversation=conversation-123"));
  expect(contactsApi.message).toHaveBeenCalledExactlyOnceWith("c");
});
it("Message failure remains safe and does not navigate", async () => {
  vi.mocked(contactsApi.list).mockResolvedValue({items:[contact],next_cursor:null});
  vi.mocked(contactsApi.message).mockRejectedValue(new Error("blocked"));
  render(<Contacts/>);
  fireEvent.click(
    await within(screen.getByRole("list")).findByRole("button", {
      name: /Office friend.*On GlobalChat/,
    }),
  );
  await screen.findByText(/unavailable for messaging/);
  expect(push).not.toHaveBeenCalled();
});
