import asyncio
import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal, init_db
from app.models.models import User, PatientCaregiverMap, RecoveryCheckin, MemoryEmbedding, RiskAlert
from app.services.rag_service import generate_embedding

DEFAULT_PATIENT_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_CAREGIVER_ID = "00000000-0000-0000-0000-000000000002"

async def seed_alex_patient_profile():
    print("Initializing SQLite Database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        print("Seeding Alex Carter Patient Profile into SQLite...")

        # 1. Upsert Patient User: Alex Carter
        res_p = await db.execute(select(User).where(User.id == DEFAULT_PATIENT_ID))
        alex = res_p.scalars().first()
        if not alex:
            alex = User(
                id=DEFAULT_PATIENT_ID,
                email="alex.carter@example.com",
                hashed_password="demo_secure_password_hash",
                full_name="Alex Carter",
                role="patient",
                phone_number="+15550192834"
            )
            db.add(alex)
        else:
            alex.full_name = "Alex Carter"
            alex.email = "alex.carter@example.com"
            alex.phone_number = "+15550192834"

        # 2. Upsert Caregiver User: Sarah Carter
        res_c = await db.execute(select(User).where(User.id == DEFAULT_CAREGIVER_ID))
        sarah = res_c.scalars().first()
        if not sarah:
            sarah = User(
                id=DEFAULT_CAREGIVER_ID,
                email="sarah.carter@example.com",
                hashed_password="demo_secure_password_hash",
                full_name="Sarah Carter",
                role="caregiver",
                phone_number="+15550192835"
            )
            db.add(sarah)

        await db.commit()

        # 3. Patient-Caregiver Mapping
        res_map = await db.execute(select(PatientCaregiverMap).where(PatientCaregiverMap.patient_id == DEFAULT_PATIENT_ID))
        mapping = res_map.scalars().first()
        if not mapping:
            mapping = PatientCaregiverMap(
                patient_id=DEFAULT_PATIENT_ID,
                caregiver_id=DEFAULT_CAREGIVER_ID,
                relationship_type="Spouse / Wife",
                notification_preference="sms_and_email"
            )
            db.add(mapping)
            await db.commit()

        # 4. Clear old memory embeddings for clean re-seed
        res_m = await db.execute(select(MemoryEmbedding).where(MemoryEmbedding.patient_id == DEFAULT_PATIENT_ID))
        for m in res_m.scalars().all():
            await db.delete(m)
        await db.commit()

        # Clear old checkins for clean re-seed
        res_chk = await db.execute(select(RecoveryCheckin).where(RecoveryCheckin.patient_id == DEFAULT_PATIENT_ID))
        for c in res_chk.scalars().all():
            await db.delete(c)
        await db.commit()

        # 5. Insert Rich Memory Profile Embeddings (No 42 day references)
        memories_data = [
            {
                "type": "motivation",
                "content": "Primary Motivation: Being present for 6-year-old daughter. Missed daughter's school performance in past due to alcohol hangover. Core commitment: 'I don't want my daughter remembering me as someone who was always tired or unavailable.'",
                "tags": ["father motivation", "daughter", "family goal"]
            },
            {
                "type": "trigger",
                "content": "High Risk Trigger - Work Stress: After difficult project manager meetings or project delays, feels the urge to reward himself ('I deserve a drink after today'). Internalizes stress and perfectionism.",
                "tags": ["work stress trigger", "perfectionism", "project management"]
            },
            {
                "type": "trigger",
                "content": "High Risk Trigger - Late Evenings (8 PM - Midnight): When spouse and daughter are asleep, feels alone with thoughts. Risk increases during emotional conflict or arguments with spouse where he withdraws.",
                "tags": ["evening cravings", "late night", "emotional withdrawal"]
            },
            {
                "type": "coping_strategy",
                "content": "Successful Coping Strategy - Walking: Alex reports 'Walking clears my head better than anything' (High effectiveness). Taking a 15-20 min outdoor walk resets perspective during cravings.",
                "tags": ["walking", "outdoor walk", "high effectiveness"]
            },
            {
                "type": "coping_strategy",
                "content": "Successful Coping Strategy - Talking with Sarah: Open communication with wife Sarah Carter helps regain emotional perspective (High effectiveness). Gym workouts and structured journaling also reduce stress.",
                "tags": ["sarah carter", "wife support", "gym", "journaling"]
            },
            {
                "type": "failed_strategy",
                "content": "Failed Coping Strategy to Avoid: Emotional isolation, overworking long hours, and ignoring feelings. Suppressing stress increases relapse risk.",
                "tags": ["avoid isolation", "avoid overworking", "relapse prevention"]
            },
            {
                "type": "support_network",
                "content": "Support Network: Wife Sarah Carter (Primary Caregiver, highest trust); Brother Michael Carter (Age 38, emergency accountability partner & workout buddy); Counselor Dr. Emily Roberts.",
                "tags": ["sarah carter", "michael carter", "dr emily roberts", "support network"]
            },
            {
                "type": "milestone",
                "content": "Recovery Profile: Committed to long-term sobriety, family health, and emotional growth. Rebuilding relationships and being present for family milestones.",
                "tags": ["sobriety goal", "family health"]
            }
        ]

        print("Generating RAG Memory Embeddings...")
        for mem in memories_data:
            vec = await generate_embedding(mem["content"])
            mem_obj = MemoryEmbedding(
                patient_id=DEFAULT_PATIENT_ID,
                memory_type=mem["type"],
                content=mem["content"],
                embedding_json=json.dumps(vec),
                metadata_json=json.dumps({"tags": mem["tags"]})
            )
            db.add(mem_obj)
        await db.commit()

        # 6. Insert Clean Historical Reflections
        now = datetime.utcnow()
        checkins_seed = [
            {
                "days_ago": 14,
                "text": "Experienced evening cravings after a tough work meeting. Took a 20-minute walk outside and talked with Sarah. Staying committed for my daughter.",
                "sentiment_label": "Positive",
                "sentiment_score": 0.8,
                "tier": "Low",
                "summary": "Craving managed successfully with walking and spouse support."
            },
            {
                "days_ago": 7,
                "text": "Work deadline was stressful today, but I headed straight to the gym instead of isolating. Feeling clearer head and sleeping better.",
                "sentiment_label": "Positive",
                "sentiment_score": 0.7,
                "tier": "Low",
                "summary": "Moderate stress redirected to gym workout."
            },
            {
                "days_ago": 3,
                "text": "Spent quality weekend time with my daughter and Sarah. Reading a story before bed reminded me why this journey matters.",
                "sentiment_label": "Positive",
                "sentiment_score": 0.95,
                "tier": "Low",
                "summary": "Positive mood. Strong motivation with family."
            },
            {
                "days_ago": 1,
                "text": "Work project went live today. Had a moment of stress, but remembered my walking coping strategy and called Michael for a quick chat.",
                "sentiment_label": "Positive",
                "sentiment_score": 0.85,
                "tier": "Low",
                "summary": "Work milestone completed sober using accountability call."
            }
        ]

        for c in checkins_seed:
            created_dt = now - timedelta(days=c["days_ago"])
            chk = RecoveryCheckin(
                patient_id=DEFAULT_PATIENT_ID,
                journal_text=c["text"],
                risk_tier=c["tier"],
                risk_score=0.1,
                sentiment_label=c["sentiment_label"],
                sentiment_score=c["sentiment_score"],
                ai_summary=c["summary"],
                created_at=created_dt
            )
            db.add(chk)
        await db.commit()

        print("✅ Alex Carter Profile re-seeded cleanly into SQLite without 42-day references!")

if __name__ == "__main__":
    asyncio.run(seed_alex_patient_profile())
