import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.future import select
from google import genai
from google.genai import types

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.models.models import User, RecoveryCheckin, MemoryEmbedding, DailyInteraction
from app.services.risk_engine import evaluate_risk

logger = logging.getLogger("recoverai.ws")
router = APIRouter(tags=["Voice & Chat WebSocket"])

DEFAULT_PATIENT_ID = "00000000-0000-0000-0000-000000000001"

BASE_SYSTEM_PROMPT = """You are RecoverAI, a supportive, warm, and highly expressive recovery companion.
Your voice responses are read aloud using Text-to-Speech audio synthesis.

STRICT DATA GROUNDING POLICY:
1. Speak in a naturally expressive, comforting, and conversational tone.
2. Keep responses concise (2-3 sentences max).
3. Ground your responses strictly on the patient's personal background, core motivations, known triggers, and proven coping strategies provided below.
4. Encourage the patient using their specific personal goals and past resilience strategies that worked for them.
5. Never give medical diagnoses. If self-harm or suicide is mentioned, encourage calling/texting 988 immediately."""

CANDIDATE_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
]


def get_genai_client():
    api_key = settings.effective_gemini_api_key
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Error creating GenAI client: {str(e)}")
    return None


async def fetch_patient_grounding_context(patient_id: str) -> str:
    """Fetch patient profile, RAG memory embeddings, & checkin history strictly filtered by patient_id from SQLite."""
    try:
        async with AsyncSessionLocal() as db:
            res_u = await db.execute(select(User).where(User.id == patient_id))
            patient = res_u.scalars().first()
            patient_name = patient.full_name if patient else "Patient"

            res_m = await db.execute(
                select(MemoryEmbedding)
                .where(MemoryEmbedding.patient_id == patient_id)
                .order_by(MemoryEmbedding.created_at.desc())
            )
            memories = res_m.scalars().all()

            res_c = await db.execute(
                select(RecoveryCheckin)
                .where(RecoveryCheckin.patient_id == patient_id)
                .order_by(RecoveryCheckin.created_at.desc())
                .limit(5)
            )
            checkins = res_c.scalars().all()

            context_lines = [
                f"\n\nSTRICT GROUNDED DATA FOR PATIENT: {patient_name} (ID: {patient_id})"
            ]

            if memories:
                context_lines.append(
                    "\nPERSONAL GROUNDING MEMORIES & RECOVERY PROFILE:"
                )
                for m in memories:
                    context_lines.append(f"- [{m.memory_type.upper()}]: {m.content}")
            else:
                context_lines.append(
                    "\nPERSONAL GROUNDING MEMORIES: New patient record."
                )

            if checkins:
                context_lines.append("\nRECENT DAILY REFLECTIONS (SQLite DB):")
                for c in checkins:
                    sent = (
                        f" (Sentiment: {c.sentiment_label})"
                        if c.sentiment_label
                        else ""
                    )
                    context_lines.append(
                        f"- Check-in ({c.created_at.strftime('%b %d') if c.created_at else 'Recent'}){sent}: '{c.journal_text}'"
                    )

            context_lines.append(
                "\nSTRICT INSTRUCTION: Ground your response strictly using this specific patient's personal background, motivations, and coping strategies."
            )
            return "\n".join(context_lines)
    except Exception as e:
        logger.error(f"Error fetching patient grounding context from DB: {str(e)}")
        return ""


async def record_daily_interaction(patient_id: str, user_msg: str, ai_msg: str):
    """Saves every interaction turn to SQLite daily_interactions table for end-of-day auto-summarization."""
    try:
        async with AsyncSessionLocal() as db:
            interaction = DailyInteraction(
                patient_id=patient_id, user_message=user_msg, ai_response=ai_msg
            )
            db.add(interaction)
            await db.commit()
    except Exception as e:
        logger.error(f"Error logging daily interaction turn: {str(e)}")


@router.websocket("/ws/voice-chat")
async def voice_chat_websocket(websocket: WebSocket, patient_id: Optional[str] = None):
    await websocket.accept()
    logger.info("WebSocket connection established.")

    active_patient_id = patient_id or DEFAULT_PATIENT_ID

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "text")
            content = message.get("content", "")

            if msg_type == "set_patient":
                active_patient_id = message.get("patient_id", DEFAULT_PATIENT_ID)
                await websocket.send_text(
                    json.dumps(
                        {"type": "patient_updated", "patient_id": active_patient_id}
                    )
                )
                continue

            if msg_type == "end_session":
                await websocket.send_text(json.dumps({"type": "session_ended"}))
                break

            # Evaluate real-time risk on incoming message content
            risk_tier, risk_score, reason = evaluate_risk(journal_text=content)

            # Send immediate risk feedback delta to client
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "risk_update",
                        "risk_tier": risk_tier,
                        "risk_score": risk_score,
                    }
                )
            )

            if risk_tier == "Critical":
                critical_msg = "CRITICAL SAFETY NOTICE: I care about your safety. Please connect immediately with the 988 Suicide & Crisis Lifeline by calling or texting 988 (Available 24/7, free and confidential)."
                await websocket.send_text(
                    json.dumps({"type": "transcript_delta", "delta": critical_msg})
                )
                await websocket.send_text(
                    json.dumps({"type": "stream_complete", "full_text": critical_msg})
                )
                await record_daily_interaction(active_patient_id, content, critical_msg)
                continue

            # Fetch patient grounding context strictly by active_patient_id
            grounding_context = await fetch_patient_grounding_context(active_patient_id)
            full_system_instruction = BASE_SYSTEM_PROMPT + grounding_context

            # Stream real-time AI response using Google Gemini API
            genai_client = get_genai_client()
            full_response = ""
            success = False

            if genai_client:
                for model_name in CANDIDATE_MODELS:
                    try:
                        response_stream = genai_client.models.generate_content_stream(
                            model=model_name,
                            contents=content,
                            config=types.GenerateContentConfig(
                                system_instruction=full_system_instruction
                            ),
                        )
                        for chunk in response_stream:
                            if chunk.text:
                                full_response += chunk.text
                                await websocket.send_text(
                                    json.dumps(
                                        {
                                            "type": "transcript_delta",
                                            "delta": chunk.text,
                                        }
                                    )
                                )
                        success = True
                        break
                    except Exception as e:
                        logger.warning(
                            f"Model {model_name} failed: {str(e)}. Trying fallback model..."
                        )

            if not success and not full_response:
                api_key = settings.effective_gemini_api_key
                if not api_key:
                    full_response = f"I hear you sharing: '{content}'. Please generate a free Gemini API key (starting with AIzaSy...) at https://aistudio.google.com/ and set GEMINI_API_KEY in backend/.env to get live Gemini responses!"
                else:
                    full_response = f"I hear you: '{content}'. Your API key or rate limit is being reset. Please ensure your key starts with AIzaSy... from https://aistudio.google.com/."

                await websocket.send_text(
                    json.dumps({"type": "transcript_delta", "delta": full_response})
                )

            # Record interaction turn into SQLite daily_interactions table
            await record_daily_interaction(active_patient_id, content, full_response)

            # Signal stream complete so browser Speech Synthesis (TTS) can read aloud
            await websocket.send_text(
                json.dumps({"type": "stream_complete", "full_text": full_response})
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
