import "./globals.css";
import React from "react";

export const metadata = {
  title: "RecoverAI — Multimodal Recovery Companion",
  description: "Empathetic voice check-ins, long-term memory, and real-time risk support for patients and caregivers.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 flex flex-col min-h-screen">
        {/* Emergency Crisis Hotline Banner */}
        <div className="bg-rose-950/80 border-b border-rose-800/50 text-rose-200 px-4 py-2 text-xs sm:text-sm font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>Immediate Crisis Support: Call or text <strong>988</strong> (Suicide & Crisis Lifeline - 24/7)</span>
          </div>
          <a
            href="tel:988"
            className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded font-semibold transition"
          >
            Call 988
          </a>
        </div>

        {/* Navigation Bar */}
        <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-4 flex items-center justify-between sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center font-bold text-white shadow-lg shadow-teal-500/20">
              R
            </div>
            <div>
              <h1 className="font-bold text-lg text-slate-100 tracking-tight">RecoverAI</h1>
              <p className="text-xs text-teal-400">Patient Recovery Companion</p>
            </div>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <a href="/" className="text-slate-200 font-medium hover:text-teal-400 transition">Check-in</a>
            <a href="#memories" className="text-slate-400 hover:text-slate-200 transition">Memories</a>
            <a href="#history" className="text-slate-400 hover:text-slate-200 transition">History</a>
          </nav>
        </header>

        {/* Main Application Container */}
        <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 space-y-6">
          {children}
        </main>

        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
          RecoverAI Companion Platform &copy; 2026. Designed for Trauma-Informed Recovery.
        </footer>
      </body>
    </html>
  );
}
