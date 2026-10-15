"use client";

import { Toaster, toast } from "sonner";

export function notify(message: string) {
  toast.success(message);
}

export function Toast() {
  return (
    <Toaster
      closeButton
      duration={5000}
      position="bottom-right"
      richColors
      toastOptions={{ className: "font-sans" }}
    />
  );
}
