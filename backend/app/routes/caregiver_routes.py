from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database.session import get_db
from app.models.models import User, PatientCaregiverMap, RiskAlert, RecoveryCheckin
from app.schemas.schemas import RiskAlertResponse, AlertAcknowledgeRequest
from app.auth.auth_handler import get_current_user

router = APIRouter(prefix="/caregiver", tags=["Caregiver Portal"])

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
            "status": a.status,
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

@router.get("/alerts", response_model=List[RiskAlertResponse])
async def list_caregiver_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "caregiver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Caregiver endpoint accessible only by caregiver accounts."
        )

    map_stmt = select(PatientCaregiverMap.patient_id).where(PatientCaregiverMap.caregiver_id == current_user.id)
    map_result = await db.execute(map_stmt)
    patient_ids = map_result.scalars().all()

    if not patient_ids:
        return []

    alert_stmt = (
        select(RiskAlert)
        .where(RiskAlert.patient_id.in_(patient_ids))
        .order_by(RiskAlert.created_at.desc())
    )
    alert_result = await db.execute(alert_stmt)
    return alert_result.scalars().all()
