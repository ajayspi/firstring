-- MediCall AI — PostgreSQL + pgvector Schema
-- Run: psql -U ubuntu -d mediacall -f backend/postgres_schema.sql
-- Migration: Supabase → Local PostgreSQL + pgvector
-- Medical Call Center domain: voice-first, multi-language, Indian telephony/payments

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Core: Clinics/Facilities (replaces restaurants from TalkByte AI)
CREATE TABLE clinics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    address TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    pincode TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    closing_time TIME DEFAULT '22:00',
    ai_instructions TEXT DEFAULT '',
    plan TEXT DEFAULT 'starter',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Multi-tenant: Clinic staff/users
CREATE TABLE clinic_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'staff', -- owner, staff, readonly, triage_agent
    language_pref TEXT DEFAULT 'en', -- hi, en, ta, te, bn
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clinic_id, user_id)
);

-- Calls (core entity: voice-first medical call center)
-- State machine: GREETING -> TRIAGE -> APPOINTMENT / PRESCRIPTION -> COMPLETE
--                with branches: ESCALATED / DROPPED at each stage, PAYMENT_SENT / PAYMENT_EXPIRED loop
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    caller_number TEXT NOT NULL,
    caller_language TEXT DEFAULT 'en', -- hi, en, ta, te, bn (5 Indian languages)
    state TEXT DEFAULT 'GREETING', -- GREETING, TRIAGE, APPOINTMENT, PRESCRIPTION, COMPLETE, ESCALATED, DROPPED
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    transcript JSONB DEFAULT '[]', -- Multi-language transcript:
                                    -- [{"role":"caller","text":"...","language":"hi"},{"role":"agent","text":"...","language":"en"}]
    stt_confidence REAL DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    triage_severity TEXT, -- green, amber, red, critical (from AI triage)
    diagnosed_conditions JSONB DEFAULT '[]', -- SNOMED CT code list
    prescription_issued BOOLEAN DEFAULT FALSE,
    appointment_scheduled BOOLEAN DEFAULT FALSE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    escalated_to_human BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Appointments (derived from call triage + scheduling)
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    patient_name TEXT,
    patient_phone TEXT,
    patient_language TEXT DEFAULT 'en', -- hi, en, ta, te, bn
    caller_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, confirmed, completed, cancelled, no_show
    reason TEXT, -- chief complaint summary (from triage AI)
    doctor_id UUID, -- references practitioners/users who are doctors
    duration_minutes INTEGER DEFAULT 30,
    location TEXT, -- clinic address or telemedicine link (LiveKit room URL)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prescriptions (from call triage + doctor review)
CREATE TABLE prescriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    patient_name TEXT,
    patient_phone TEXT,
    patient_language TEXT DEFAULT 'en',
    caller_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    medication TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    instructions TEXT,
    doctor_id UUID, -- references prescribing doctor
    status TEXT DEFAULT 'pending', -- pending, approved, sent_pharmacy, dispensed
    pharmacy_name TEXT, -- Razorpay/PhonePe/Cashfree integrated pharmacy
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Medical embeddings (pgvector for similar call search, symptom clustering, triage pattern matching)
CREATE TABLE call_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID UNIQUE REFERENCES calls(id) ON DELETE CASCADE,
    embedding VECTOR(1536), -- 1536-dim embedding (Deepgram → LLM → ElevenLabs pipeline)
    embedding_type TEXT DEFAULT 'call_analysis', -- call_analysis, triage_summary, prescription_summary, speaker_embedding
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indian languages reference (for STT/TTS model mapping and UI localization)
CREATE TABLE language_codes (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE, -- hi, en, ta, te, bn
    script TEXT DEFAULT 'Latin/Devanagari/Tamil/Telugu/Bengali',
    deepgram_model TEXT DEFAULT 'nova-3', -- Deepgram model name/identifier
    elevenlabs_voice_id TEXT, -- ElevenLabs voice ID for TTS
    is_active BOOLEAN DEFAULT TRUE
);

-- Seed Indian language codes for STT/TTS
INSERT INTO language_codes (code, script, deepgram_model, elevenlabs_voice_id, is_active) VALUES
('en', 'Latin', 'nova-3', NULL, TRUE),
('hi', 'Devanagari', 'nova-3', NULL, TRUE),
('ta', 'Tamil', 'nova-3', NULL, TRUE),
('te', 'Telugu', 'nova-3', NULL, TRUE),
('bn', 'Bengali', 'nova-3', NULL, TRUE);

-- Call sessions / active call tracking (Lightweight LiveKit room mapping)
CREATE TABLE call_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID UNIQUE REFERENCES calls(id) ON DELETE CASCADE,
    clinic_id UUID REFERENCES clinics(id) ON DELETE SET NULL,
    livekit_room TEXT, -- LiveKit room ID for this call
    livekit_participant_id TEXT, -- Remote participant ID (caller/agent)
    status TEXT DEFAULT 'idle', -- idle, recording, in_progress, completed, failed
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fk_call FOREIGN KEY (call_id) REFERENCES calls(id) ON DELETE CASCADE
);

-- Plan §1: voice pipeline, prompts, eval, ops (mirror of SQLAlchemy models)
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    event_id TEXT NOT NULL,
    status TEXT DEFAULT 'received',
    attempts INTEGER DEFAULT 0,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(provider, event_id)
);

CREATE TABLE call_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    type TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    body TEXT NOT NULL,
    active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE voice_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language TEXT NOT NULL,
    turn_policy JSONB DEFAULT '{}',
    vendor_set JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE eval_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    language TEXT NOT NULL,
    script JSONB DEFAULT '{}',
    assertions JSONB DEFAULT '{}'
);

CREATE TABLE eval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_set JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE blocklist (
    e164 TEXT PRIMARY KEY,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    dedupe_key TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    claimed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dedupe_key)
);

-- Indexes for call center performance (critical for high-concurrency workload)
CREATE INDEX idx_calls_clinic ON calls(clinic_id);
CREATE INDEX idx_calls_state ON calls(state);
CREATE INDEX idx_calls_language ON calls(caller_language);
CREATE INDEX idx_calls_started ON calls(started_at DESC);
CREATE INDEX idx_calls_triage ON calls(triage_severity) WHERE triage_severity IS NOT NULL;
CREATE INDEX idx_appointments_clinic_status ON appointments(clinic_id, status);
CREATE INDEX idx_appointments_scheduled ON appointments(scheduled_at);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_clinics_active ON clinics(is_active);
CREATE INDEX idx_clinic_users_clinic ON clinic_users(clinic_id);
CREATE INDEX idx_call_embeddings_call ON call_embeddings(call_id);

-- pgvector similarity search function: find calls with similar patterns
CREATE OR REPLACE FUNCTION search_similar_calls(
    clinic_uuid UUID,
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    call_id UUID,
    similarity REAL
) LANGUAGE sql AS $$
    SELECT
        c.id AS call_id,
        1 - (ce.embedding <=> query_embedding) AS similarity
    FROM call_embeddings ce
    JOIN calls c ON ce.call_id = c.id
    WHERE c.clinic_id = clinic_uuid
      AND c.ended_at IS NOT NULL -- only completed calls for analysis
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- pgvector similarity search: find calls by symptom pattern
CREATE OR REPLACE FUNCTION search_calls_by_symptoms(
    clinic_uuid UUID,
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    call_id UUID,
    caller_number TEXT,
    similarity REAL,
    state TEXT,
    severity TEXT
) LANGUAGE sql AS $$
    SELECT
        c.id AS call_id,
        c.caller_number,
        1 - (ce.embedding <=> query_embedding) AS similarity,
        c.state,
        c.triage_severity
    FROM call_embeddings ce
    JOIN calls c ON ce.call_id = c.id
    WHERE c.clinic_id = clinic_uuid
    ORDER BY ce.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- pgvector similarity search: find related calls (same patient, different time)
CREATE OR REPLACE FUNCTION search_related_calls(
    clinic_uuid UUID,
    call_id UUID,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    related_call_id UUID,
    caller_number TEXT,
    similarity REAL,
    state TEXT
) LANGUAGE sql AS $$
    DECLARE
        target_embedding VECTOR(1536);
        target_language TEXT;
    BEGIN
        -- Get the embedding and language of the reference call
        SELECT ce.embedding, c.caller_language
        INTO target_embedding, target_language
        FROM call_embeddings ce
        JOIN calls c ON ce.call_id = c.id
        WHERE c.id = call_id AND c.clinic_id = clinic_uuid;

        RETURN QUERY
        SELECT
            c.id AS related_call_id,
            c.caller_number,
            1 - (ce.embedding <=> target_embedding) AS similarity,
            c.state
        FROM call_embeddings ce
        JOIN calls c ON ce.call_id = c.id
        WHERE c.clinic_id = clinic_uuid
          AND c.id != call_id
          AND c.caller_language = target_language -- same language calls
        ORDER BY ce.embedding <=> target_embedding
        LIMIT match_count;
    END;
$$;

-- Trigger for automatic updated_at on core tables
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER update_clinics_updated_at BEFORE UPDATE ON clinics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_prescriptions_updated_at BEFORE UPDATE ON prescriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Row Level Security (RLS) — multi-tenant data isolation
ALTER TABLE clinics ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinic_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;

-- Clinic owners see their own clinic data
CREATE POLICY clinic_own_data ON clinics
    FOR ALL USING (
        id IN (
            SELECT clinic_id FROM clinic_users 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

-- Staff can read clinic info
CREATE POLICY clinic_staff_read ON clinics
    FOR SELECT USING (
        id IN (
            SELECT clinic_id FROM clinic_users 
            WHERE user_id = auth.uid()
        )
    );

-- Staff can create calls for their clinic
CREATE POLICY calls_create ON calls
    FOR INSERT WITH CHECK (clinic_id IN (
        SELECT clinic_id FROM clinic_users WHERE user_id = auth.uid()
    ));

-- Staff can read calls for their clinic
CREATE POLICY calls_read ON calls
    FOR SELECT USING (clinic_id IN (
        SELECT clinic_id FROM clinic_users WHERE user_id = auth.uid()
    ));

-- Appointments: clinic staff can manage (CRUD)
CREATE POLICY appointments_manage ON appointments
    FOR ALL USING (clinic_id IN (
        SELECT clinic_id FROM clinic_users WHERE user_id = auth.uid()
    ));

-- Prescriptions: clinic staff can manage
CREATE POLICY prescriptions_manage ON prescriptions
    FOR ALL USING (clinic_id IN (
        SELECT clinic_id FROM clinic_users WHERE user_id = auth.uid()
    ));

-- Language codes: always readable (reference data)
CREATE POLICY language_codes_read ON language_codes
    FOR SELECT USING (is_active = TRUE);

-- Grant permissions for authenticated users (Supabase auth → PostgreSQL auth bridge)
GRANT ALL ON clinics TO authenticated;
GRANT ALL ON clinic_users TO authenticated;
GRANT ALL ON calls TO authenticated;
GRANT ALL ON appointments TO authenticated;
GRANT ALL ON prescriptions TO authenticated;
GRANT USAGE, SELECT ON sequence language_codes_id_seq TO authenticated;