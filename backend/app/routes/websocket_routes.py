import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import google.generativeai as genai
from app.core.config import settings
from app.services.risk_engine import evaluate_risk

logger = logging.getLogger("recoverai.ws")
router = APIRouter(tags=["Voice & Chat WebSocket"])

if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
    genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """You are RecoverAI, a supportive, empathetic, and trauma-informed recovery companion.
Your goal is to support users in their addiction recovery, mental health, or post-medical rehabilitation.
Keep responses warm, encouraging, non-judgmental, active-listening, and concise (2-3 sentences max).
Never give medical diagnoses. If self-harm or suicide is mentioned, encourage calling/texting 988 immediately."""

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

            # Stream response using Gemini API if key is present
            full_response = ""
            if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_"):
                try:
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=SYSTEM_PROMPT
                    )
                    response = model.generate_content(content, stream=True)
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            await websocket.send_text(json.dumps({
                                "type": "transcript_delta",
                                "delta": chunk.text
                            }))
                except Exception as e:
                    logger.error(f"Error streaming Gemini response: {str(e)}")
                    fallback = "I'm listening and right here with you. How are you feeling right now?"
                    full_response = fallback
                    await websocket.send_text(json.dumps({
                        "type": "transcript_delta",
                        "delta": fallback
                    }))
            else:
                # Fallback response if GEMINI_API_KEY is not entered yet
                fallback = f"I hear you sharing: '{content}'. Thank you for opening up. How can I best support your recovery journey today?"
                full_response = fallback
                await websocket.send_text(json.dumps({
                    "type": "transcript_delta",
                    "delta": fallback
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
