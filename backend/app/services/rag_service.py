import logging
import json
import numpy as np
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google import genai
from google.genai import types

from app.core.config import settings
from app.models.models import MemoryEmbedding

logger = logging.getLogger("recoverai.rag")

def get_genai_client():
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
        try:
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Error creating GenAI client: {str(e)}")
    return None

async def generate_embedding(text: str) -> List[float]:
    client = get_genai_client()
    if client:
        try:
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            return result.embedding.values
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {str(e)}")

    logger.info("Using zero-vector fallback for embeddings.")
    return [0.0] * 768

async def save_memory(
    db: AsyncSession,
    patient_id: str,
    memory_type: str,
    content: str,
    metadata: dict = None
) -> MemoryEmbedding:
    embedding_vec = await generate_embedding(content)
    memory = MemoryEmbedding(
        patient_id=str(patient_id),
        memory_type=memory_type,
        content=content,
        embedding_json=json.dumps(embedding_vec),
        metadata_json=json.dumps(metadata or {})
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

async def query_relevant_memories(
    db: AsyncSession,
    patient_id: str,
    query_text: str,
    top_k: int = 5
) -> List[MemoryEmbedding]:
    query_vec = await generate_embedding(query_text)

    # Fetch all patient memory embeddings
    stmt = (
        select(MemoryEmbedding)
        .where(MemoryEmbedding.patient_id == str(patient_id))
    )
    result = await db.execute(stmt)
    all_memories = result.scalars().all()

    if not all_memories:
        return []

    # Score memories by cosine similarity
    scored_memories = []
    for mem in all_memories:
        vec = mem.embedding
        sim = cosine_similarity(query_vec, vec)
        scored_memories.append((sim, mem))

    # Sort descending by similarity score
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    
    top_memories = [item[1] for item in scored_memories[:top_k]]
    return top_memories
