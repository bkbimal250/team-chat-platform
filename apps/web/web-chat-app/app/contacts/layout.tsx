import { AuthProvider } from "@/workspace/features/auth/auth-provider";
import { ThemeListener } from "@/features/settings/appearance";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <ThemeListener />
      {children}
    </AuthProvider>
  );
}
