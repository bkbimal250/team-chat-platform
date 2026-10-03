import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });
export const metadata: Metadata = {
  title: "GlobalChat",
  description: "Secure communication for connected teams.",
};
export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html suppressHydrationWarning lang="en" className={geist.variable}>
      <head><script dangerouslySetInnerHTML={{__html: `try{var t=localStorage.getItem('globalchat.theme');document.documentElement.dataset.theme=t==='dark'||t==='light'?t:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}catch{}`}}/></head><body>{children}</body>
    </html>
  );
}
