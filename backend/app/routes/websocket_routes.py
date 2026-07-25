import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from app.core.config import settings
from app.services.risk_engine import evaluate_risk

logger = logging.getLogger("recoverai.ws")
router = APIRouter(tags=["Voice & Chat WebSocket"])

SYSTEM_PROMPT = """You are RecoverAI, a supportive, warm, and highly expressive recovery companion.
Your voice responses are read aloud using Text-to-Speech audio synthesis.
Rules:
1. Speak in a naturally expressive, comforting, and conversational tone.
2. Use warm, natural phrasing with gentle pauses (commas/periods) for expressive speech synthesis pacing.
3. Keep responses concise (2-3 sentences max).
4. Never give medical diagnoses. If self-harm or suicide is mentioned, encourage calling/texting 988 immediately."""

CANDIDATE_MODELS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-1.5-pro"
]

def get_genai_client():
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
        try:
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Error creating GenAI client: {str(e)}")
    return None

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
                                system_instruction=SYSTEM_PROMPT
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
                    full_response = f"I hear you: '{content}'. Your API key or rate limit is being reset. Please ensure you have a free Gemini key starting with AIzaSy... from https://aistudio.google.com/."

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
