import logging
import json
import numpy as np
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google import genai

from app.core.config import settings
from app.models.models import MemoryEmbedding

logger = logging.getLogger("recoverai.rag")


async def generate_embedding(text: str) -> List[float]:
    """Generate vector embedding for text using Google Gemini API."""
    if not settings.effective_gemini_api_key:
        return [0.0] * 768

    try:
        client = genai.Client(api_key=settings.effective_gemini_api_key)
        response = client.models.embed_content(
            model="text-embedding-004", contents=text
        )
        if response.embedding and response.embedding.values:
            return response.embedding.values
    except Exception as e:
        logger.error(f"Error generating Gemini embedding: {str(e)}")

    return [0.0] * 768


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(v1)
    b = np.array(v2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def save_memory(
    db: AsyncSession,
    patient_id: str,
    memory_type: str,
    content: str,
    metadata: dict = None,
) -> MemoryEmbedding:
    """Stores a new memory entry with embedding vector in SQLite."""
    vec = await generate_embedding(content)
    mem = MemoryEmbedding(
        patient_id=patient_id,
        memory_type=memory_type,
        content=content,
        embedding_json=json.dumps(vec),
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(mem)
    await db.commit()
    await db.refresh(mem)
    return mem


async def query_relevant_memories(
    db: AsyncSession, patient_id: str, query_text: str, top_k: int = 3
) -> List[MemoryEmbedding]:
    """Retrieve top-K most relevant memory embeddings for patient strictly by cosine similarity."""
    query_vec = await generate_embedding(query_text)

    stmt = select(MemoryEmbedding).where(
        MemoryEmbedding.patient_id == patient_id
    )
    res = await db.execute(stmt)
    memories = res.scalars().all()

    if not memories:
        return []

    scored_memories = []
    for m in memories:
        score = cosine_similarity(query_vec, m.embedding)
        scored_memories.append((score, m))

    scored_memories.sort(key=lambda x: x[0], reverse=True)
    return [mem for score, mem in scored_memories[:top_k]]
