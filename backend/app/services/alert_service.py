import logging
import json
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.models import RiskAlert

logger = logging.getLogger("recoverai.alert")

async def get_redis_client():
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

async def trigger_caregiver_alert(
    db: AsyncSession,
    patient_id: str,
    checkin_id: str,
    risk_tier: str,
    trigger_reason: str
) -> RiskAlert:
    alert = RiskAlert(
        patient_id=patient_id,
        checkin_id=checkin_id,
        risk_tier=risk_tier,
        trigger_reason=trigger_reason,
        is_acknowledged=False
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    # Broadcast event via Redis Pub/Sub if risk level is High or Critical
    if risk_tier in ["High", "Critical"]:
        try:
            r = await get_redis_client()
            payload = {
                "alert_id": str(alert.id),
                "patient_id": str(patient_id),
                "risk_tier": risk_tier,
                "reason": trigger_reason,
                "created_at": alert.created_at.isoformat()
            }
            await r.publish(f"patient:{patient_id}:alerts", json.dumps(payload))
            await r.publish("global_caregiver_alerts", json.dumps(payload))
            await r.close()
            logger.info(f"Broadcasted {risk_tier} risk alert for patient {patient_id}")
        except Exception as e:
            logger.error(f"Failed to publish Redis alert event: {str(e)}")

    return alert
