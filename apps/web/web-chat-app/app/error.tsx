"use client";
export default function ErrorPage({reset}:{reset:()=>void}){return <main className="grid min-h-dvh place-content-center gap-5 p-8"><h1 className="text-2xl font-semibold">Something went wrong</h1><p>Your session data has not been displayed. Try loading this page again.</p><button onClick={reset} className="rounded-xl bg-cyan-700 p-3 text-white">Try again</button></main>;}
