import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.session import Base, is_sqlite

def UUIDColumn():
    return String(36) if is_sqlite else PG_UUID(as_uuid=True)

def generate_uuid_str():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="patient") # 'patient' or 'caregiver'
    phone_number = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    checkins = relationship("RecoveryCheckin", back_populates="patient", cascade="all, delete-orphan")
    memories = relationship("MemoryEmbedding", back_populates="patient", cascade="all, delete-orphan")
    risk_alerts = relationship("RiskAlert", foreign_keys="RiskAlert.patient_id", back_populates="patient", cascade="all, delete-orphan")
    interactions = relationship("DailyInteraction", back_populates="patient", cascade="all, delete-orphan")

class PatientCaregiverMap(Base):
    __tablename__ = "patient_caregiver_map"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    patient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    caregiver_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(100), default="caregiver")
    notification_preference = Column(String(50), default="sms_and_email")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class RecoveryCheckin(Base):
    __tablename__ = "recovery_checkins"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    patient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mood_score = Column(Integer, nullable=True)
    craving_level = Column(Integer, nullable=True)
    journal_text = Column(Text, nullable=True)
    audio_file_url = Column(String(512), nullable=True)
    risk_tier = Column(String(50), default="Low") # Low, Medium, High, Critical
    risk_score = Column(Float, default=0.0)
    sentiment_label = Column(String(50), nullable=True, default="Neutral")
    sentiment_score = Column(Float, nullable=True, default=0.0)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("User", back_populates="checkins")

class DailyInteraction(Base):
    __tablename__ = "daily_interactions"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    patient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("User", back_populates="interactions")

class MemoryEmbedding(Base):
    __tablename__ = "memory_embeddings"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    patient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(100), nullable=False) # 'trigger', 'coping_strategy', 'milestone', 'reflection'
    content = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=False) # Stored as JSON string vector
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("User", back_populates="memories")

    @property
    def embedding(self):
        return json.loads(self.embedding_json) if self.embedding_json else []

    @embedding.setter
    def embedding(self, value):
        self.embedding_json = json.dumps(value)

class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    patient_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    checkin_id = Column(String(36), ForeignKey("recovery_checkins.id", ondelete="SET NULL"), nullable=True)
    risk_tier = Column(String(50), nullable=False)
    trigger_reason = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("User", foreign_keys=[patient_id], back_populates="risk_alerts")
