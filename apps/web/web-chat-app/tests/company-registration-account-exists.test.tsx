import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider } from "@/workspace/features/auth/auth-provider";
import { PasswordAuth } from "@/workspace/features/auth/password-auth";

const navigation = vi.hoisted(() => ({ push: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => navigation,
}));

it("explains an existing company account and offers sign in", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof globalThis.fetch>(
      async () =>
        new Response(
          JSON.stringify({
            error: {
              code: "ACCOUNT_EXISTS",
              message:
                "Registration is unavailable. Sign in or contact support.",
            },
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        ),
    ),
  );
  render(
    <AuthProvider>
      <PasswordAuth registration />
    </AuthProvider>,
  );
  const user = userEvent.setup({ delay: null });
  await user.click(screen.getByRole("button", { name: "Create a company" }));
  await user.type(screen.getByLabelText("Company name"), "Acme Inc");
  await user.type(screen.getByLabelText("Owner name"), "Avery Owner");
  await user.type(screen.getByLabelText("Email"), "owner@example.test");
  await user.type(screen.getByLabelText("Phone number"), "9876543210");
  await user.click(screen.getByRole("button", { name: "Continue" }));
  await user.type(screen.getByLabelText("Password"), "A secure password 123!");
  await user.type(
    screen.getByLabelText("Confirm password"),
    "A secure password 123!",
  );
  await user.click(screen.getByRole("button", { name: "Create company" }));

  expect((await screen.findByRole("alert")).textContent).toContain(
    "An account already exists for this email. Sign in to your workspace instead.",
  );
  expect(
    screen.getByRole("link", { name: "Sign in instead" }).getAttribute("href"),
  ).toBe("/login");
}, 15000);
