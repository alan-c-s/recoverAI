from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.session import get_db
from app.models.models import User
from app.schemas.schemas import MemoryResponse
from app.auth.auth_handler import get_current_user
from app.services.rag_service import query_relevant_memories

router = APIRouter(prefix="/recovery", tags=["Vector Memory & RAG"])


@router.get("/memories", response_model=List[MemoryResponse])
async def search_memories(
    query: str = Query(
        ..., min_length=2, description="Search term or topic for semantic memory search"
    ),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Memory search is restricted to the patient account owner.",
        )

    results = await query_relevant_memories(
        db=db, patient_id=str(current_user.id), query_text=query, top_k=top_k
    )
    return results
