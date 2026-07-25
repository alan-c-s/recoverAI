"use client";

import React, { useState } from "react";
import { AlertTriangle, CheckCircle, Bell, User, ShieldAlert, PhoneCall, Activity } from "lucide-react";

export default function CaregiverDashboardPage() {
  const [alerts, setAlerts] = useState<any[]>([
    {
      id: "alt_101",
      patientName: "Alex Mercer",
      patientId: "usr_987",
      riskTier: "High",
      reason: "Elevated craving level (8/10) reported during check-in.",
      timestamp: "10 mins ago",
      isAcknowledged: false
    },
    {
      id: "alt_100",
      patientName: "Alex Mercer",
      patientId: "usr_987",
      riskTier: "Medium",
      reason: "Low mood score (3/10) and stress indicator detected.",
      timestamp: "2 hours ago",
      isAcknowledged: true
    }
  ]);

  const handleAcknowledge = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, isAcknowledged: true } : a))
    );
  };

  const unacknowledgedCount = alerts.filter((a) => !a.isAcknowledged).length;

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-amber-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100">Caregiver Dashboard</h2>
          <p className="text-sm text-slate-400 mt-1">Real-time risk monitoring for assigned recovery patients.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl flex items-center gap-3">
            <Bell className="w-5 h-5 text-amber-400" />
            <div>
              <div className="text-xs text-slate-400">Pending Alerts</div>
              <div className="text-base font-bold text-amber-400">{unacknowledgedCount} Active</div>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Patient Overview & Live Alert Feed */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Assigned Patient Profile Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <User className="w-4 h-4 text-amber-400" />
            <h3 className="font-semibold text-slate-200 text-sm">Assigned Patient</h3>
          </div>

          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-850 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-100 text-base">Alex Mercer</span>
              <span className="px-2.5 py-0.5 rounded-full bg-amber-950 border border-amber-600 text-amber-300 text-[10px] font-bold">
                HIGH RISK
              </span>
            </div>
            <div className="text-xs text-slate-400 space-y-1">
              <p>Relationship: Caregiver / Family</p>
              <p>Last Check-in: 10 mins ago</p>
              <p>Current Mood: 4/10 | Craving: 8/10</p>
            </div>
            <div className="pt-2 flex gap-2">
              <a
                href="tel:+15550192834"
                className="flex-1 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition"
              >
                <PhoneCall className="w-3.5 h-3.5" /> Direct Call
              </a>
            </div>
          </div>
        </div>

        {/* Real-time Alert Feed */}
        <div className="md:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <h3 className="font-semibold text-slate-200 text-sm">Real-time Risk Alert Feed</h3>
            </div>
            <span className="text-xs text-slate-500">Auto-syncing via Redis Pub/Sub</span>
          </div>

          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  alert.riskTier === "Critical" ? "bg-rose-950/40 border-rose-800" :
                  alert.riskTier === "High" ? "bg-amber-950/40 border-amber-800" :
                  "bg-slate-950/40 border-slate-800"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      alert.riskTier === "High" ? "bg-amber-500 text-black" : "bg-yellow-500 text-black"
                    }`}>
                      {alert.riskTier}
                    </span>
                    <span className="font-bold text-slate-200 text-sm">{alert.patientName}</span>
                    <span className="text-xs text-slate-500">• {alert.timestamp}</span>
                  </div>
                  <p className="text-xs text-slate-300">{alert.reason}</p>
                </div>

                <div>
                  {alert.isAcknowledged ? (
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-400 font-semibold px-3 py-1.5 bg-emerald-950/60 border border-emerald-800 rounded-xl">
                      <CheckCircle className="w-3.5 h-3.5" /> Acknowledged
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-xl shadow-md transition"
                    >
                      Acknowledge Alert
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
