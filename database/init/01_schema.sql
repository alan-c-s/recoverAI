-- RecoverAI Database Schema Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('patient', 'caregiver')),
    phone_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patient-Caregiver Mapping Table
CREATE TABLE IF NOT EXISTS patient_caregiver_map (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    caregiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) DEFAULT 'caregiver',
    notification_preference VARCHAR(50) DEFAULT 'sms_and_email',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patient_id, caregiver_id)
);

-- 3. Recovery Journals & Check-ins Table
CREATE TABLE IF NOT EXISTS recovery_checkins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mood_score INT CHECK (mood_score BETWEEN 1 AND 10),
    craving_level INT CHECK (craving_level BETWEEN 0 AND 10),
    journal_text TEXT,
    audio_file_url VARCHAR(512),
    risk_tier VARCHAR(50) DEFAULT 'Low' CHECK (risk_tier IN ('Low', 'Medium', 'High', 'Critical')),
    risk_score FLOAT DEFAULT 0.0,
    ai_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Long-Term Vector Memory (RAG) Table
CREATE TABLE IF NOT EXISTS memory_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    memory_type VARCHAR(100) NOT NULL, -- 'trigger', 'coping_strategy', 'milestone', 'reflection'
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Risk Alerts & Escalations Table
CREATE TABLE IF NOT EXISTS risk_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    checkin_id UUID REFERENCES recovery_checkins(id) ON DELETE SET NULL,
    risk_tier VARCHAR(50) NOT NULL CHECK (risk_tier IN ('Low', 'Medium', 'High', 'Critical')),
    trigger_reason TEXT NOT NULL,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW Vector Index for Semantic Search
CREATE INDEX IF NOT EXISTS idx_memory_embeddings_vector 
ON memory_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_memory_patient_type 
ON memory_embeddings (patient_id, memory_type);
