import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import { clearSession } from "@/lib/auth/session";
afterEach(() => {
  cleanup();
  clearSession();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  sessionStorage.clear();
  localStorage.clear();
});
