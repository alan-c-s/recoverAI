# RecoverAI — API Specification

## 1. Global API Standards

- **Base URL**: `https://api.recoverai.dev/v1`
- **Protocol**: HTTPS / WSS
- **Authentication**: `Authorization: Bearer <jwt_token>`
- **Content Type**: `application/json`

---

## 2. Authentication Endpoints (`/auth`)

### `POST /auth/register`
- **Description**: Registers a new user (Patient or Caregiver).
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Alex Mercer",
    "role": "patient"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "usr_987654321",
    "email": "user@example.com",
    "role": "patient",
    "created_at": "2026-07-25T10:00:00Z"
  }
  ```

### `POST /auth/login`
- **Request Body**: `OAuth2 Password Form Data` (`username`, `password`).
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": "usr_987654321",
      "role": "patient"
    }
  }
  ```

---

## 3. Recovery Check-in & Memory Endpoints (`/recovery`)

### `POST /recovery/checkins`
- **Description**: Submits a completed check-in reflection.
- **Request Body**:
  ```json
  {
    "mood_score": 7,
    "craving_level": 2,
    "journal_text": "Had a stressful morning, but used deep breathing exercises.",
    "audio_session_id": "ses_12345"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "checkin_id": "chk_5551212",
    "risk_tier": "Low",
    "ai_feedback": "Great job utilizing your breathing techniques!",
    "created_at": "2026-07-25T10:15:00Z"
  }
  ```

### `GET /recovery/memories`
- **Description**: Queries semantic memory fragments for the current user.
- **Query Params**: `query` (string), `top_k` (int, default=5).
- **Response (200 OK)**:
  ```json
  {
    "memories": [
      {
        "id": "mem_001",
        "fact": "Deep breathing helps when feeling overwhelmed by work deadlines.",
        "similarity_score": 0.89,
        "created_at": "2026-07-20T14:30:00Z"
      }
    ]
  }
  ```

---

## 4. WebSocket Streaming Endpoints (`/ws`)

### `WSS /ws/voice-chat`
- **Description**: Real-time bi-directional streaming audio & text session.
- **Client Message Types**:
  - `audio_chunk`: Raw PCM / WebM audio binary data.
  - `text_message`: `{ "type": "text", "content": "I feel anxious today." }`
  - `end_session`: `{ "type": "end_session" }`
- **Server Message Types**:
  - `transcript_delta`: `{ "type": "transcript", "delta": "I hear that..." }`
  - `audio_chunk`: Binary audio stream response.
  - `risk_update`: `{ "type": "risk_update", "tier": "Medium", "score": 0.45 }`

---

## 5. Caregiver Portal Endpoints (`/caregiver`)

### `GET /caregiver/patients/{patient_id}/timeline`
- **Description**: Returns patient check-in timeline and risk history.

### `POST /caregiver/alerts/acknowledge`
- **Description**: Acknowledges a high/critical risk notification.
- **Request Body**: `{ "alert_id": "alt_999", "action_taken": "Called patient" }`
