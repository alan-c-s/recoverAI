import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.session import init_db
from app.routes import auth_routes, checkin_routes, memory_routes, caregiver_routes, websocket_routes

app = FastAPI(
    title="RecoverAI Backend API",
    description="Multimodal GenAI-powered recovery companion platform API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

@app.on_event("startup")
async def on_startup():
    await init_db()

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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

# Mount Web Application Interfaces
@app.get("/", include_in_schema=False)
@app.get("/patient", include_in_schema=False)
async def serve_patient_app():
    return FileResponse(os.path.join(STATIC_DIR, "patient.html"))

@app.get("/caregiver", include_in_schema=False)
async def serve_caregiver_portal():
    return FileResponse(os.path.join(STATIC_DIR, "caregiver.html"))

@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "online",
        "service": "RecoverAI API",
        "database": settings.DATABASE_URL.split(":")[0],
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }
