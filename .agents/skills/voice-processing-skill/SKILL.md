---
name: voice-processing-skill
description: Guidelines and procedures for streaming audio, speech-to-text processing, voice sentiment extraction, and acoustic biomarker monitoring in RecoverAI.
---

# Voice Processing Skill

## Overview
Provides specifications and procedures for handling real-time voice streaming, audio encoding, Speech-to-Text (STT), Text-to-Speech (TTS), and acoustic sentiment analysis.

## Audio Specifications

- **Format**: PCM 16-bit 24kHz / Opus mono stream.
- **Protocol**: WebSockets (`wss://api.recoverai.dev/v1/ws/voice-chat`).
- **Chunk Size**: 100ms audio frames.

## Processing Pipeline

1. **Ingestion**: Web Audio API captures microphone stream and sends binary frames via WebSocket.
2. **Transcription & Synthesis**: OpenAI Realtime API / Whisper processes audio into text deltas.
3. **Voice Sentiment Analysis**:
   - Extract pitch variation, speaking cadence, hesitation markers, and vocal tremor indicators.
   - Combine text sentiment with acoustic confidence score to evaluate user distress.
