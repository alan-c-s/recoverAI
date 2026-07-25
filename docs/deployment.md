# RecoverAI — Infrastructure & Deployment Plan

## 1. Local Development Architecture

The entire stack runs locally via `docker-compose.yml`:
- **Backend API**: FastAPI running on port 8000 (`uvicorn`).
- **PostgreSQL 16**: Port 5432 with `pgvector` pre-installed.
- **Redis 7**: Port 6379 for Pub/Sub & token caching.
- **Web App**: Next.js 14 running on port 3000.
- **Caregiver Dashboard**: Next.js 14 running on port 3001.

---

## 2. Docker Compose Configuration

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: recoverai_postgres
    environment:
      POSTGRES_USER: recoverai
      POSTGRES_PASSWORD: recoverai_secret_password
      POSTGRES_DB: recoverai
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    container_name: recoverai_redis
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: recoverai_backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://recoverai:recoverai_secret_password@postgres:5432/recoverai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  pgdata:
```

---

## 3. Production Deployment (GCP / Kubernetes)

- **Container Orchestration**: Google Kubernetes Engine (GKE) Autopilot.
- **Database**: Cloud SQL for PostgreSQL 16 (with pgvector extension) + Read Replicas.
- **Cache**: Cloud Memorystore for Redis.
- **Ingress**: GKE Ingress with Google-managed TLS certificates and Cloud Armor WAF.

---

## 4. CI/CD Pipeline (GitHub Actions)

1. **Lint & Test**: Pytest for backend, Jest/Playwright for web apps, ESLint & Flake8.
2. **Build**: Build multi-arch Docker images via Cloud Build.
3. **Scan**: Security vulnerability scanning with Trivy & Snyk.
4. **Deploy**: Rolling deployment to staging/production GKE clusters.
