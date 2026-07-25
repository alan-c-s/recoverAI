from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# User Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: str = Field("patient", pattern="^(patient|caregiver)$")
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    phone_number: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PatientProfileUploadRequest(BaseModel):
    patient_id: Optional[str] = None
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    primary_challenge: Optional[str] = "Alcohol Use Disorder"
    motivation: Optional[str] = None
    triggers: Optional[str] = None
    coping_strategies: Optional[str] = None
    personal_background: Optional[str] = None

# Check-in Schemas
class CheckinCreate(BaseModel):
    patient_id: Optional[str] = None
    mood_score: Optional[int] = Field(None, ge=1, le=10)
    craving_level: Optional[int] = Field(None, ge=0, le=10)
    journal_text: Optional[str] = None
    audio_file_url: Optional[str] = None
    days_ago: Optional[int] = 0
    date_str: Optional[str] = None

class CheckinResponse(BaseModel):
    id: UUID
    patient_id: UUID
    mood_score: Optional[int]
    craving_level: Optional[int]
    journal_text: Optional[str]
    risk_tier: str
    risk_score: float
    ai_summary: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Memory Schemas
class MemoryCreate(BaseModel):
    memory_type: str # 'trigger', 'coping_strategy', 'milestone', 'reflection'
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class MemoryResponse(BaseModel):
    id: UUID
    patient_id: UUID
    memory_type: str
    content: str
    similarity_score: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Alert Schemas
class RiskAlertResponse(BaseModel):
    id: UUID
    patient_id: UUID
    checkin_id: Optional[UUID]
    risk_tier: str
    trigger_reason: str
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertAcknowledgeRequest(BaseModel):
    alert_id: UUID
