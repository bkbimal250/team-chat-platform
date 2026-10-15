import { expect, it } from "vitest";
import { ApiError } from "@/workspace/lib/api/client";
import { contactMessageError } from "@/features/contacts/contact-message-error";

it("preserves actionable forbidden responses for contact messaging", () => {
  expect(
    contactMessageError(
      new ApiError("Switch to a personal account.", 403, "PERSONAL_CONTEXT_REQUIRED"),
    ),
  ).toBe("Switch to a personal account.");
  expect(
    contactMessageError(
      new ApiError("Direct messaging is unavailable.", 403, "DIRECT_CONVERSATION_BLOCKED"),
    ),
  ).toBe("Direct messaging is unavailable.");
});

it("uses a neutral message for other contact messaging failures", () => {
  expect(contactMessageError(new Error("network failure"))).toBe(
    "This contact is unavailable for messaging. Check discoverability and try again.",
  );
});
