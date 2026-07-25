# RecoverAI — Security, Privacy & HIPAA Compliance Architecture

## 1. Compliance & Data Privacy Architecture
RecoverAI handles sensitive Protected Health Information (PHI) and Personal Identifiable Information (PII) regarding patient recovery journeys. Security is designed into every layer.

---

## 2. Encryption Standards

### 2.1 Encryption at Rest
- **Database & Storage**: PostgreSQL tables and pgvector embedding columns encrypted using **AES-256-GCM**.
- **Audio Files**: Audio recordings stored in GCS/S3 buckets with customer-managed KMS keys (CMEK) and strict retention policies (auto-purge after 30 days unless consented).

### 2.2 Encryption in Transit
- **TLS 1.3**: Mandatory for all HTTP and WebSocket connections.
- **Secure WebSockets**: `wss://` protocol enforced with strict HSTS policies.

---

## 3. Authentication & Authorization (RBAC)

- **JWT Tokens**: Signed using RS256 algorithm with short expiration (1 hour access tokens, 14-day refresh tokens).
- **Role-Based Access Control**:
  - `patient`: Access to personal journal, memory, voice chat, and check-in history.
  - `caregiver`: Read-only access to assigned patient risk level, alert history, and timeline.
  - `admin`: Infrastructure management without PHI access.

---

## 4. PII/PHI Redaction & Anonymization Pipeline

Before sending user text or transcripts to LLM endpoints (e.g. OpenAI):
1. **Presidio PII Redactor**: Filters names, addresses, phone numbers, and SSNs.
2. **Zero-Data Retention Policy**: Opt-out of model provider training data collection.
3. **Audit Logging**: Immutable hash-chained audit logs tracking all PHI data access requests.
