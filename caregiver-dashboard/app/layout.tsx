import "./globals.css";
import React from "react";

export const metadata = {
  title: "RecoverAI — Caregiver Portal",
  description: "Real-time risk monitoring, alert feeds, and patient recovery timeline for caregivers.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 flex flex-col min-h-screen">
        {/* Navigation Bar */}
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-600 flex items-center justify-center font-bold text-white shadow-lg shadow-amber-500/20">
              C
            </div>
            <div>
              <h1 className="font-bold text-lg text-slate-100 tracking-tight">RecoverAI</h1>
              <p className="text-xs text-amber-400">Caregiver Escalation Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-slate-400 font-medium">Live Sentinel Stream</span>
          </div>
        </header>

        {/* Main Dashboard Body */}
        <main className="flex-1 max-w-6xl w-full mx-auto p-4 sm:p-6 space-y-6">
          {children}
        </main>

        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
          RecoverAI Caregiver Portal &copy; 2026. Confidential Patient Health Monitoring.
        </footer>
      </body>
    </html>
  );
}
