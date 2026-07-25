# RecoverAI — System Architecture Document

## 1. High-Level Architecture Overview

RecoverAI utilizes a microservice-ready modular architecture built on **FastAPI (Backend)**, **Next.js 14 (Frontend & Caregiver Portal)**, **PostgreSQL with pgvector (Database & Long-term RAG Memory)**, and **Redis (Caching, Rate Limiting, Pub/Sub)**.

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|  +-------------------------------------+   +-----------------------------------+  |
|  |     RecoverAI Web App (Patient)     |   |    Caregiver Portal (Dashboard)   |  |
|  |     (Next.js 14 / Web Audio API)    |   |     (Next.js 14 / WebSockets)     |  |
|  +------------------+------------------+   +-----------------+-----------------+  |
+---------------------|----------------------------------------|--------------------+
                      | HTTP / WebSocket                       | HTTP / WebSocket
+---------------------v----------------------------------------v--------------------+
|                                  API GATEWAY & BACKEND                            |
|  +-----------------------------------------------------------------------------+  |
|  |                      FastAPI Application Server                             |  |
|  |   - Auth & Session Service       - Journaling & Audio Stream Service        |  |
|  |   - Risk Triage Engine           - Caregiver Alert & Escalation Service     |  |
|  +------------------+------------------------------+---------------------------+  |
+---------------------|------------------------------|------------------------------+
                      |                              |
+---------------------v------------------------------v------------------------------+
|                             DATA & EVENT PIPELINE                                 |
|  +----------------------------+  +-------------------+  +----------------------+  |
|  |  PostgreSQL 16 + pgvector  |  |  Redis 7 Pub/Sub  |  |   OpenAI GPT-4o /    |  |
|  |  (Users, Memory, Logs)     |  |  (Alerts, Cache)  |  |   Realtime Audio     |  |
|  +----------------------------+  +-------------------+  +----------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Component Specifications

### 2.1 Web Application (`/web`)
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript.
- **Styling**: Tailwind CSS + Shadcn UI + Framer Motion for smooth voice visualizer micro-animations.
- **Audio Processing**: Browser Web Audio API (MediaRecorder, AudioWorklet) for streaming PCM audio to backend WebSockets.

### 2.2 Caregiver Dashboard (`/caregiver-dashboard`)
- **Framework**: Next.js 14 (App Router) + Tailwind CSS.
- **Real-time Engine**: WebSocket client subscribing to patient risk status channels via Redis Pub/Sub.

### 2.3 Backend API & Services (`/backend`)
- **Framework**: FastAPI (Python 3.11+) with AsyncIO.
- **API Protocol**: REST (JSON) for standard CRUD; WebSockets for low-latency voice and chat streaming.
- **ORMs & Drivers**: SQLAlchemy 2.0 (Async) + `asyncpg` + `pgvector-python`.

### 2.4 AI Engine & RAG Memory Pipeline (`/ai` & `/backend/app/memory`)
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dims).
- **Vector Storage**: PostgreSQL `pgvector` with HNSW vector index for sub-50ms similarity search.
- **Memory Extractor**: Async background pipeline extracting core facts (triggers, coping methods, support network) from daily sessions.

### 2.5 Database & Event Queue (`/database` & `/infrastructure`)
- **Primary Database**: PostgreSQL 16 with `pgvector` extension enabled.
- **Cache & Message Broker**: Redis 7 for user session tokens, rate limiting, and real-time alert event broadcasting.

---

## 3. Data Flow & Sequence

### 3.1 Daily Check-in & Memory Retrieval Flow
1. Patient initiates voice/text check-in via `/web`.
2. WebSocket connection established at `/ws/voice-chat`.
3. Backend fetches recent user history and queries `pgvector` for relevant past memory fragments matching current query context.
4. System prompt combined with RAG context is dispatched to LLM.
5. Response stream (text + audio tokens) piped back to patient.
6. Check-in summary and new embeddings persisted asynchronously.

### 3.2 Risk Detection & Caregiver Escalation Flow
1. Risk Triage Engine analyzes sentiment, acoustic biomarkers, and keyword indicators in real-time.
2. If Risk Level >= High (Tier 3/4), Risk Engine triggers immediate alert event in Redis Pub/Sub.
3. Notification service dispatches SMS (Twilio) / Push Notification to caregiver.
4. Caregiver Dashboard updates alert badge in real-time via WebSocket.
