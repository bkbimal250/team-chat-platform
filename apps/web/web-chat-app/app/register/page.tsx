import { AuthProvider } from "@/workspace/features/auth/auth-provider";
import { PasswordAuth } from "@/workspace/features/auth/password-auth";
export default function Register(){return <AuthProvider><PasswordAuth registration/></AuthProvider>;}
