from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database.session import get_db
from app.models.models import User, RecoveryCheckin
from app.schemas.schemas import CheckinCreate, CheckinResponse
from app.auth.auth_handler import get_current_user
from app.services.risk_engine import evaluate_risk
from app.services.alert_service import trigger_caregiver_alert
from app.services.rag_service import save_memory

router = APIRouter(prefix="/recovery", tags=["Recovery & Check-ins"])

@router.post("/checkins", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def submit_checkin(
    checkin_data: CheckinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patient accounts can submit recovery check-ins."
        )

    # 1. Evaluate Risk Tier
    risk_tier, risk_score, trigger_reason = evaluate_risk(
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text
    )

    # 2. Generate AI Feedback Summary
    if risk_tier == "Critical":
        ai_summary = "CRITICAL ALERT: Please call or text 988 immediately. You are not alone and support is available 24/7."
    elif risk_tier == "High":
        ai_summary = "We noticed elevated cravings/distress. A caregiver alert has been logged, and we encourage taking deep breaths and using your coping plan."
    elif risk_tier == "Medium":
        ai_summary = "Thank you for checking in. Remember to pause, take a moment for yourself, and practice your daily grounding exercise."
    else:
        ai_summary = "Great job completing your reflection! Keep up the momentum in your recovery journey."

    # 3. Create Check-in Record
    new_checkin = RecoveryCheckin(
        patient_id=current_user.id,
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text,
        audio_file_url=checkin_data.audio_file_url,
        risk_tier=risk_tier,
        risk_score=risk_score,
        ai_summary=ai_summary
    )
    db.add(new_checkin)
    await db.commit()
    await db.refresh(new_checkin)

    # 4. Trigger Caregiver Alert if Medium/High/Critical
    if risk_tier in ["Medium", "High", "Critical"]:
        await trigger_caregiver_alert(
            db=db,
            patient_id=str(current_user.id),
            checkin_id=str(new_checkin.id),
            risk_tier=risk_tier,
            trigger_reason=trigger_reason
        )

    # 5. Extract & Save RAG Memory if journal text provided
    if checkin_data.journal_text and len(checkin_data.journal_text.strip()) > 10:
        await save_memory(
            db=db,
            patient_id=str(current_user.id),
            memory_type="reflection",
            content=checkin_data.journal_text,
            metadata={"mood": checkin_data.mood_score, "craving": checkin_data.craving_level}
        )

    return new_checkin

@router.get("/checkins", response_model=List[CheckinResponse])
async def list_checkins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(RecoveryCheckin)
        .where(RecoveryCheckin.patient_id == current_user.id)
        .order_by(RecoveryCheckin.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
