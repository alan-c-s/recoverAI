from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database.session import get_db
from app.models.models import User, PatientCaregiverMap, RiskAlert, RecoveryCheckin
from app.schemas.schemas import RiskAlertResponse, AlertAcknowledgeRequest, CheckinResponse
from app.auth.auth_handler import get_current_user

router = APIRouter(prefix="/caregiver", tags=["Caregiver Portal"])

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

    # Get all patients mapped to this caregiver
    map_stmt = select(PatientCaregiverMap.patient_id).where(PatientCaregiverMap.caregiver_id == current_user.id)
    map_result = await db.execute(map_stmt)
    patient_ids = map_result.scalars().all()

    if not patient_ids:
        return []

    # Get alerts for these patients
    alert_stmt = (
        select(RiskAlert)
        .where(RiskAlert.patient_id.in_(patient_ids))
        .order_by(RiskAlert.created_at.desc())
    )
    alert_result = await db.execute(alert_stmt)
    return alert_result.scalars().all()

@router.post("/alerts/acknowledge", response_model=RiskAlertResponse)
async def acknowledge_alert(
    req: AlertAcknowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role != "caregiver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Alert acknowledgment restricted to caregivers."
        )

    stmt = select(RiskAlert).where(RiskAlert.id == req.alert_id)
    result = await db.execute(stmt)
    alert = result.scalars().first()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    await db.commit()
    await db.refresh(alert)
    return alert
