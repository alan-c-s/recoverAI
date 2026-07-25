import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.future import select
from google import genai
from google.genai import types

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.models.models import RecoveryCheckin, MemoryEmbedding
from app.services.risk_engine import evaluate_risk

logger = logging.getLogger("recoverai.ws")
router = APIRouter(tags=["Voice & Chat WebSocket"])

BASE_SYSTEM_PROMPT = """You are RecoverAI, a supportive, warm, and highly expressive recovery companion.
Your voice responses are read aloud using Text-to-Speech audio synthesis.

Rules:
1. Speak in a naturally expressive, comforting, and conversational tone.
2. Use warm, natural phrasing with gentle pauses (commas/periods) for expressive speech synthesis pacing.
3. Keep responses concise (2-3 sentences max).
4. Use the patient's recovery journal history provided below to encourage them, celebrate their progress, and gently remind them of past coping strategies that worked for them (like walking or talking with Sarah).
5. Never give medical diagnoses. If self-harm or suicide is mentioned, encourage calling/texting 988 immediately."""

CANDIDATE_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest"
]

def get_genai_client():
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
        try:
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Error creating GenAI client: {str(e)}")
    return None

async def fetch_patient_journal_context() -> str:
    """Fetch recent recovery check-ins & RAG journal entries from SQLite to synthesize AI encouragement context."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(RecoveryCheckin).order_by(RecoveryCheckin.created_at.desc()).limit(5)
            res = await db.execute(stmt)
            checkins = res.scalars().all()

            if not checkins:
                return "\n\nPATIENT JOURNAL HISTORY: New user starting their recovery journey today."

            history_lines = []
            for c in checkins:
                sent = f" ({c.sentiment_label})" if c.sentiment_label else ""
                line = f"- Log ({c.created_at.strftime('%b %d') if c.created_at else 'Recent'}){sent}: Reflection: '{c.journal_text}'"
                history_lines.append(line)

            context_str = "\n\nPATIENT RECOVERY JOURNAL HISTORY (From SQLite DB):\n" + "\n".join(history_lines)
            context_str += "\nUse this journal history to personalize your response, remind them of past resilience, and encourage their ongoing progress."
            return context_str
    except Exception as e:
        logger.error(f"Error fetching journal context from DB: {str(e)}")
        return ""

@router.websocket("/ws/voice-chat")
async def voice_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "text")
            content = message.get("content", "")

            if msg_type == "end_session":
                await websocket.send_text(json.dumps({"type": "session_ended"}))
                break

            # Evaluate real-time risk on incoming message content
            risk_tier, risk_score, reason = evaluate_risk(journal_text=content)

            # Send immediate risk feedback delta to client
            await websocket.send_text(json.dumps({
                "type": "risk_update",
                "risk_tier": risk_tier,
                "risk_score": risk_score
            }))

            if risk_tier == "Critical":
                critical_msg = "CRITICAL SAFETY NOTICE: I care about your safety. Please connect immediately with the 988 Suicide & Crisis Lifeline by calling or texting 988 (Available 24/7, free and confidential)."
                await websocket.send_text(json.dumps({
                    "type": "transcript_delta",
                    "delta": critical_msg
                }))
                await websocket.send_text(json.dumps({
                    "type": "stream_complete",
                    "full_text": critical_msg
                }))
                continue

            # Fetch patient journal history from SQLite to build context-aware encouragement prompt
            journal_context = await fetch_patient_journal_context()
            full_system_instruction = BASE_SYSTEM_PROMPT + journal_context

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
                            )
                        )
                        for chunk in response_stream:
                            if chunk.text:
                                full_response += chunk.text
                                await websocket.send_text(json.dumps({
                                    "type": "transcript_delta",
                                    "delta": chunk.text
                                }))
                        success = True
                        break
                    except Exception as e:
                        logger.warning(f"Model {model_name} failed: {str(e)}. Trying fallback model...")

            if not success and not full_response:
                # Key missing, invalid, or quota exceeded notice
                if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your_"):
                    full_response = f"I hear you sharing: '{content}'. Please generate a free Gemini API key (starting with AIzaSy...) at https://aistudio.google.com/ and set GEMINI_API_KEY in backend/.env to get live Gemini responses!"
                else:
                    full_response = f"I hear you: '{content}'. Your API key or rate limit is being reset. Please ensure your key starts with AIzaSy... from https://aistudio.google.com/."

                await websocket.send_text(json.dumps({
                    "type": "transcript_delta",
                    "delta": full_response
                }))

            # Signal stream complete so browser Speech Synthesis (TTS) can read aloud
            await websocket.send_text(json.dumps({
                "type": "stream_complete",
                "full_text": full_response
            }))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
