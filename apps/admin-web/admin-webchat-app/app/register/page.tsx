import Link from "next/link";
export default function RegisterPage() {
  const workspace = process.env.NEXT_PUBLIC_WORKSPACE_URL;
  return <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center gap-4 px-6">
    <p className="font-semibold text-indigo-600">GlobalChat Admin · Platform Administration</p>
    <h1 className="text-3xl font-semibold">Company registration belongs in your workspace</h1>
    <p>This application is reserved for platform administration. Company owners register and sign in through GlobalChat Company Workspace.</p>
    {workspace ? <a href={new URL("/register", workspace).toString()} className="font-semibold text-indigo-600 underline">Open Company Workspace registration</a> : <p>Company Workspace URL has not been configured.</p>}
    <Link href="/login" className="underline">Platform sign in</Link>
  </main>;
}
