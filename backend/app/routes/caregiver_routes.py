import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.models.models import User, PatientCaregiverMap, RiskAlert, RecoveryCheckin, MemoryEmbedding
from app.schemas.schemas import RiskAlertResponse, PatientProfileUploadRequest
from app.auth.auth_handler import get_current_user
from app.services.rag_service import generate_embedding

router = APIRouter(prefix="/caregiver", tags=["Caregiver Portal & Patient Management"])

DEFAULT_CAREGIVER_ID = "00000000-0000-0000-0000-000000000002"

@router.get("/patients")
async def list_patients(db: AsyncSession = Depends(get_db)):
    """Fetch list of all registered patients in SQLite database for caregiver patient selector."""
    stmt = select(User).where(User.role == "patient").order_by(User.full_name.asc())
    res = await db.execute(stmt)
    patients = res.scalars().all()

    return [
        {
            "id": str(p.id),
            "full_name": p.full_name,
            "email": p.email,
            "phone_number": p.phone_number or ""
        }
        for p in patients
    ]

@router.post("/patient")
async def upload_patient_profile(
    req: PatientProfileUploadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Upload or update patient personal information from caregiver side to ground AI motivations & responses."""
    # 1. Upsert Patient User
    patient_id = req.patient_id or str(uuid.uuid4())
    res_p = await db.execute(select(User).where(User.id == patient_id))
    patient = res_p.scalars().first()

    if not patient:
        # Check if email already exists
        res_email = await db.execute(select(User).where(User.email == req.email))
        existing_by_email = res_email.scalars().first()
        if existing_by_email:
            patient = existing_by_email
            patient_id = str(patient.id)
        else:
            patient = User(
                id=patient_id,
                email=req.email,
                hashed_password="demo_secure_password_hash",
                full_name=req.full_name,
                role="patient",
                phone_number=req.phone_number or ""
            )
            db.add(patient)
    
    patient.full_name = req.full_name
    patient.email = req.email
    if req.phone_number:
        patient.phone_number = req.phone_number

    await db.commit()

    # 2. Upsert Patient-Caregiver Mapping
    res_map = await db.execute(
        select(PatientCaregiverMap).where(PatientCaregiverMap.patient_id == patient_id)
    )
    mapping = res_map.scalars().first()
    if not mapping:
        mapping = PatientCaregiverMap(
            patient_id=patient_id,
            caregiver_id=DEFAULT_CAREGIVER_ID,
            relationship_type="Primary Caregiver",
            notification_preference="sms_and_email"
        )
        db.add(mapping)
        await db.commit()

    # 3. Store Structured Grounding Memories in memory_embeddings
    grounding_entries = []

    if req.personal_background:
        grounding_entries.append({
            "type": "personal_background",
            "content": f"Personal Background: {req.personal_background}",
            "tags": ["personal_background", "profile"]
        })
    if req.primary_challenge:
        grounding_entries.append({
            "type": "primary_challenge",
            "content": f"Primary Recovery Challenge: {req.primary_challenge}",
            "tags": ["challenge", "sobriety_target"]
        })
    if req.motivation:
        grounding_entries.append({
            "type": "motivation",
            "content": f"Core Motivation & Grounding Reason: {req.motivation}",
            "tags": ["motivation", "family", "personal_goal"]
        })
    if req.triggers:
        grounding_entries.append({
            "type": "trigger",
            "content": f"High Risk Triggers: {req.triggers}",
            "tags": ["triggers", "risk_factors"]
        })
    if req.coping_strategies:
        grounding_entries.append({
            "type": "coping_strategy",
            "content": f"Proven Coping Strategies: {req.coping_strategies}",
            "tags": ["coping_strategy", "resilience"]
        })

    for item in grounding_entries:
        vec = await generate_embedding(item["content"])
        mem_obj = MemoryEmbedding(
            patient_id=patient_id,
            memory_type=item["type"],
            content=item["content"],
            embedding_json=json.dumps(vec),
            metadata_json=json.dumps({"tags": item["tags"], "uploaded_by": "caregiver"})
        )
        db.add(mem_obj)

    await db.commit()

    return {
        "status": "success",
        "message": f"Patient profile for '{req.full_name}' saved & AI grounding data indexed successfully in SQLite!",
        "patient_id": patient_id
    }

@router.get("/patient/{patient_id}/profile")
async def get_patient_profile(patient_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch patient profile and grounding memory entries from SQLite."""
    res_p = await db.execute(select(User).where(User.id == patient_id))
    patient = res_p.scalars().first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    res_m = await db.execute(select(MemoryEmbedding).where(MemoryEmbedding.patient_id == patient_id))
    memories = res_m.scalars().all()

    return {
        "patient": {
            "id": str(patient.id),
            "full_name": patient.full_name,
            "email": patient.email,
            "phone_number": patient.phone_number or ""
        },
        "grounding_memories": [
            {
                "id": str(m.id),
                "type": m.memory_type,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else ""
            }
            for m in memories
        ]
    }

@router.get("/demo-alerts")
async def list_demo_alerts(db: AsyncSession = Depends(get_db)):
    """Fetch persistent live risk alerts from SQLite database."""
    stmt = select(RiskAlert).order_by(RiskAlert.created_at.desc()).limit(50)
    result = await db.execute(stmt)
    alerts = result.scalars().all()
    
    return [
        {
            "id": str(a.id),
            "patient_id": str(a.patient_id),
            "checkin_id": str(a.checkin_id) if a.checkin_id else None,
            "risk_tier": a.risk_tier,
            "trigger_reason": a.trigger_reason,
            "is_acknowledged": a.is_acknowledged,
            "created_at": a.created_at.isoformat() if a.created_at else ""
        }
        for a in alerts
    ]

@router.post("/demo-acknowledge/{alert_id}")
async def acknowledge_demo_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Acknowledge a live risk alert in SQLite."""
    stmt = select(RiskAlert).where(RiskAlert.id == alert_id)
    result = await db.execute(stmt)
    alert = result.scalars().first()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return {"status": "success", "alert_id": alert_id, "is_acknowledged": True}
