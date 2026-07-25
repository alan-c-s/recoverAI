from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google import genai

from app.core.config import settings
from app.database.session import get_db
from app.models.models import User, RecoveryCheckin, RiskAlert, DailyInteraction
from app.schemas.schemas import CheckinCreate
from app.auth.auth_handler import get_current_user
from app.services.risk_engine import evaluate_risk
from app.services.sentiment_engine import analyze_log_sentiment
from app.services.alert_service import trigger_caregiver_alert
from app.services.rag_service import save_memory

router = APIRouter(prefix="/recovery", tags=["Recovery & Check-ins"])

DEFAULT_PATIENT_ID = "00000000-0000-0000-0000-000000000001"


class LocationAlertRequest(BaseModel):
    patient_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AutoSummarizeRequest(BaseModel):
    patient_id: Optional[str] = None


async def ensure_demo_users(db: AsyncSession):
    """Ensure default patient exists in SQLite database."""
    stmt = select(User).where(User.id == DEFAULT_PATIENT_ID)
    res = await db.execute(stmt)
    patient = res.scalars().first()
    if not patient:
        demo_patient = User(
            id=DEFAULT_PATIENT_ID,
            email="patient@example.com",
            hashed_password="demo_hash",
            full_name="Alex Carter",
            role="patient",
        )
        db.add(demo_patient)
        await db.commit()


@router.post("/auto-summarize-daily-interactions")
async def auto_summarize_daily_interactions(
    req: Optional[AutoSummarizeRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """Automatically synthesizes a daily reflection log & sentiment metric from today's conversations if patient hasn't manually logged."""
    await ensure_demo_users(db)
    target_patient_id = (req and req.patient_id) or DEFAULT_PATIENT_ID

    # 1. Check if patient already has a check-in logged today
    today_start = datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    res_exist = await db.execute(
        select(RecoveryCheckin)
        .where(RecoveryCheckin.patient_id == target_patient_id)
        .where(RecoveryCheckin.created_at >= today_start)
    )
    existing_checkin = res_exist.scalars().first()
    if existing_checkin:
        return {
            "status": "already_logged",
            "message": "Daily reflection log for today already exists in database.",
            "checkin_id": str(existing_checkin.id),
            "journal_text": existing_checkin.journal_text,
            "sentiment_label": existing_checkin.sentiment_label,
        }

    # 2. Fetch today's interaction turns
    res_inter = await db.execute(
        select(DailyInteraction)
        .where(DailyInteraction.patient_id == target_patient_id)
        .where(DailyInteraction.created_at >= today_start)
        .order_by(DailyInteraction.created_at.asc())
    )
    interactions = res_inter.scalars().all()

    if not interactions:
        return {
            "status": "no_interactions",
            "message": "No conversation turns recorded today yet to auto-summarize.",
        }

    # 3. Combine conversation transcripts
    transcript_lines = []
    for inter in interactions:
        if inter.user_message:
            transcript_lines.append(f"Patient: {inter.user_message}")
        if inter.ai_response:
            transcript_lines.append(f"Companion: {inter.ai_response}")

    full_transcript = "\n".join(transcript_lines)

    # 4. Generate Daily Summary via Gemini or Fallback NLP
    api_key = settings.effective_gemini_api_key
    auto_summary_text = ""
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"Summarize the following patient's daily conversations into a 2-sentence empathetic daily recovery reflection log note written in first person:\n\n{full_transcript}"
            res_sum = client.models.generate_content(
                model="gemini-flash-lite-latest", contents=prompt
            )
            if res_sum.text:
                auto_summary_text = res_sum.text.strip()
        except Exception:
            pass

    if not auto_summary_text:
        # Fallback transcript aggregation
        user_msgs = [i.user_message for i in interactions if i.user_message]
        auto_summary_text = f"Auto-Generated Daily Reflection: Engaged in conversation turns today. Expressed: '{' '.join(user_msgs[:3])}'"

    # 5. Automated Sentiment Analysis & Risk Evaluation
    sent_res = analyze_log_sentiment(auto_summary_text)
    risk_tier, risk_score, trigger_reason = evaluate_risk(
        journal_text=auto_summary_text
    )

    # 6. Save Auto-Generated Daily Log to SQLite
    auto_checkin = RecoveryCheckin(
        patient_id=target_patient_id,
        journal_text=f"🤖 [Auto-Generated from Conversations] {auto_summary_text}",
        risk_tier=risk_tier,
        risk_score=risk_score,
        sentiment_label=sent_res["sentiment_label"],
        sentiment_score=sent_res["sentiment_score"],
        ai_summary=f"🤖 Auto-Synthesized Reflection ({sent_res['sentiment_label']})",
        created_at=datetime.utcnow(),
    )
    db.add(auto_checkin)
    await db.commit()
    await db.refresh(auto_checkin)

    return {
        "status": "success",
        "message": "Automated daily reflection log & sentiment metric synthesized from today's interactions!",
        "checkin_id": str(auto_checkin.id),
        "journal_text": auto_checkin.journal_text,
        "sentiment_label": sent_res["sentiment_label"],
        "sentiment_score": sent_res["sentiment_score"],
        "emotional_tone": sent_res["emotional_tone"],
        "risk_tier": auto_checkin.risk_tier,
    }


@router.post("/instant-alert")
async def trigger_instant_caregiver_alert(
    loc: Optional[LocationAlertRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """Allows patient to manually alert their caregiver immediately with HTML5 geolocation."""
    await ensure_demo_users(db)
    target_patient_id = (loc and loc.patient_id) or DEFAULT_PATIENT_ID

    loc_str = ""
    if loc and loc.latitude and loc.longitude:
        maps_link = f"https://maps.google.com/?q={loc.latitude},{loc.longitude}"
        loc_str = f" 📍 Patient Live Location: {maps_link}"
    else:
        loc_str = " 📍 Location: Shared from Patient Companion Web App"

    trigger_reason = (
        f"🚨 PATIENT MANUAL ALERT: Immediate assistance requested.{loc_str}"
    )

    alert = RiskAlert(
        patient_id=target_patient_id,
        risk_tier="High",
        trigger_reason=trigger_reason,
        is_acknowledged=False,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return {
        "status": "success",
        "alert_id": str(alert.id),
        "trigger_reason": trigger_reason,
        "message": "Caregiver alert dispatched immediately to Caregiver Sentinel Portal.",
    }


@router.post("/demo-checkin", status_code=status.HTTP_201_CREATED)
async def submit_demo_checkin(
    checkin_data: CheckinCreate, db: AsyncSession = Depends(get_db)
):
    """Zero-auth demo endpoint: performs automated sentiment analysis on logs, evaluates risk, and saves to SQLite."""
    await ensure_demo_users(db)
    target_patient_id = checkin_data.patient_id or DEFAULT_PATIENT_ID

    # 1. Automated Sentiment Analysis on Daily Log
    sent_res = analyze_log_sentiment(checkin_data.journal_text)

    # 2. Evaluate Risk Tier
    risk_tier, risk_score, trigger_reason = evaluate_risk(
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text,
    )

    # 3. Determine Created Timestamp
    created_dt = datetime.utcnow()
    if checkin_data.days_ago and checkin_data.days_ago > 0:
        created_dt = datetime.utcnow() - timedelta(days=checkin_data.days_ago)
    elif checkin_data.date_str:
        try:
            created_dt = datetime.fromisoformat(checkin_data.date_str)
        except Exception:
            pass

    # 4. Generate AI Feedback Summary with Sentiment Metric
    if risk_tier == "Critical":
        ai_summary = f"CRITICAL ALERT ({sent_res['sentiment_label']}): High distress detected. Crisis Lifeline protocol activated."
    elif risk_tier == "High":
        ai_summary = f"Elevated Risk ({sent_res['sentiment_label']}): Elevated distress detected in log."
    else:
        ai_summary = f"Sentiment Analysis: {sent_res['sentiment_label']} ({sent_res['emotional_tone']}). Reflection recorded."

    # 5. Create Check-in Record in SQLite
    new_checkin = RecoveryCheckin(
        patient_id=target_patient_id,
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text or "Daily Reflection Log",
        audio_file_url=checkin_data.audio_file_url,
        risk_tier=risk_tier,
        risk_score=risk_score,
        sentiment_label=sent_res["sentiment_label"],
        sentiment_score=sent_res["sentiment_score"],
        ai_summary=ai_summary,
        created_at=created_dt,
    )
    db.add(new_checkin)
    await db.commit()
    await db.refresh(new_checkin)

    # 6. Trigger Caregiver Alert if High/Critical
    alert_triggered = False
    alert_id = None
    if risk_tier in ["Medium", "High", "Critical"]:
        alert = RiskAlert(
            patient_id=target_patient_id,
            checkin_id=new_checkin.id,
            risk_tier=risk_tier,
            trigger_reason=trigger_reason
            or f"Log Sentiment: {sent_res['sentiment_label']}",
            is_acknowledged=False,
            created_at=created_dt,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        alert_triggered = True
        alert_id = str(alert.id)

    # 7. Extract & Save RAG Memory
    if checkin_data.journal_text and len(checkin_data.journal_text.strip()) > 5:
        await save_memory(
            db=db,
            patient_id=target_patient_id,
            memory_type="reflection",
            content=checkin_data.journal_text,
            metadata={
                "sentiment": sent_res["sentiment_label"],
                "score": sent_res["sentiment_score"],
            },
        )

    return {
        "status": "success",
        "checkin_id": str(new_checkin.id),
        "journal_text": new_checkin.journal_text,
        "sentiment_label": sent_res["sentiment_label"],
        "sentiment_score": sent_res["sentiment_score"],
        "emotional_tone": sent_res["emotional_tone"],
        "risk_tier": new_checkin.risk_tier,
        "ai_summary": new_checkin.ai_summary,
        "alert_triggered": alert_triggered,
        "alert_id": alert_id,
        "created_at": new_checkin.created_at.isoformat(),
    }


@router.get("/demo-history")
async def get_demo_history(
    patient_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)
):
    """Fetch persistent check-ins history strictly for the selected patient from SQLite."""
    target_patient_id = patient_id or DEFAULT_PATIENT_ID

    stmt = (
        select(RecoveryCheckin)
        .where(RecoveryCheckin.patient_id == target_patient_id)
        .order_by(RecoveryCheckin.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    checkins = result.scalars().all()

    out = []
    for c in checkins:
        label = c.sentiment_label
        score = c.sentiment_score
        if not label:
            analysis = analyze_log_sentiment(c.journal_text)
            label = analysis["sentiment_label"]
            score = analysis["sentiment_score"]

        out.append(
            {
                "id": str(c.id),
                "journal_text": c.journal_text,
                "sentiment_label": label,
                "sentiment_score": score,
                "risk_tier": c.risk_tier,
                "ai_summary": c.ai_summary,
                "created_at": c.created_at.isoformat() if c.created_at else "",
            }
        )
    return out


@router.post(
    "/checkins", status_code=status.HTTP_201_CREATED
)
async def submit_checkin(
    checkin_data: CheckinCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patient accounts can submit recovery check-ins.",
        )

    sent_res = analyze_log_sentiment(checkin_data.journal_text)
    risk_tier, risk_score, trigger_reason = evaluate_risk(
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text,
    )

    new_checkin = RecoveryCheckin(
        patient_id=current_user.id,
        mood_score=checkin_data.mood_score,
        craving_level=checkin_data.craving_level,
        journal_text=checkin_data.journal_text,
        audio_file_url=checkin_data.audio_file_url,
        risk_tier=risk_tier,
        risk_score=risk_score,
        sentiment_label=sent_res["sentiment_label"],
        sentiment_score=sent_res["sentiment_score"],
        ai_summary=f"Log Sentiment: {sent_res['sentiment_label']}",
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
            trigger_reason=trigger_reason,
        )

    return new_checkin
