"use client";
import { useRouter } from "next/navigation";
import { PasswordLogin } from "@/features/auth/password-login";
export default function Login(){const router=useRouter();return <PasswordLogin onAuthenticated={()=>router.replace("/")}/>;}
