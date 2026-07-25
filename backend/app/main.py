import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.database.session import init_db
from app.routes import auth_routes, checkin_routes, memory_routes, caregiver_routes, websocket_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    try:
        await init_db()
    except Exception as e:
        print("Database startup initialization note:", e)
    yield

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
