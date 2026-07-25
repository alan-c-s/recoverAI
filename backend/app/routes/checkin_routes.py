import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database.session import get_db
from app.models.models import User, RecoveryCheckin, RiskAlert
from app.schemas.schemas import CheckinCreate, CheckinResponse, RiskAlertResponse
from app.auth.auth_handler import get_current_user
from app.services.risk_engine import evaluate_risk
from app.services.alert_service import trigger_caregiver_alert
from app.services.rag_service import save_memory

router = APIRouter(prefix="/recovery", tags=["Recovery & Check-ins"])

DEFAULT_PATIENT_ID = "00000000-0000-0000-0000-000000000001"

async def ensure_demo_users(db: AsyncSession):
    """Ensure demo patient and caregiver exist in SQLite database."""
    stmt = select(User).where(User.id == DEFAULT_PATIENT_ID)
    res = await db.execute(stmt)
    patient = res.scalars().first()
    if not patient:
        demo_patient = User(
            id=DEFAULT_PATIENT_ID,
            email="patient@example.com",
            password_hash="demo_hash",
            full_name="Demo Patient",
            role="patient"
        )
        db.add(demo_patient)
        await db.commit()

@router.post("/demo-checkin", status_code=status.HTTP_201_CREATED)
async def submit_demo_checkin(
    checkin_data: CheckinCreate,
    db: AsyncSession = Depends(get_db)
):
    """Zero-auth demo endpoint to log check-ins, evaluate risk, save to SQLite, and trigger caregiver alerts."""
    await ensure_demo_users(db)

    # 1. Evaluate Risk Tier
    risk_tier, risk_score, trigger_reason = evaluate_risk(
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text
    )

    # 2. Generate AI Feedback Summary
    if risk_tier == "Critical":
        ai_summary = "CRITICAL ALERT: High distress detected. 988 Crisis Lifeline protocol activated and caregiver notified."
    elif risk_tier == "High":
        ai_summary = "Elevated cravings/distress detected. Caregiver alert logged in SQLite database."
    elif risk_tier == "Medium":
        ai_summary = "Moderate risk check-in recorded. Grounding exercises recommended."
    else:
        ai_summary = "Great job completing your reflection! Keep up the momentum in your recovery journey."

    # 3. Create Check-in Record in SQLite
    new_checkin = RecoveryCheckin(
        patient_id=DEFAULT_PATIENT_ID,
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text or "Daily Voice Reflection",
        audio_file_url=checkin_data.audio_file_url,
        risk_tier=risk_tier,
        risk_score=risk_score,
        ai_summary=ai_summary
    )
    db.add(new_checkin)
    await db.commit()
    await db.refresh(new_checkin)

    # 4. Trigger Caregiver Alert if Medium/High/Critical
    alert_triggered = False
    alert_id = None
    if risk_tier in ["Medium", "High", "Critical"]:
        alert = RiskAlert(
            patient_id=DEFAULT_PATIENT_ID,
            checkin_id=new_checkin.id,
            risk_tier=risk_tier,
            trigger_reason=trigger_reason or f"Elevated Craving Level ({checkin_data.craving_level}/10)",
            status="Active",
            is_acknowledged=False
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        alert_triggered = True
        alert_id = str(alert.id)

    # 5. Extract & Save RAG Memory
    if checkin_data.journal_text and len(checkin_data.journal_text.strip()) > 5:
        await save_memory(
            db=db,
            patient_id=DEFAULT_PATIENT_ID,
            memory_type="reflection",
            content=checkin_data.journal_text,
            metadata={"mood": checkin_data.mood_score, "craving": checkin_data.craving_level}
        )

    return {
        "status": "success",
        "checkin_id": str(new_checkin.id),
        "mood_score": new_checkin.mood_score,
        "craving_level": new_checkin.craving_level,
        "risk_tier": new_checkin.risk_tier,
        "ai_summary": new_checkin.ai_summary,
        "alert_triggered": alert_triggered,
        "alert_id": alert_id,
        "created_at": new_checkin.created_at.isoformat()
    }

@router.get("/demo-history")
async def get_demo_history(db: AsyncSession = Depends(get_db)):
    """Fetch persistent check-ins history from SQLite."""
    stmt = select(RecoveryCheckin).order_by(RecoveryCheckin.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    checkins = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "mood_score": c.mood_score,
            "craving_level": c.craving_level,
            "journal_text": c.journal_text,
            "risk_tier": c.risk_tier,
            "ai_summary": c.ai_summary,
            "created_at": c.created_at.isoformat() if c.created_at else ""
        }
        for c in checkins
    ]

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

    risk_tier, risk_score, trigger_reason = evaluate_risk(
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text
    )

    new_checkin = RecoveryCheckin(
        patient_id=current_user.id,
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text,
        audio_file_url=checkin_data.audio_file_url,
        risk_tier=risk_tier,
        risk_score=risk_score,
        ai_summary="Reflection recorded."
    )
    db.add(new_checkin)
    await db.commit()
    await db.refresh(new_checkin)

    if risk_tier in ["Medium", "High", "Critical"]:
        await trigger_caregiver_alert(
            db=db,
            patient_id=str(current_user.id),
            checkin_id=str(new_checkin.id),
            risk_tier=risk_tier,
            trigger_reason=trigger_reason
        )

    return new_checkin
