---
name: rag-memory-skill
description: Procedures for long-term patient context preservation, pgvector embedding generation, similarity search, and RAG context synthesis in RecoverAI.
---

# RAG Long-Term Memory Skill

## Overview
Defines how RecoverAI stores, indexes, and retrieves long-term semantic memory from patient interactions to personalize recovery support.

## Vector Architecture

- **Embedding Model**: OpenAI `text-embedding-3-small` (1536 dimensions).
- **Database Engine**: PostgreSQL 16 with `pgvector` HNSW index (`vector_cosine_ops`).
- **Memory Types**: `trigger`, `coping_strategy`, `milestone`, `reflection`.

## Operational Workflow

### 1. Memory Extraction
After every check-in session, summarize core insights:
- Identified relapse triggers (e.g. "Work deadlines causing anxiety").
- Effective coping mechanisms (e.g. "Evening walks with dog help reduce cravings").
- Personal milestones (e.g. "Reached 30 days sober on July 20").

### 2. Retrieval Strategy
During active conversation:
1. Generate query vector from user's latest input.
2. Query `memory_embeddings` using cosine similarity (`<->` operator) with `LIMIT 5`.
3. Filter by similarity threshold > 0.75.
4. Inject relevant memories into system prompt RAG context window.
