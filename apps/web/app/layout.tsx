import type { Metadata } from "next";
import Link from "next/link";
import { AppNav } from "@/components/layout/app-nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "InferSight",
  description: "LLM gateway and inference observability platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(()=>{try{const t=localStorage.getItem('infersight-theme')||'dark';document.documentElement.classList.toggle('dark',t==='dark');document.documentElement.dataset.theme=t;}catch(e){document.documentElement.classList.add('dark');document.documentElement.dataset.theme='dark';}})();"
          }}
        />
      </head>
      <body>
        <div className="min-h-screen">
          <header className="sticky top-0 z-30 border-b border-black/10 bg-paper/90 backdrop-blur">
            <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <Link href="/chat" className="group inline-flex items-center gap-3 text-lg font-semibold tracking-normal text-ink">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#13211f] text-sm text-white shadow-sm transition-transform group-hover:-translate-y-0.5 dark:bg-signal dark:text-[#07100f]">
                  IS
                </span>
                <span>InferSight</span>
              </Link>
              <AppNav />
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
