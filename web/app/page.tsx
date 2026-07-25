"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Send, Heart, ShieldAlert, Sparkles, Brain, Clock } from "lucide-react";

export default function PatientDashboardPage() {
  const [isRecording, setIsRecording] = useState(false);
  const [inputText, setInputText] = useState("");
  const [moodScore, setMoodScore] = useState(7);
  const [cravingLevel, setCravingLevel] = useState(2);
  const [riskTier, setRiskTier] = useState("Low");
  const [aiResponse, setAiResponse] = useState("Hello! I am your RecoverAI companion. How are you feeling today?");
  const [checkinHistory, setCheckinHistory] = useState<any[]>([]);
  const [memorySearch, setMemorySearch] = useState("");
  const [memories, setMemories] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Establish WebSocket Connection
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/v1/ws/voice-chat";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to RecoverAI Voice/Chat WebSocket");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "transcript_delta") {
          setAiResponse((prev) => prev + data.delta);
        } else if (data.type === "risk_update") {
          setRiskTier(data.risk_tier);
        }
      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    const msg = inputText;
    setInputText("");
    setAiResponse("");

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "text", content: msg }));
    } else {
      setAiResponse("Connecting to backend service...");
    }

    // Add local checkin history snippet
    setCheckinHistory((prev) => [
      { id: Date.now(), text: msg, mood: moodScore, craving: cravingLevel, tier: riskTier, date: new Date().toLocaleTimeString() },
      ...prev
    ]);
  };

  const handleSearchMemory = () => {
    if (!memorySearch.trim()) return;
    // Mock semantic memory search representation
    setMemories([
      { id: "1", type: "coping_strategy", content: `When feeling '${memorySearch}', deep 4-7-8 breathing and a 15 min walk helps.` },
      { id: "2", type: "milestone", content: "Successfully managed evening craving trigger on Thursday." }
    ]);
  };

  return (
    <div className="space-y-8">
      {/* Hero Welcome Card */}
      <div className="bg-gradient-to-r from-teal-900/40 via-slate-900 to-cyan-950/40 border border-teal-800/40 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-300 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5" /> 24/7 Recovery Support Active
            </div>
            <h2 className="text-2xl font-bold text-slate-100">Welcome back to your safe space</h2>
            <p className="text-sm text-slate-400 mt-1">Take a deep breath. Speak or write whatever is on your mind.</p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={`px-4 py-2 rounded-xl text-xs font-bold border flex items-center gap-2 ${
              riskTier === "Critical" ? "bg-rose-950/80 border-rose-600 text-rose-300" :
              riskTier === "High" ? "bg-amber-950/80 border-amber-600 text-amber-300" :
              riskTier === "Medium" ? "bg-yellow-950/80 border-yellow-600 text-yellow-300" :
              "bg-emerald-950/80 border-emerald-600 text-emerald-300"
            }`}>
              <ShieldAlert className="w-4 h-4" /> Risk Tier: {riskTier}
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Voice Companion & Daily Sliders */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Companion Conversational Box */}
        <div className="md:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-teal-400 animate-pulse" />
              <span className="font-semibold text-slate-200 text-sm">RecoverAI Companion Stream</span>
            </div>
            <span className="text-xs text-slate-500">WebSocket Connected</span>
          </div>

          {/* Audio Visualizer Wave Circle */}
          <div className="flex flex-col items-center justify-center py-6 bg-slate-950/40 rounded-xl border border-slate-850">
            <div className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-500 ${
              isRecording ? "bg-teal-500/20 border-2 border-teal-400 pulse-ring shadow-lg shadow-teal-500/30" : "bg-slate-800/80 border border-slate-700"
            }`}>
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`p-4 rounded-full text-white transition ${isRecording ? "bg-teal-600 hover:bg-teal-500" : "bg-slate-700 hover:bg-slate-600"}`}
                title={isRecording ? "Stop Voice Stream" : "Start Voice Stream"}
              >
                {isRecording ? <Mic className="w-6 h-6 animate-bounce" /> : <MicOff className="w-6 h-6" />}
              </button>
            </div>
            <span className="text-xs text-slate-400 mt-3 font-medium">
              {isRecording ? "Listening to your voice stream..." : "Click mic to start voice check-in"}
            </span>
          </div>

          {/* AI Response Display Box */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 min-h-[100px] max-h-[180px] overflow-y-auto">
            <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiResponse || "Listening..."}</p>
          </div>

          {/* Text Input & Send */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Or type how you feel today..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-teal-500 transition"
            />
            <button
              onClick={handleSendMessage}
              className="p-2.5 bg-teal-600 hover:bg-teal-500 text-white rounded-xl font-medium transition flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Daily Reflection Sliders */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Heart className="w-4 h-4 text-teal-400" />
            <h3 className="font-semibold text-slate-200 text-sm">Daily Self-Assessment</h3>
          </div>

          {/* Mood Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Mood Score</span>
              <span className="font-bold text-teal-400">{moodScore} / 10</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={moodScore}
              onChange={(e) => setMoodScore(Number(e.target.value))}
              className="w-full accent-teal-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>1 (Low)</span>
              <span>10 (Great)</span>
            </div>
          </div>

          {/* Craving Level Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span>Craving Level</span>
              <span className="font-bold text-amber-400">{cravingLevel} / 10</span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              value={cravingLevel}
              onChange={(e) => setCravingLevel(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0 (None)</span>
              <span>10 (Severe)</span>
            </div>
          </div>

          {/* Submit Reflections */}
          <button
            onClick={handleSendMessage}
            className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            Log Reflection
          </button>
        </div>

      </div>

      {/* Memory Search & History Section */}
      <div id="memories" className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* RAG Long-term Memory Search */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Brain className="w-4 h-4 text-cyan-400" />
            <h3 className="font-semibold text-slate-200 text-sm">Long-Term Memory Search (RAG)</h3>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={memorySearch}
              onChange={(e) => setMemorySearch(e.target.value)}
              placeholder="Search triggers, coping methods, past wins..."
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={handleSearchMemory}
              className="px-4 py-2 bg-cyan-700 hover:bg-cyan-600 text-white text-xs font-semibold rounded-xl transition"
            >
              Search
            </button>
          </div>
          <div className="space-y-2">
            {memories.map((m) => (
              <div key={m.id} className="p-3 bg-slate-950/40 rounded-xl border border-slate-800 text-xs space-y-1">
                <span className="inline-block px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 text-[10px] font-bold uppercase">{m.type}</span>
                <p className="text-slate-300">{m.content}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Reflections History */}
        <div id="history" className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
            <Clock className="w-4 h-4 text-teal-400" />
            <h3 className="font-semibold text-slate-200 text-sm">Today's Reflection History</h3>
          </div>
          <div className="space-y-2 max-h-[160px] overflow-y-auto">
            {checkinHistory.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No check-ins logged yet today.</p>
            ) : (
              checkinHistory.map((item) => (
                <div key={item.id} className="p-2.5 bg-slate-950/40 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <span className="text-slate-300 truncate max-w-[200px]">{item.text}</span>
                  <span className="text-slate-500 text-[10px]">{item.date}</span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
