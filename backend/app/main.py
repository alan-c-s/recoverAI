import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.future import select

from app.core.config import settings
from app.database.session import init_db, AsyncSessionLocal
from app.models.models import User
from app.routes import auth_routes, checkin_routes, memory_routes, caregiver_routes, websocket_routes
from app.routes.checkin_routes import auto_summarize_daily_interactions

logger = logging.getLogger("recoverai.cron")

async def run_daily_cron_summarizer():
    """Background cron task: checks all patient accounts every hour. If a patient chatted today but hasn't logged, auto-summarizes interactions into daily reflection."""
    while True:
        try:
            await asyncio.sleep(3600) # Runs background check every hour
            logger.info("⏰ Running automated end-of-day interaction summarizer cron job...")
            async with AsyncSessionLocal() as db:
                res = await db.execute(select(User.id).where(User.role == "patient"))
                patient_ids = res.scalars().all()
                for pid in patient_ids:
                    class DummyReq:
                        patient_id = str(pid)
                    await auto_summarize_daily_interactions(req=DummyReq(), db=db)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in automated daily summarizer cron: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB tables on startup
    try:
        await init_db()
    except Exception as e:
        print("Database startup initialization note:", e)

    # 2. Start automated background end-of-day cron task
    cron_task = asyncio.create_task(run_daily_cron_summarizer())
    
    yield
    
    # Clean shutdown of cron task
    cron_task.cancel()

app = FastAPI(
    title="RecoverAI Backend API",
    description="Multimodal GenAI-powered recovery companion platform API.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /v1
app.include_router(auth_routes.router, prefix="/v1")
app.include_router(checkin_routes.router, prefix="/v1")
app.include_router(memory_routes.router, prefix="/v1")
app.include_router(caregiver_routes.router, prefix="/v1")
app.include_router(websocket_routes.router, prefix="/v1")

# Serve Web Interfaces
@app.get("/", include_in_schema=False)
@app.get("/patient", include_in_schema=False)
async def serve_patient_app():
    file_path = os.path.join(STATIC_DIR, "patient.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"status": "online", "message": "RecoverAI API running. Patient UI loading."})

@app.get("/caregiver", include_in_schema=False)
async def serve_caregiver_portal():
    file_path = os.path.join(STATIC_DIR, "caregiver.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse({"status": "online", "message": "Caregiver Portal loading."})

@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "online",
        "service": "RecoverAI API",
        "database": settings.DATABASE_URL.split(":")[0],
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }
